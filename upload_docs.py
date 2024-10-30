from collections.abc import Callable, Sequence
from collections import OrderedDict
from functools import partial
from pathlib import Path
from pydantic import Field
from typing import Any, List, cast
from uuid import uuid5, UUID
import asyncio
import datetime
import json
import logging
import os
import re

from postgrest.exceptions import APIError
from supabase._async.client import create_client as create_async_client, AsyncClient
import numpy as np

from paperqa.clients import DEFAULT_CLIENTS, DocMetadataClient
from paperqa.core import llm_parse_json, map_fxn_summary
from paperqa.docs import Docs
from paperqa.llms import (
    EmbeddingModel,
    EmbeddingModes,
    LLMModel,
    NumpyVectorStore,
    PromptRunner,
    cosine_similarity,
)
from paperqa.readers import read_doc
from paperqa.settings import MaybeSettings, get_settings
from paperqa.types import (
    Answer,
    Context,
    Doc,
    DocKey,
    Embeddable,
    Text,
    set_llm_answer_ids,
)
from paperqa.utils import (
    gather_with_concurrency,
    maybe_is_text,
    name_in_text,
)

from quote_docs import AnswerQuotes
from supabase_store import SupabaseStore
from utils import TextPlus, AnswerQuotesFormatted

logger = logging.getLogger(__name__)


NAMESPACE_CITATION = UUID("5345abad-94db-4db0-a1b1-6107ba7a4cb7")

def generate_dockey(citation: str):
    return str(uuid5(NAMESPACE_CITATION, citation))


async def upload_chunk(chunk: Text|TextPlus, supabase: AsyncClient):
    response = (
        await supabase.table("chunks")
        .insert(
            {
                "document": chunk.doc.dockey,
                "pages": chunk.pages if type(chunk) == TextPlus else [],
                "text": chunk.text,
                "text_emb": chunk.embedding,
            }
        )
        .execute()
    )
    if not len(response.data):
        raise ValueError("Chunk not inserted")


class UploadDocs(Docs):
    supabase_url: str
    supabase_service_key: str

    async def retrieve_texts(
        self,
        query: str,
        k: int,
        settings: MaybeSettings = None,
        embedding_model: EmbeddingModel | None = None,
    ) -> list[Text]:
        self.texts_index = SupabaseStore(
            supabase_url=self.supabase_url,
            supabase_service_key=self.supabase_service_key,
        )

        settings = get_settings(settings)
        if embedding_model is None:
            embedding_model = settings.get_embedding_model()

        # TODO: should probably happen elsewhere
        self.texts_index.mmr_lambda = settings.texts_index_mmr_lambda

        await self._build_texts_index(embedding_model)
        _k = k + len(self.deleted_dockeys)
        matches: list[Text] = cast(
            list[Text],
            (
                await self.texts_index.max_marginal_relevance_search(
                    query, k=_k, fetch_k=2 * _k, embedding_model=embedding_model
                )
            )[0],
        )
        matches = [m for m in matches if m.doc.dockey not in self.deleted_dockeys]
        return matches[:k]

    async def aget_evidence(
        self,
        query: Answer | str,
        exclude_text_filter: set[str] | None = None,
        settings: MaybeSettings = None,
        callbacks: list[Callable] | None = None,
        embedding_model: EmbeddingModel | None = None,
        summary_llm_model: LLMModel | None = None,
    ) -> Answer:
        supabase = await create_async_client(self.supabase_url, self.supabase_service_key)

        evidence_settings = get_settings(settings)
        answer_config = evidence_settings.answer
        prompt_config = evidence_settings.prompts

        answer = (
            Answer(question=query, config_md5=evidence_settings.md5)
            if isinstance(query, str)
            else query
        )

        num_chunks_response = (
            await supabase.table("chunks")
            .select("id", count="exact")
            .execute()
        )

        if not self.docs and num_chunks_response.count == 0:
            return answer

        if embedding_model is None:
            embedding_model = evidence_settings.get_embedding_model()

        if summary_llm_model is None:
            summary_llm_model = evidence_settings.get_summary_llm()

        exclude_text_filter = exclude_text_filter or set()
        exclude_text_filter |= {c.text.name for c in answer.contexts}

        _k = answer_config.evidence_k
        if exclude_text_filter:
            _k += len(
                exclude_text_filter
            )  # heuristic - get enough so we can downselect

        if answer_config.evidence_retrieval:
            matches = await self.retrieve_texts(
                answer.question, _k, evidence_settings, embedding_model
            )
        else:
            matches = self.texts

        if exclude_text_filter:
            matches = [m for m in matches if m.text not in exclude_text_filter]

        matches = (
            matches[: answer_config.evidence_k]
            if answer_config.evidence_retrieval
            else matches
        )

        prompt_runner: PromptRunner | None = None
        if not answer_config.evidence_skip_summary:
            if prompt_config.use_json:
                prompt_runner = partial(
                    summary_llm_model.run_prompt,
                    prompt_config.summary_json,
                    system_prompt=prompt_config.summary_json_system,
                )
            else:
                prompt_runner = partial(
                    summary_llm_model.run_prompt,
                    prompt_config.summary,
                    system_prompt=prompt_config.system,
                )

        with set_llm_answer_ids(answer.id):
            results = await gather_with_concurrency(
                answer_config.max_concurrent_requests,
                [
                    map_fxn_summary(
                        text=m,
                        question=answer.question,
                        prompt_runner=prompt_runner,
                        extra_prompt_data={
                            "summary_length": answer_config.evidence_summary_length,
                            "citation": f"{m.name}: {m.doc.citation}",
                        },
                        parser=llm_parse_json if prompt_config.use_json else None,
                        callbacks=callbacks,
                    )
                    for m in matches
                ],
            )

        for _, llm_result in results:
            answer.add_tokens(llm_result)

        answer.contexts += [r for r, _ in results if r is not None]
        return answer

    async def aupload(  # noqa: PLR0912
        self,
        path: Path,
        citation: str | None = None,
        docname: str | None = None,
        dockey: DocKey | None = None,
        title: str | None = None,
        abstract: str | None = None,
        doi: str | None = None,
        authors: list[str] | None = None,
        settings: MaybeSettings = None,
        llm_model: LLMModel | None = None,
        embedding_model: EmbeddingModel | None = None,
        **kwargs,
    ) -> str | None:
        """Add a document to the collection."""
        all_settings = get_settings(settings)
        parse_config = all_settings.parsing

        supabase = await create_async_client(self.supabase_url, self.supabase_service_key)

        if llm_model is None:
            llm_model = all_settings.get_llm()
        if citation is None:
            # Peek first chunk
            texts = read_doc(
                path,
                Doc(docname="", citation="", dockey=dockey),  # Fake doc
                chunk_chars=parse_config.chunk_size,
                overlap=parse_config.overlap,
                page_size_limit=parse_config.page_size_limit,
            )
            if not texts:
                raise ValueError(f"Could not read document {path}. Is it empty?")
            result = await llm_model.run_prompt(
                prompt=parse_config.citation_prompt,
                data={"text": texts[0].text},
                skip_system=True,  # skip system because it's too hesitant to answer
            )
            citation = result.text
            if (
                len(citation) < 3  # noqa: PLR2004
                or "Unknown" in citation
                or "insufficient" in citation
            ):
                citation = f"Unknown, {os.path.basename(path)}, {datetime.now().year}"
        
        # Generate dockey from citation info to support dedup
        if dockey is None:
            dockey = generate_dockey(citation)

        if docname is None:
            # get first name and year from citation
            match = re.search(r"([A-Z][a-z]+)", citation)
            if match is not None:
                author = match.group(1)
            else:
                # panicking - no word??
                raise ValueError(
                    f"Could not parse docname from citation {citation}. "
                    "Consider just passing key explicitly - e.g. docs.py "
                    "(path, citation, key='mykey')"
                )
            year = ""
            match = re.search(r"(\d{4})", citation)
            if match is not None:
                year = match.group(1)
            docname = f"{author}{year}"
        docname = self._get_unique_name(docname)

        doc = Doc(docname=docname, citation=citation, dockey=dockey)

        # try to extract DOI / title from the citation
        if (doi is title is None) and parse_config.use_doc_details:
            # TODO: specify a JSON schema here when many LLM providers support this
            result = await llm_model.run_prompt(
                prompt=parse_config.structured_citation_prompt,
                data={"citation": citation},
                skip_system=True,
            )
            # This code below tries to isolate the JSON
            # based on observed messages from LLMs
            # it does so by isolating the content between
            # the first { and last } in the response.
            # Since the anticipated structure should  not be nested,
            # we don't have to worry about nested curlies.
            clean_text = result.text.split("{", 1)[-1].split("}", 1)[0]
            clean_text = "{" + clean_text + "}"
            try:
                citation_json = json.loads(clean_text)
                if citation_title := citation_json.get("title"):
                    title = citation_title
                if citation_doi := citation_json.get("doi"):
                    doi = citation_doi
                if citation_author := citation_json.get("authors"):
                    authors = citation_author
            except (json.JSONDecodeError, AttributeError):
                # json.JSONDecodeError: clean_text was not actually JSON
                # AttributeError: citation_json was not a dict (e.g. a list)
                logger.warning(
                    "Failed to parse all of title, DOI, and authors from the"
                    " ParsingSettings.structured_citation_prompt's response"
                    f" {clean_text}, consider using a manifest file or specifying a"
                    " different citation prompt."
                )
        # see if we can upgrade to DocDetails
        # if not, we can progress with a normal Doc
        # if "overwrite_fields_from_metadata" is used:
        # will map "docname" to "key", and "dockey" to "doc_id"
        if (title or doi) and parse_config.use_doc_details:
            if kwargs.get("metadata_client"):
                metadata_client = kwargs["metadata_client"]
            else:
                metadata_client = DocMetadataClient(
                    session=kwargs.pop("session", None),
                    clients=kwargs.pop("clients", DEFAULT_CLIENTS),
                )

            query_kwargs: dict[str, Any] = {}

            if doi:
                query_kwargs["doi"] = doi
            if authors:
                query_kwargs["authors"] = authors
            if title:
                query_kwargs["title"] = title
            
            doc = await metadata_client.upgrade_doc_to_doc_details(
                doc, **(query_kwargs | kwargs)
            )

            # Revert UUID dockey
            doc.dockey = dockey

        embedding_model = all_settings.get_embedding_model()
        if not embedding_model:
            raise ValueError(f"Invalid embedding_model {embedding_model}")

        abstract_emb = None
        if abstract:
            abstract_emb = (await embedding_model.embed_documents(texts=[abstract]))[0]

        # Upload document to `documents` table
        try:
            response = (
                await supabase.table("documents")
                .insert(
                    {
                        "id": dockey,
                        "title": title,
                        "abstract": abstract,
                        "abstract_emb": abstract_emb,
                        "citation": citation,
                        "authors": authors,
                        "published_at": kwargs.get("published_at"),
                    }
                )
                .execute()
            )
            if not len(response.data):
                raise ValueError("Document not inserted")

        except APIError as e:
            if e.message.startswith("duplicate key"):
                if kwargs.get("ignore_duplicate_doc"):
                    pass
                else:
                    raise ValueError("Another document with the same citation has already been uploaded previously")
            else:
                raise e

        # Read document and chunk text
        texts = read_doc(
            path,
            doc,
            chunk_chars=parse_config.chunk_size,
            overlap=parse_config.overlap,
            page_size_limit=parse_config.page_size_limit,
        )
        # loose check to see if document was loaded
        if (
            not texts
            or len(texts[0].text) < 10  # noqa: PLR2004
            or (
                not parse_config.disable_doc_valid_check
                and not maybe_is_text(texts[0].text)
            )
        ):
            raise ValueError(
                f"This does not look like a text document: {path}. Pass disable_check"
                " to ignore this error."
            )

        # Retrieve page numbers
        for i, t in enumerate(texts):
            texts[i] = TextPlus.from_text(t)

        for t, t_embedding in zip(
            texts,
            await embedding_model.embed_documents(texts=[t.text for t in texts]),
            strict=True,
        ):
            t.embedding = t_embedding
        
        await asyncio.gather(*[upload_chunk(t, supabase) for t in texts])
        
        return None

    async def aquery(  # noqa: PLR0912
        self,
        query: Answer | str,
        settings: MaybeSettings = None,
        callbacks: list[Callable] | None = None,
        llm_model: LLMModel | None = None,
        summary_llm_model: LLMModel | None = None,
        embedding_model: EmbeddingModel | None = None,
    ) -> AnswerQuotesFormatted:

        query_settings = get_settings(settings)
        answer_config = query_settings.answer
        prompt_config = query_settings.prompts

        if llm_model is None:
            llm_model = query_settings.get_llm()
        if summary_llm_model is None:
            summary_llm_model = query_settings.get_summary_llm()
        if embedding_model is None:
            embedding_model = query_settings.get_embedding_model()

        answer = (
            AnswerQuotesFormatted(question=query, config_md5=query_settings.md5)
            if isinstance(query, str)
            else query
        )

        contexts = answer.contexts

        if not contexts:
            answer = await self.aget_evidence(
                answer,
                callbacks=callbacks,
                settings=settings,
                embedding_model=embedding_model,
                summary_llm_model=summary_llm_model,
            )
            contexts = answer.contexts
        pre_str = None
        if prompt_config.pre is not None:
            with set_llm_answer_ids(answer.id):
                pre = await llm_model.run_prompt(
                    prompt=prompt_config.pre,
                    data={"question": answer.question},
                    callbacks=callbacks,
                    name="pre",
                    system_prompt=prompt_config.system,
                )
            answer.add_tokens(pre)
            pre_str = pre.text

        # sort by first score, then name
        filtered_contexts = sorted(
            contexts,
            key=lambda x: (-x.score, x.text.name),
        )[: answer_config.answer_max_sources]
        # remove any contexts with a score of 0
        filtered_contexts = [c for c in filtered_contexts if c.score > 0]

        # shim deprecated flag
        # TODO: remove in v6
        context_inner_prompt = prompt_config.context_inner
        if (
            not answer_config.evidence_detailed_citations
            and "\nFrom {citation}" in context_inner_prompt
        ):
            context_inner_prompt = context_inner_prompt.replace("\nFrom {citation}", "")

        inner_context_strs = [
            context_inner_prompt.format(
                name=c.text.name,
                text=c.context,
                quotes="\n".join(f"quote{i+1}: \"{p['quote']}\"" for i, p in enumerate(c.points)),
                citation=c.text.doc.citation,
                **(c.model_extra or {}),
            )
            for c in filtered_contexts
        ]
        if pre_str:
            inner_context_strs += (
                [f"Extra background information: {pre_str}"] if pre_str else []
            )

        context_str = prompt_config.context_outer.format(
            context_str="\n\n".join(inner_context_strs),
            valid_keys=", ".join([c.text.name for c in filtered_contexts]),
        )

        bib = OrderedDict()
        if len(context_str) < 10:  # noqa: PLR2004
            answer_text = (
                "I cannot answer this question due to insufficient information."
            )
        else:
            with set_llm_answer_ids(answer.id):
                answer_result = await llm_model.run_prompt(
                    prompt=prompt_config.qa,
                    data={
                        "context": context_str,
                        "answer_length": answer_config.answer_length,
                        "question": answer.question,
                        "example_citation": prompt_config.EXAMPLE_CITATION,
                        "example_citation_quote": prompt_config.example_citation_quote,
                    },
                    callbacks=callbacks,
                    name="answer",
                    system_prompt=prompt_config.system,
                )
            answer_text = answer_result.text
            answer.add_tokens(answer_result)
        # it still happens
        if prompt_config.EXAMPLE_CITATION in answer_text:
            answer_text = answer_text.replace(prompt_config.EXAMPLE_CITATION, "")
        for c in filtered_contexts:
            c.text = TextPlus.from_text(c.text)
            name = c.text.name
            # do check for whole key (so we don't catch Callahan2019a with Callahan2019)
            if name_in_text(name, answer_text):
                bib[name] = c
        bib_str = "\n\n".join(
            [f"{i+1}. ({k}): {c.text.doc.citation}" for i, (k, c) in enumerate(bib.items())]
        )

        if answer_config.answer_filter_extra_background:
            answer_text = re.sub(
                r"\([Ee]xtra [Bb]ackground [Ii]nformation\)",
                "",
                answer_text,
            )

        formatted_answer = f"Question: {answer.question}\n\n{answer_text}\n"
        if bib:
            formatted_answer += f"\nReferences\n\n{bib_str}\n"

        if prompt_config.post is not None:
            with set_llm_answer_ids(answer.id):
                post = await llm_model.run_prompt(
                    prompt=prompt_config.post,
                    data=answer.model_dump(),
                    callbacks=callbacks,
                    name="post",
                    system_prompt=prompt_config.system,
                )
            answer_text = post.text
            answer.add_tokens(post)
            formatted_answer = f"Question: {answer.question}\n\n{post}\n"
            if bib:
                formatted_answer += f"\nReferences\n\n{bib_str}\n"

        # now at end we modify, so we could have retried earlier
        answer.answer = answer_text
        answer.formatted_answer = formatted_answer
        answer.references = bib_str
        answer.contexts = contexts
        answer.context = context_str
        answer.filtered_contexts = filtered_contexts
        answer.bib = bib

        return answer  