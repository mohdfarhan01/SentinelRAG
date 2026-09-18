from __future__ import annotations

from typing import List, Tuple

from .models import Document
from .retrieval import RetrievalAgent
from .semantic_retrieval import SemanticRetrievalAgent

RRF_K = 60


class HybridRetrievalAgent:
    """Fuses keyword overlap (RetrievalAgent) and semantic similarity
    (SemanticRetrievalAgent) via Reciprocal Rank Fusion, so a paraphrased
    question can still be found while exact-term/ID lookups that keyword
    matching already handles well don't regress. Same search() interface
    as RetrievalAgent -- this is a pure ranking change; nothing
    downstream (authorization, conflict resolution, citations) needs to
    know or care which retrieval backend produced its candidates.
    """

    def __init__(self, persist_dir: str = "chroma_data") -> None:
        self.keyword = RetrievalAgent()
        self.semantic = SemanticRetrievalAgent(persist_dir=persist_dir)

    def search(self, query: str, documents: List[Document], top_k: int = 10) -> List[Tuple[Document, float]]:
        keyword_hits = self.keyword.search(query, documents, top_k=top_k)
        semantic_hits = self.semantic.search(query, documents, top_k=top_k)

        rrf_scores: dict = {}
        docs_by_id: dict = {}
        for ranked_list in (keyword_hits, semantic_hits):
            for rank, (doc, _score) in enumerate(ranked_list):
                docs_by_id[doc.document_id] = doc
                rrf_scores[doc.document_id] = rrf_scores.get(doc.document_id, 0.0) + 1.0 / (RRF_K + rank + 1)

        ranked_ids = sorted(rrf_scores, key=lambda doc_id: rrf_scores[doc_id], reverse=True)
        return [(docs_by_id[doc_id], rrf_scores[doc_id]) for doc_id in ranked_ids[:top_k]]
