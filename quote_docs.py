from collections.abc import Callable
from pydantic import Field, field_validator
import re

from paperqa.docs import Docs
from paperqa.llms import EmbeddingModel, LLMModel
from paperqa.settings import (
    MaybeSettings,
    PromptSettings,
    get_settings,
    get_formatted_variables,
)
from paperqa.types import (
    Answer,
    Context,
    set_llm_answer_ids,
)
from paperqa.utils import (
    name_in_text,
)


summary_json_system_prompt_with_quote = """\
Provide a summary of the relevant information that could help answer the question based on the excerpt. Respond with the following JSON format:

{{
  "summary": "...",
  "relevance_score": "...",
  "quote": "..."
}}

where `summary` is relevant information from text - {summary_length} words, `relevance_score` is the relevance of `summary` to answer question (out of 10), and `quote` is an exact-match quote (max 50 words) from the text that best supports the summary.
"""  # noqa: E501


# In `points`, having the LLM generate `quote` before `point` grounds the points better in their respective quotes.
point_form_json_system_prompt_with_quote = """\
Provide a summary of the relevant information that could help answer the question based on the excerpt. Respond with the following JSON format:

{{
  "summary": "...",
  "relevance_score": "...",
  "points": [
    {{
        "quote": "...",
        "point": "..."
    }}
  ]
}}

where `summary` is relevant information from text - {summary_length} words, `relevance_score` is the relevance of `summary` to answer question (out of 10), and `points` is an array of `point` and `quote` pairs that supports the summary where each `quote` is an exact match quote (max 50 words) from the text that best supports the respective `point`. Make sure that the quote is an exact match without truncation or changes. Do not truncate the quote with any ellipsis.
"""  # noqa: E501

CONTEXT_INNER_PROMPT_WITH_QUOTE = "{name}: {text}\n{quotes}\nFrom {citation}"

retrieve_relevant_quote_json_system_prompt = """\
Retrieve a quote from the text that best supports the claim. Respond with the following JSON format:

{{
  "quote": "..."
}}

where `quote` is an exact-match phrase or sentence (max 50 words) from the text that best supports the claim.
"""

retrieve_relevant_quote_json_prompt = (
    "Excerpt from {citation}\n\n----\n\n{text}\n\n----\n\nClaim: {claim}\n\n"
)

example_citation_quote = "(Example2012Example pages 3-4 quote1, quote2, Example2012Example pages 10-13 quote1)"


# qa_quote_prompt = (
#     "Answer the question below with the context.\n\n"
#     "Context (with relevance scores):\n\n{context}\n\n----\n\n"
#     "Question: {question}\n\n"
#     "Write an answer based on the context. "
#     "If the context provides insufficient information reply "
#     '"I cannot answer."'
#     "For each part of your answer, indicate which sources most support "
#     "it via citation keys at the end of sentences, "
#     "like {example_citation}. Only cite from the context "
#     "below and only use the valid keys. "
#     "In the citation, reference a quote if relevant like {example_citation_quote}. "
#     "Do not repeat any part of the quote in your answer. "
#     "A citation will be sufficient. "
#     "Write in the style of a "
#     "Wikipedia article, with concise sentences and coherent paragraphs. "
#     "The context comes from a variety of sources and is only a summary, "
#     "so there may inaccuracies or ambiguities. If quotes are present and "
#     "relevant, use them in the answer. This answer will go directly onto "
#     "Wikipedia, so do not add any extraneous information. "
#     "Split your answer into paragraphs with about 50 to 60 words per paragraph. "
#     "\n\n"
#     "Answer ({answer_length}):"
# )

qa_quote_prompt = (
    "Answer the question below with the context.\n\n"
    "Context (with relevance scores):\n\n{context}\n\n----\n\n"
    "Question: {question}\n\n"
    "Write an answer based on the context. "
    "If the context provides insufficient information reply "
    '"I cannot answer."'
    "For each part of your answer, indicate which sources most support "
    "it via citation keys at the end of sentences, "
    "like {example_citation}. Only cite from the context "
    "below and only use the valid keys. "
    "In the citation, reference a quote if relevant like {example_citation_quote}. "
    "Do not repeat any part of the quote in your answer. "
    "A citation will be sufficient. "
    "Write in a style accessible to the layperson but keep your "
    "wording and content accurate without any misrepresentation. "
    "The context comes from a variety of sources and is only a summary, "
    "so there may inaccuracies or ambiguities. Do not add any extraneous information. "
    "Split your answer into paragraphs with about 50 to 60 words per paragraph. "
    "\n\n"
    "Answer ({answer_length}):"
)


class AnswerQuotes(Answer):
    bib: dict[str, Context] = Field(default_factory=dict)
    filtered_contexts: list[Context] = Field(default_factory=list)


class PromptQuoteSettings(PromptSettings):
    example_citation_quote: str = ""

    # Overwrite field_validator in PromptSettings to customize QA prompt
    @field_validator("qa")
    @classmethod
    def check_qa(cls, v: str) -> str:
        if not get_formatted_variables(v).issubset(get_formatted_variables(qa_quote_prompt)):
            raise ValueError(
                "QA prompt can only have variables:"
                f" {get_formatted_variables(qa_quote_prompt)}"
            )
        return v


class QuoteDocs(Docs):

    async def aquery(  # noqa: PLR0912
        self,
        query: Answer | str,
        settings: MaybeSettings = None,
        callbacks: list[Callable] | None = None,
        llm_model: LLMModel | None = None,
        summary_llm_model: LLMModel | None = None,
        embedding_model: EmbeddingModel | None = None,
    ) -> AnswerQuotes:

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
            AnswerQuotes(question=query, config_md5=query_settings.md5)
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

        bib = {}
        bib_contexts = {}
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
            name = c.text.name
            citation = c.text.doc.citation
            # do check for whole key (so we don't catch Callahan2019a with Callahan2019)
            if name_in_text(name, answer_text):
                print(f"\n{name}")
                print(c.points)
                bib[name] = citation
                # bib[name] = f"{citation}, \"{c.quote}\""
                bib_contexts[name] = c
        bib_str = "\n\n".join(
            [f"{i+1}. ({k}): {c}" for i, (k, c) in enumerate(bib.items())]
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
        answer.bib = bib_contexts

        return answer        
