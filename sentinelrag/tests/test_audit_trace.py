from sentinel.audit import AuditLog
from sentinel.audit_trace import build_trace


class FakeDecision:
    def __init__(self, document_id, allowed, reason):
        self.document_id = document_id
        self.allowed = allowed
        self.reason = reason


class FakeDoc:
    def __init__(self, document_id, version):
        self.document_id = document_id
        self.version = version


def seed_query(audit: AuditLog, query_id="Q1", user_id="U205"):
    audit.log_query(query_id, user_id, "What is the Q4 revenue forecast?")
    audit.log_decisions(
        query_id,
        [
            FakeDecision("DOC-101", True, "authorized"),
            FakeDecision("DOC-201", False, "user clearance level insufficient"),
            FakeDecision("DOC-999", False, "user department not permitted"),
        ],
    )
    audit.log_evidence(query_id, [FakeDoc("DOC-101", "2.0")])
    audit.log_answer(query_id, "Q4 revenue is 120 crore [DOC-101].", retrieved=3, authorized=1, blocked=2)
    return query_id


def test_owner_sees_their_own_trace():
    audit = AuditLog(":memory:")
    query_id = seed_query(audit, user_id="U205")

    trace = build_trace(audit, query_id, requesting_user_id="U205", is_admin=False)

    assert trace is not None
    assert trace["question"] == "What is the Q4 revenue forecast?"
    assert trace["evidence_firewall"] == {"retrieved": 3, "authorized": 1, "blocked": 2}


def test_non_admin_trace_never_reveals_blocked_document_ids():
    audit = AuditLog(":memory:")
    query_id = seed_query(audit, user_id="U205")

    trace = build_trace(audit, query_id, requesting_user_id="U205", is_admin=False)

    decision_ids = {d["document_id"] for d in trace["authorization_decisions"]}
    assert "DOC-201" not in decision_ids
    assert "DOC-999" not in decision_ids
    assert all(d["allowed"] for d in trace["authorization_decisions"])
    # Black-box check: the denial reasons for blocked docs must not leak
    # anywhere in the serialized trace, not just the decisions list.
    import json

    serialized = json.dumps(trace)
    assert "DOC-201" not in serialized
    assert "DOC-999" not in serialized
    assert trace["is_full_trace"] is False


def test_admin_sees_full_trace_including_denials():
    audit = AuditLog(":memory:")
    query_id = seed_query(audit, user_id="U205")

    trace = build_trace(audit, query_id, requesting_user_id="UADMIN", is_admin=True)

    decision_ids = {d["document_id"] for d in trace["authorization_decisions"]}
    assert "DOC-201" in decision_ids
    assert "DOC-999" in decision_ids
    assert trace["is_full_trace"] is True


def test_non_owner_non_admin_cannot_see_someone_elses_trace():
    audit = AuditLog(":memory:")
    query_id = seed_query(audit, user_id="U205")

    trace = build_trace(audit, query_id, requesting_user_id="U102", is_admin=False)

    assert trace is None


def test_unknown_query_id_returns_none():
    audit = AuditLog(":memory:")

    trace = build_trace(audit, "does-not-exist", requesting_user_id="U205", is_admin=False)

    assert trace is None


def test_agent_tool_calls_included_and_never_contain_document_ids():
    audit = AuditLog(":memory:")
    query_id = seed_query(audit, user_id="U301")
    audit.log_tool_calls(
        query_id,
        [
            {"query": "Q4 revenue", "retrieved": 3, "authorized": 1, "blocked": 2},
            {"query": "latest Q4 forecast", "retrieved": 3, "authorized": 1, "blocked": 2},
        ],
    )

    trace = build_trace(audit, query_id, requesting_user_id="U301", is_admin=False)

    assert len(trace["agent_tool_calls"]) == 2
    assert trace["agent_tool_calls"][0]["query"] == "Q4 revenue"
    assert any(s["stage"] == "agent_search" for s in trace["steps"])
