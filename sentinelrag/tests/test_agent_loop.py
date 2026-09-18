from datetime import date

from sentinel.agent_loop import MAX_TOOL_CALLS, AgentLoop
from sentinel.models import Document, User

TODAY = date(2026, 9, 18)


class FakeLLMClient:
    """Simulates a tool-calling LLM with no network call, so the agent
    loop's own behavior (call cap, response shape, refusal handling) can
    be tested deterministically and offline."""

    def __init__(self, queries_to_issue, final_answer="{evidence}"):
        self.enabled = True
        self.provider = "fake"
        self.queries_to_issue = queries_to_issue
        self._final_answer_template = final_answer
        self.observations = []

    def run_agent_loop(self, system_prompt, user_prompt, tool_schema, tool_callable, tool_fn, max_tool_calls):
        for q in self.queries_to_issue:
            self.observations.append(tool_fn(q))
        return self._final_answer_template.format(evidence="\n".join(self.observations))


def make_doc(**overrides) -> Document:
    base = dict(
        document_id="DOC-101",
        title="Q4 Revenue Forecast",
        classification="Internal",
        content="Q4 projected revenue is 120 crore.",
        version="1.0",
        effective_date="2026-01-01",
        allowed_departments=["Finance"],
        allowed_roles=["Finance"],
    )
    base.update(overrides)
    return Document.from_dict(base)


def test_single_search_produces_grounded_cited_answer():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc()
    fake = FakeLLMClient(
        queries_to_issue=["Q4 revenue forecast"],
        final_answer="The forecast is 120 crore [DOC-101].",
    )
    loop = AgentLoop(fake)

    result = loop.run(user, "What is the Q4 revenue forecast?", [doc], TODAY)

    assert "120 crore" in result["answer"]
    assert any(c["document_id"] == "DOC-101" for c in result["citations"])
    assert result["evidence_firewall"]["authorized"] == 1
    assert len(result["tool_calls"]) == 1


def test_model_can_search_twice_and_both_are_logged():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc()
    fake = FakeLLMClient(
        queries_to_issue=["revenue", "Q4 revenue forecast reformulated"],
        final_answer="Found it [DOC-101].",
    )
    loop = AgentLoop(fake)

    result = loop.run(user, "vague question", [doc], TODAY)

    assert len(result["tool_calls"]) == 2
    assert result["tool_calls"][0]["query"] == "revenue"
    assert result["tool_calls"][1]["query"] == "Q4 revenue forecast reformulated"


def test_call_cap_holds_even_if_fake_model_tries_to_call_more_than_the_max():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc()
    fake = FakeLLMClient(queries_to_issue=["q1", "q2", "q3", "q4", "q5"], final_answer="[DOC-101]")
    loop = AgentLoop(fake)

    result = loop.run(user, "question", [doc], TODAY)

    assert len(result["tool_calls"]) <= MAX_TOOL_CALLS


def test_unauthorized_search_yields_zero_unauthorized_evidence():
    user = User("U205", "Marketing", "Marketing", "Internal")
    doc = make_doc(
        document_id="DOC-201",
        classification="Restricted",
        content="Q4 projected revenue is 145 crore.",
        allowed_departments=["Executive"],
        allowed_roles=["Executive"],
    )
    fake = FakeLLMClient(
        queries_to_issue=["Q4 revenue forecast"],
        final_answer="I don't have enough authorized information to answer that.",
    )
    loop = AgentLoop(fake)

    result = loop.run(user, "What is the Q4 revenue forecast?", [doc], TODAY)

    assert result["citations"] == []
    assert result["evidence_firewall"]["authorized"] == 0
    assert result["evidence_firewall"]["blocked"] == 1
    assert "145" not in result["answer"]
    assert "DOC-201" not in result["answer"]
    # The tool's own observation text -- what the model actually saw --
    # must also contain no unauthorized content, not just the final answer.
    assert all("145" not in obs and "DOC-201" not in obs for obs in fake.observations)


def test_model_that_never_searches_gets_a_refusal_not_an_ungrounded_answer():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc()
    fake = FakeLLMClient(queries_to_issue=[], final_answer="I already know the answer is 120 crore.")
    loop = AgentLoop(fake)

    result = loop.run(user, "What is the Q4 revenue forecast?", [doc], TODAY)

    assert result["citations"] == []
    assert "don't have enough" in result["answer"].lower()
    assert result["tool_calls"] == []


def test_response_shape_matches_deterministic_path():
    """Both the agentic and deterministic paths must return identical
    top-level keys so callers never need to know which one ran."""
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc()
    fake = FakeLLMClient(queries_to_issue=["Q4 revenue"], final_answer="120 crore [DOC-101].")
    loop = AgentLoop(fake)

    result = loop.run(user, "What is the Q4 revenue forecast?", [doc], TODAY)

    expected_keys = {"answer", "citations", "evidence_firewall", "conflicts", "tool_calls", "resolved_documents"}
    assert expected_keys.issubset(result.keys())
    assert isinstance(result["evidence_firewall"]["retrieved"], int)
    assert isinstance(result["evidence_firewall"]["authorized"], int)
    assert isinstance(result["evidence_firewall"]["blocked"], int)
