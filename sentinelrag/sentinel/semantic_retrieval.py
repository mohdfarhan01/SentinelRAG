from __future__ import annotations

from typing import List, Tuple

from .models import Document
from .vector_store import ChromaVectorStore


class SemanticRetrievalAgent:
    """Same `search()` contract as RetrievalAgent (sentinel/retrieval.py):
    whole document list in, ranked (Document, score) pairs out. Backed by
    ChromaDB embeddings instead of keyword overlap, so a paraphrased
    question with none of a document's exact words can still find it.

    Authorization, conflict resolution, and citation validation never
    change based on which retrieval backend is active -- they only ever
    see the Document objects this returns, resolved from the live
    document store, never from the vector index's own cached copy.
    """

    def __init__(self, persist_dir: str = "chroma_data") -> None:
        self.store = ChromaVectorStore(persist_dir=persist_dir)

    def search(self, query: str, documents: List[Document], top_k: int = 10) -> List[Tuple[Document, float]]:
        self.store.sync(documents)
        hits = self.store.search(query, top_k)
        by_id = {d.document_id: d for d in documents}
        return [(by_id[doc_id], score) for doc_id, score in hits if doc_id in by_id]
