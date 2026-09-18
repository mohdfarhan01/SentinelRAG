from __future__ import annotations

from typing import Optional

from .audit import AuditLog


def build_trace(
    audit: AuditLog, query_id: str, requesting_user_id: str, is_admin: bool
) -> Optional[dict]:
    """Builds the audit trace response for a query, redacted for who is
    asking.

    Admins get the full trace, including which specific documents were
    denied and why. Everyone else gets their own query's trace only, with
    denied documents reduced to an aggregate count -- revealing a blocked
    document's id, title, or denial reason to the requester would itself
    be metadata leakage, exactly what this system exists to prevent.
    `evidence_used` and `agent_tool_calls` are safe to show everyone as-is:
    the former only ever contains documents the requester was already
    authorized to see (the same set shown as citations), and the latter
    was never given per-document detail to begin with.

    Returns None if the query doesn't exist, or if the requester is
    neither its owner nor an admin -- callers should treat that as a 404,
    not distinguish "doesn't exist" from "not yours to see".
    """
    query_info = audit.get_query_info(query_id)
    if not query_info:
        return None
    if not is_admin and query_info["user_id"] != requesting_user_id:
        return None

    decisions = audit.get_decisions(query_id)
    evidence = audit.get_evidence(query_id)
    tool_calls = audit.get_tool_calls(query_id)
    answer_record = audit.get_answer_record(query_id) or {
        "answer": None,
        "retrieved": 0,
        "authorized": 0,
        "blocked": 0,
    }

    decisions_out = decisions if is_admin else [d for d in decisions if d["allowed"]]

    steps = [
        {"stage": "query_received", "detail": query_info["question"]},
        {"stage": "retrieval", "detail": f"{answer_record['retrieved']} candidate document(s) reviewed"},
        {
            "stage": "authorization",
            "detail": f"{answer_record['authorized']} authorized, {answer_record['blocked']} blocked",
        },
    ]
    if tool_calls:
        steps.append(
            {"stage": "agent_search", "detail": f"agent performed {len(tool_calls)} search(es)"}
        )
    steps.append({"stage": "answer_generated", "detail": "grounded in authorized evidence only"})
    steps.append({"stage": "citations_validated", "detail": f"{len(evidence)} citation(s) confirmed"})

    return {
        "query_id": query_id,
        "question": query_info["question"],
        "created_at": query_info["created_at"],
        "answer": answer_record["answer"],
        "evidence_firewall": {
            "retrieved": answer_record["retrieved"],
            "authorized": answer_record["authorized"],
            "blocked": answer_record["blocked"],
        },
        "authorization_decisions": decisions_out,
        "evidence_used": evidence,
        "agent_tool_calls": tool_calls,
        "steps": steps,
        "is_full_trace": is_admin,
    }
