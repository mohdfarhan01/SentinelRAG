from sentinel.hybrid_retrieval import HybridRetrievalAgent
from sentinel.models import Document


def make_doc(**overrides) -> Document:
    base = dict(
        document_id="DOC-X",
        title="Q4 Revenue Forecast",
        classification="Internal",
        content="Q4 projected revenue is 120 crore.",
        version="1.0",
        effective_date="2026-01-01",
        allowed_departments=[],
        allowed_roles=[],
    )
    base.update(overrides)
    return Document.from_dict(base)


def test_exact_document_id_still_ranks_highly(tmp_path):
    """Proves the hybrid fusion doesn't regress what keyword matching
    already does well: an exact, distinctive term should still surface
    its document even with semantic search fused in."""
    target = make_doc(document_id="DOC-777", title="Vendor Contract XZQ-9981", content="Terms for vendor XZQ-9981.")
    other = make_doc(document_id="DOC-778", title="Engineering Roadmap", content="Next release in October.")

    agent = HybridRetrievalAgent(persist_dir=str(tmp_path / "chroma"))
    results = agent.search("XZQ-9981", [target, other], top_k=5)

    assert results
    assert results[0][0].document_id == "DOC-777"


def test_paraphrased_query_still_finds_the_document_via_semantic_side():
    """The capability keyword-only retrieval lacks: closes via the
    semantic half of the fusion even when no exact words overlap."""
    doc = make_doc(document_id="DOC-101", content="Q4 projected revenue is 120 crore.")
    other = make_doc(document_id="DOC-102", title="Engineering Roadmap", content="Next release in October.")

    agent = HybridRetrievalAgent()
    results = agent.search("what are the quarterly earnings projections", [doc, other], top_k=5)

    result_ids = [d.document_id for d, _score in results]
    assert "DOC-101" in result_ids


def test_documents_found_by_both_signals_rank_above_single_signal_hits():
    strong = make_doc(
        document_id="DOC-101",
        title="Q4 Revenue Forecast",
        content="Q4 projected revenue is 120 crore.",
    )
    keyword_only = make_doc(
        document_id="DOC-999",
        title="Random Q4 Notes",
        content="Q4 team offsite scheduled for a hotel in the mountains.",
    )

    agent = HybridRetrievalAgent()
    results = agent.search("Q4 revenue forecast", [strong, keyword_only], top_k=5)

    result_ids = [d.document_id for d, _score in results]
    assert result_ids[0] == "DOC-101"
