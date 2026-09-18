from __future__ import annotations


def create_retrieval_agent(persist_dir: str = "chroma_data"):
    """Returns the best available retrieval backend: keyword+semantic
    hybrid if chromadb is installed and usable, otherwise plain
    keyword-only. Both implement the exact same search() interface, so
    every caller -- the deterministic path and the agentic tool -- gets
    the same upgrade automatically and never needs to know which backend
    it actually got.

    Broad except, deliberately: a demo shouldn't crash because chromadb
    isn't installed, or its on-disk index can't be created for some
    environment-specific reason. Falling back to keyword-only is always
    a safe, working default.
    """
    try:
        from .hybrid_retrieval import HybridRetrievalAgent

        return HybridRetrievalAgent(persist_dir=persist_dir)
    except Exception:
        from .retrieval import RetrievalAgent

        return RetrievalAgent()
