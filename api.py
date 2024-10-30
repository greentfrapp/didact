import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from paperqa import Settings
from quote_docs import (
    CONTEXT_INNER_PROMPT_WITH_QUOTE,
    example_citation_quote,
    point_form_json_system_prompt_with_quote,
    qa_quote_prompt,
    PromptQuoteSettings,
)
from upload_docs import UploadDocs


load_dotenv()

docs = UploadDocs(
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_service_key=os.environ["SUPABASE_SERVICE_KEY"],
)


app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
origins = [
    # "http://localhost",
    # "http://localhost:8080",
    "http://localhost:5173",
    # "http://localhost:5174",
    "https://app.pebblely.com",
    "https://app-dev.pebblely.com",
    "https://pebblely.com",
    "https://www.pebblely.com",
    "https://dev.pebblely.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryPayload(BaseModel):
    query: str


@app.post("/query")
def send_otp(payload: QueryPayload):
    response = docs.query(
        payload.query,
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

    # Convert citations into <cite> tags
    docnames = "|".join(set(b.text.doc.docname for b in response.bib.values()))
    citation_group_pattern = re.compile(f"\\(({docnames}) pages \\d+-\\d+( quote\\d+(, quote\\d+)*)?((,|;) ({docnames}) pages \\d+-\\d+( quote\\d+((,|;) quote\\d+)*)?)*\\)")
    citation_single_pattern = re.compile(f"((?P<citation>({docnames}) pages \\d+-\\d+)(?P<quotes> quote\\d+((,|;) quote\\d+)*)?)((,|;) )?")

    def replace_individual_citations(match: re.Match):
        quotes_text = match.groupdict()["quotes"]
        if quotes_text:
            quotes_formatted = re.sub("(?P<q>quote\\d+)(, )?", lambda q: f"<quote>{q.groupdict()['q']}</quote>", quotes_text)
        else:
            quotes_formatted = ""
        return f"<doc>{match.groupdict()['citation'].strip()}{quotes_formatted}</doc>"

    def replace_with_tag(match: re.Match):
        text = match.group().strip("(").strip(")")
        new_text = re.sub(citation_single_pattern, replace_individual_citations, text)
        return f"<cite>{new_text}</cite>"

    response.answer = re.sub(citation_group_pattern, replace_with_tag, response.answer.strip())

    period_citation_pattern = re.compile(f"\\.\\s*?(?P<citation><cite>.*?</cite>)")
    def move_period_mark(match: re.Match):
        return f"{match.groupdict()['citation']}."
    
    response.answer = re.sub(period_citation_pattern, move_period_mark, response.answer)

    # Format response
    return {
        "question": response.question,
        "text": response.answer,
        "references": [
            {
                "id": b.text.name,
                "value": b.text.doc.citation,
                "pages": b.text.pages,
                "quotes": b.points,
            } for b in response.bib.values()
        ]
    }
