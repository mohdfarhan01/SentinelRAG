from datetime import date

from sentinel.audit import AuditLog
from sentinel.document_store import DocumentStore
from sentinel.models import Document, User
from sentinel.orchestrator import SentinelRAGPipeline
from tests.test_agent_loop import FakeLLMClient
from sentinel.agent_loop import AgentLoop

TODAY = date(2026, 9, 18)


def build_pipeline():
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
        )
    ]
    store = DocumentStore(docs)
    return SentinelRAGPipeline(store, audit_log=AuditLog(":memory:"))


RESPONSE_KEYS = {"query_id", "answer", "citations", "evidence_firewall", "conflicts", "llm_mode"}


def test_deterministic_path_response_shape():
    pipeline = build_pipeline()  # no LLM configured in the test environment -> STUB mode
    user = User("U102", "Finance", "Finance", "Internal")

    result = pipeline.run(user, "What is the Q4 revenue forecast?", today=TODAY)

    assert RESPONSE_KEYS.issubset(result.keys())
    assert result["llm_mode"] == "stub"
    assert "120 crore" in result["answer"]


def test_agentic_path_response_shape_matches_deterministic():
    pipeline = build_pipeline()
    fake = FakeLLMClient(queries_to_issue=["Q4 revenue forecast"], final_answer="120 crore [DOC-101].")
    pipeline.llm_client = fake
    pipeline.agent_loop = AgentLoop(fake)

    user = User("U102", "Finance", "Finance", "Internal")
    result = pipeline.run(user, "What is the Q4 revenue forecast?", today=TODAY)

    assert RESPONSE_KEYS.issubset(result.keys())
    assert result["llm_mode"] == "fake"
    assert "120 crore" in result["answer"]
    assert any(c["document_id"] == "DOC-101" for c in result["citations"])


def test_agentic_mode_can_be_forced_off_via_env(monkeypatch):
    monkeypatch.setenv("AGENTIC_MODE", "false")
    pipeline = build_pipeline()
    fake = FakeLLMClient(queries_to_issue=["Q4 revenue forecast"], final_answer="should not be used")
    pipeline.llm_client = fake
    pipeline.agent_loop = AgentLoop(fake)

    user = User("U102", "Finance", "Finance", "Internal")
    result = pipeline.run(user, "What is the Q4 revenue forecast?", today=TODAY)

    # Falls back to the deterministic path even though an "enabled" LLM
    # client is present, because AGENTIC_MODE=false.
    assert "120 crore" in result["answer"]
    assert fake.observations == []
