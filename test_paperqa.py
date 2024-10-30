import os

from paperqa import Docs, Settings
from paperqa.settings import PromptSettings
from paperqa.llms import LiteLLMEmbeddingModel

from quote_docs import (
    CONTEXT_INNER_PROMPT_WITH_QUOTE,
    example_citation_quote,
    point_form_json_system_prompt_with_quote,
    qa_quote_prompt,
    summary_json_system_prompt_with_quote,
    PromptQuoteSettings,
    QuoteDocs,
)


paths = [
    "../sample_papers/14_74.pdf",
    # "../sample_papers/JBPE-8-127.pdf",
    # "/home/sweekiat/Downloads/Final IncomeShield policy conditions 1 Sep 2024.pdf",
]

docs = QuoteDocs()
for doc in paths:
    # docs.add(doc, settings=Settings(embedding="openai/text-embedding-3-large"))
    a = docs.add(doc,
        settings=Settings(
            llm="gemini/gemini-1.5-flash-002",
            summary_llm="gemini/gemini-1.5-flash-002",
            embedding="gemini/text-embedding-004",
    ))

response = docs.query(
    "What is natto?",
    settings=Settings(
        llm="gemini/gemini-1.5-flash-002",
        summary_llm="gemini/gemini-1.5-flash-002",
        embedding="gemini/text-embedding-004",
        prompts=PromptQuoteSettings(
            summary_json_system=point_form_json_system_prompt_with_quote,
            context_inner=CONTEXT_INNER_PROMPT_WITH_QUOTE,
            qa=qa_quote_prompt,
            example_citation_quote=example_citation_quote,
        ),
    )
)

print()
print(response)
# print([(b, c.quote) for b, c in response.bib.items()])
