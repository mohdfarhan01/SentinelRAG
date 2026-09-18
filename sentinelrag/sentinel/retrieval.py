from __future__ import annotations

import re
from typing import List, Tuple

from .models import Document

_STOPWORDS = {
    "what", "is", "the", "a", "an", "of", "for", "to", "was", "were",
    "in", "on", "latest", "are", "and", "or", "does", "do", "can",
}


def _tokenize(text: str) -> set:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


class RetrievalAgent:
    """Deterministic keyword/metadata retrieval -- no embeddings, no LLM.

    Runs over the ENTIRE document store regardless of who is asking.
    Relevance is decided independently of authorization on purpose: the
    Authorization Gatekeeper that runs immediately after this is what
    proves a relevant-but-restricted document never leaks, rather than
    retrieval quietly hiding it before the firewall gets a chance to.
    """

    def search(self, query: str, documents: List[Document], top_k: int = 10) -> List[Tuple[Document, float]]:
        query_tokens = _tokenize(query)
        scored = []
        for doc in documents:
            doc_tokens = _tokenize(doc.title) | _tokenize(doc.content)
            overlap = query_tokens & doc_tokens
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            scored.append((doc, score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]
