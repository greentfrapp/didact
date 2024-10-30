from pydantic import Field
from typing import List
import re

import numpy as np

from paperqa.types import (
    Answer,
    Context,
    Text,
)


class TextPlus(Text):
    pages: List[int] = []

    @classmethod
    def from_text(cls, text: Text):
        # Retrieve page numbers
        pattern = re.compile(".*? pages (\\d+)-(\\d+)")
        matches = pattern.match(text.name)
        if matches:
            start = int(matches.groups()[0])
            end = int(matches.groups()[1])
            return cls(
                text=text.text,
                name=text.name,
                doc=text.doc,
                pages=[n+start for n in np.arange(end-start+1)],
                embedding=text.embedding,
            )
        else:
            return cls(
                text=text.text,
                name=text.name,
                doc=text.doc,
                embedding=text.embedding,
            )


class AnswerQuotesFormatted(Answer):
    bib: dict[str, Context] = Field(default_factory=dict)
    filtered_contexts: list[Context] = Field(default_factory=list)
