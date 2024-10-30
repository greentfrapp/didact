import argparse
import os

from dotenv import load_dotenv

from paperqa import Settings
from paperqa.settings import AnswerSettings

from quote_docs import (
    CONTEXT_INNER_PROMPT_WITH_QUOTE,
    example_citation_quote,
    point_form_json_system_prompt_with_quote,
    qa_quote_prompt,
    PromptQuoteSettings,
)
from upload_docs import UploadDocs


load_dotenv()


def main(query: str):
    docs = UploadDocs(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_service_key=os.environ["SUPABASE_SERVICE_KEY"],
    )

    response = docs.query(
        query,
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
            answer=AnswerSettings(
                evidence_k=20,
                answer_max_sources=10,
            ),
        )
    )

    print()
    print(response.formatted_answer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    main(args.query)
