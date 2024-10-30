from pathlib import Path
import asyncio
import os

from dotenv import load_dotenv

from paperqa import Settings
from upload_docs import UploadDocs

load_dotenv()

pdfs = [
    {
        "path": "./papers/AIA HealthShield Gold Max Brochure.pdf",
        "title": "AIA HealthShield Gold Max Brochure",
        "abstract": "AIA HealthShield Gold Max is a MediSave-approved Integrated Shield Plan consisting of MediShield Life and private insurance coverage for private or public hospital treatment",
    },
    {
        "path": "./papers/AIA HealthShield Gold Max Product Summary Booklet (truncated).pdf",
        "title": "AIA HealthShield Gold Max Product Summary Booklet",
        "abstract": "AIA HealthShield Gold Max is issued under a joint insurance arrangement with the Central Provident Fund (CPF) Board to enhance the coverage provided by MediShield Life. The insured will be covered by AIA HealthShield Gold Max and MediShield Life at the same time and, upon making a claim, we will pay the higher of the benefits under both plans.",
    }
]


async def main():
    docs = UploadDocs(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_service_key=os.environ["SUPABASE_SERVICE_KEY"],
    )
    for pdf in pdfs:
        await docs.aupload(
            path=pdf["path"],
            title=pdf["title"],
            abstract=pdf["abstract"],
            settings=Settings(
                llm="gemini/gemini-1.5-flash-002",
                summary_llm="gemini/gemini-1.5-flash-002",
                embedding="gemini/text-embedding-004",
            ),
            ignore_duplicate_doc=True,
        )


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
