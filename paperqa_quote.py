from paperqa import Docs, Settings
from paperqa.llms import LiteLLMEmbeddingModel
import os

paths = [
    "../sample_papers/14_74.pdf",
    # "../sample_papers/JBPE-8-127.pdf",
    # "/home/sweekiat/Downloads/Final IncomeShield policy conditions 1 Sep 2024.pdf",
]

docs = Docs()
for doc in paths:
    # docs.add(doc, settings=Settings(embedding="openai/text-embedding-3-large"))
    a = docs.add(doc,
        settings=Settings(
            llm="gemini/gemini-1.5-flash-002",
            summary_llm="gemini/gemini-1.5-flash-002",
            embedding="gemini/text-embedding-004",
    ))
    # print(docs.docs)
    # print(docs.texts)
    print(len(docs.texts))
    for text in docs.texts:
        print(text.text)
        # print(len(docs.texts[0].embedding))
