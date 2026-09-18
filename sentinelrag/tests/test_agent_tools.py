from datetime import date

from sentinel.agent_tools import DocumentSearchTool
from sentinel.models import Document, User

TODAY = date(2026, 9, 18)


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


def test_authorized_query_returns_content():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc(allowed_departments=["Finance"], allowed_roles=["Finance"])
    tool = DocumentSearchTool(user, [doc], TODAY)

    result = tool.run("Q4 revenue forecast")

    assert "120 crore" in result
    assert "DOC-X" in result


def test_denied_document_content_never_appears_in_tool_output():
    user = User("U205", "Marketing", "Marketing", "Internal")
    doc = make_doc(
        document_id="DOC-201",
        classification="Restricted",
        content="Q4 projected revenue is 145 crore.",
        allowed_departments=["Executive"],
        allowed_roles=["Executive"],
    )
    tool = DocumentSearchTool(user, [doc], TODAY)

    result = tool.run("Q4 revenue forecast")

    # Zero exposure: no content, no document id, no classification.
    assert "145" not in result
    assert "DOC-201" not in result
    assert "Restricted" not in result
    assert tool.call_log[0]["authorized"] == 0
    assert tool.call_log[0]["blocked"] == 1


def test_call_cap_is_enforced_regardless_of_how_many_times_the_model_calls():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc(allowed_departments=["Finance"], allowed_roles=["Finance"])
    tool = DocumentSearchTool(user, [doc], TODAY, max_calls=3)

    for _ in range(6):
        tool.run("Q4 revenue forecast")

    # Only the first 3 calls should have performed a real search.
    assert len(tool.call_log) == 3


def test_call_cap_response_does_not_leak_evidence_after_limit():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc(allowed_departments=["Finance"], allowed_roles=["Finance"])
    tool = DocumentSearchTool(user, [doc], TODAY, max_calls=1)

    tool.run("first search")
    second_result = tool.run("second search")

    assert "limit reached" in second_result.lower()
    assert len(tool.call_log) == 1


def test_no_evidence_found_message_does_not_reveal_blocked_metadata():
    user = User("U205", "Marketing", "Marketing", "Internal")
    doc = make_doc(
        document_id="DOC-201",
        title="CEO Compensation Report",
        classification="Restricted",
        allowed_departments=["Executive"],
        allowed_roles=["Executive"],
    )
    tool = DocumentSearchTool(user, [doc], TODAY)

    result = tool.run("CEO compensation")

    assert "No authorized evidence" in result
    assert "CEO Compensation Report" not in result
    assert "DOC-201" not in result
    assert "1 relevant document" in result  # aggregate count only


def test_conflict_resolves_to_latest_version_via_tool():
    user = User("U301", "Finance", "Finance", "Internal")
    docs = [
        make_doc(document_id="DOC-301", title="Q4 Forecast", version="1.0",
                 effective_date="2026-06-01", content="Q4 projected revenue is 110 crore.",
                 allowed_departments=["Finance"], allowed_roles=["Finance"]),
        make_doc(document_id="DOC-302", title="Q4 Forecast", version="2.0",
                 effective_date="2026-09-01", content="Q4 projected revenue is 125 crore.",
                 allowed_departments=["Finance"], allowed_roles=["Finance"]),
    ]
    tool = DocumentSearchTool(user, docs, TODAY)

    result = tool.run("latest Q4 forecast")

    assert "125 crore" in result
    assert "DOC-302" in result
    assert "superseded" in result.lower()
