from __future__ import annotations

import os
import uuid
from typing import List, Optional, Tuple

from .models import Document

# Adapted from a teammate's separate SentinelRAG prototype (its
# src/rag/vector_store.py): same core idea -- a persistent Chroma
# collection using Chroma's bundled default embedding model (local, no
# API key), with a cosine-distance cutoff to drop irrelevant hits.
#
# One deliberate change from that version: this store is never asked to
# reconstruct a Document from its own cached metadata. It only ever
# returns (document_id, score) pairs; the caller (SemanticRetrievalAgent)
# resolves each id back to the live Document from the current document
# store. That way a document's classification/ACL is always read fresh,
# even if it changed since the index was last synced -- the vector index
# is a search aid, never a system of record.


class ChromaVectorStore:
    """Persistent on-disk vector index for semantic document search.

    Defaults to a random collection name so that separate instances --
    separate test cases, or a pipeline rebuilt in a new process -- never
    share index state by accident, even though they share the same
    on-disk directory (Chroma keeps collections logically separate
    within one persist_dir). `sync()` re-populates a fresh collection
    from the live document store on the very next search anyway, so this
    costs nothing in practice: nothing here is a system of record.
    """

    def __init__(self, persist_dir: str = "chroma_data", collection_name: Optional[str] = None) -> None:
        import chromadb
        from chromadb.config import Settings

        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        collection_name = collection_name or f"sentinel_docs_{uuid.uuid4().hex[:12]}"
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def sync(self, documents: List[Document]) -> None:
        """Upserts the current document set into the index. Idempotent,
        and cheap enough at hackathon scale to call on every search --
        RetrievalAgent.search() already receives the whole store on every
        call, so this keeps the index current without a separate
        ingestion hook anywhere else in the codebase."""
        if not documents:
            return
        ids = [d.document_id for d in documents]
        texts = [f"{d.title}\n{d.content}" for d in documents]
        self.collection.upsert(ids=ids, documents=texts)

    def search(self, query_text: str, top_k: int, distance_threshold: float = 0.60) -> List[Tuple[str, float]]:
        """Returns (document_id, score) pairs, score = 1 - cosine
        distance (higher is more relevant), for hits within
        distance_threshold. distance_threshold=0.60 matches the value
        validated in the prototype this was adapted from."""
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.query(query_texts=[query_text], n_results=min(top_k, count))

        hits: List[Tuple[str, float]] = []
        if results and results.get("ids") and results.get("distances"):
            for doc_id, distance in zip(results["ids"][0], results["distances"][0]):
                if distance > distance_threshold:
                    continue
                hits.append((doc_id, 1.0 - distance))
        return hits
