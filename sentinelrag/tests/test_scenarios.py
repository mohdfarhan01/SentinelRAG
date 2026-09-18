"""End-to-end tests against the three official PS14 test inputs.

These build the exact documents/users given in Problem_statement.txt in
isolation (not from data/documents.json) so they verify the pipeline
against the official spec regardless of how the demo corpus evolves.
"""

from datetime import date

from sentinel.audit import AuditLog
from sentinel.document_store import DocumentStore
from sentinel.models import Document, User
from sentinel.orchestrator import SentinelRAGPipeline

TODAY = date(2026, 9, 18)


def build_pipeline(documents):
    store = DocumentStore(documents)
    audit = AuditLog(":memory:")
    return SentinelRAGPipeline(store, audit_log=audit)


def test_scenario_a_authorized_answer():
    docs = [
        Document.from_dict(
            {
                "document_id": "DOC-101",
                "title": "Q4 Revenue Forecast",
                "classification": "Internal",
                "allowed_departments": ["Finance"],
                "allowed_roles": ["Finance"],
                "version": "2.0",
                "effective_date": "2026-09-01",
                "content": "Q4 projected revenue is 120 crore.",
            }
        ),
        Document.from_dict(
            {
                "document_id": "DOC-102",
                "title": "Engineering Roadmap",
                "classification": "Internal",
                "allowed_departments": ["Engineering"],
                "allowed_roles": ["Engineer"],
                "version": "1.0",
                "effective_date": "2026-08-01",
                "content": "The next platform release is planned for October.",
            }
        ),
    ]
    user = User("U102", "Finance", "Finance", "Internal")
    pipeline = build_pipeline(docs)
    result = pipeline.run(user, "What is the Q4 revenue forecast?", today=TODAY)

    assert result["evidence_firewall"]["authorized"] == 1
    assert result["evidence_firewall"]["blocked"] == 0
    assert "120 crore" in result["answer"]
    assert any(c["document_id"] == "DOC-101" for c in result["citations"])


def test_scenario_b_relevant_but_unauthorized():
    docs = [
        Document.from_dict(
            {
                "document_id": "DOC-201",
                "title": "Q4 Revenue Forecast",
                "classification": "Restricted",
                "allowed_departments": ["Executive"],
                "allowed_roles": ["Executive"],
                "version": "3.0",
                "effective_date": "2026-09-01",
                "content": "Q4 projected revenue is 145 crore.",
            }
        ),
    ]
    user = User("U205", "Marketing", "Marketing", "Internal")
    pipeline = build_pipeline(docs)
    result = pipeline.run(user, "What is the Q4 revenue forecast?", today=TODAY)

    assert result["evidence_firewall"]["authorized"] == 0
    assert result["evidence_firewall"]["blocked"] == 1
    # Zero exposure: no content, no classification, no document id in the answer.
    assert "145" not in result["answer"]
    assert "Restricted" not in result["answer"]
    assert "DOC-201" not in result["answer"]
    assert result["citations"] == []


def test_scenario_c_authorized_conflict_resolves_to_latest():
    docs = [
        Document.from_dict(
            {
                "document_id": "DOC-301",
                "title": "Q4 Forecast",
                "classification": "Internal",
                "allowed_departments": ["Finance"],
                "allowed_roles": ["Finance"],
                "version": "1.0",
                "effective_date": "2026-06-01",
                "content": "Q4 projected revenue is 110 crore.",
            }
        ),
        Document.from_dict(
            {
                "document_id": "DOC-302",
                "title": "Q4 Forecast",
                "classification": "Internal",
                "allowed_departments": ["Finance"],
                "allowed_roles": ["Finance"],
                "version": "2.0",
                "effective_date": "2026-09-01",
                "content": "Q4 projected revenue is 125 crore.",
            }
        ),
    ]
    user = User("U301", "Finance", "Finance", "Internal")
    pipeline = build_pipeline(docs)
    result = pipeline.run(user, "What is the latest Q4 revenue forecast?", today=TODAY)

    assert "125 crore" in result["answer"]
    assert any(c["document_id"] == "DOC-302" for c in result["citations"])
    assert not any(c["document_id"] == "DOC-301" for c in result["citations"])
    assert result["conflicts"] == []
