from __future__ import annotations

import json
from pathlib import Path
from typing import List, Union

from .models import Document


class DocumentStore:
    """The full corpus, regardless of who is asking. Authorization is never
    applied here -- this is deliberate, so that retrieval can find a
    relevant-but-restricted document, and the Evidence Firewall downstream
    is the thing that proves it caught it."""

    def __init__(self, documents: List[Document]):
        self._documents = documents

    @classmethod
    def from_json_file(cls, path: Union[str, Path]) -> "DocumentStore":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return cls([Document.from_dict(d) for d in raw])

    def all(self) -> List[Document]:
        return list(self._documents)
