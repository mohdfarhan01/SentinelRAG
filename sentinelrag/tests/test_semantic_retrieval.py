from sentinel.models import Document
from sentinel.semantic_retrieval import SemanticRetrievalAgent


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


def test_paraphrased_query_with_no_shared_keywords_still_finds_the_document(tmp_path):
    """This is the actual capability gap semantic retrieval closes: a
    keyword-only search for this phrasing would find nothing, since it
    shares no exact words with the document."""
    doc = make_doc(
        document_id="DOC-101",
        title="Q4 Revenue Forecast",
        content="Q4 projected revenue is 120 crore.",
    )
    other = make_doc(document_id="DOC-102", title="Engineering Roadmap", content="The next release ships in October.")

    agent = SemanticRetrievalAgent(persist_dir=str(tmp_path / "chroma"))
    results = agent.search("what are the quarterly earnings projections", [doc, other], top_k=5)

    result_ids = [d.document_id for d, _score in results]
    assert "DOC-101" in result_ids


def test_unrelated_query_returns_nothing_above_the_relevance_threshold(tmp_path):
    doc = make_doc(document_id="DOC-101", content="Q4 projected revenue is 120 crore.")

    agent = SemanticRetrievalAgent(persist_dir=str(tmp_path / "chroma"))
    results = agent.search("what is the office holiday schedule for December", [doc], top_k=5)

    assert results == []


def test_resolves_against_the_live_document_not_a_cached_copy(tmp_path):
    """The vector index must never be trusted as a system of record --
    if a document's classification changes after indexing, the next
    search must reflect the current value, not whatever was indexed."""
    agent = SemanticRetrievalAgent(persist_dir=str(tmp_path / "chroma"))
    doc = make_doc(document_id="DOC-101", classification="Internal")
    agent.search("Q4 revenue forecast", [doc], top_k=5)

    updated_doc = make_doc(document_id="DOC-101", classification="Restricted")
    results = agent.search("Q4 revenue forecast", [updated_doc], top_k=5)

    assert results[0][0].classification == "Restricted"
