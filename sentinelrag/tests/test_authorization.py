from datetime import date

from sentinel.authorization import AuthorizationGatekeeper
from sentinel.models import Document, User

TODAY = date(2026, 9, 18)


def make_doc(**overrides) -> Document:
    base = dict(
        document_id="DOC-X",
        title="Test Doc",
        classification="Internal",
        content="content",
        version="1.0",
        effective_date="2026-01-01",
        allowed_departments=[],
        allowed_roles=[],
    )
    base.update(overrides)
    return Document.from_dict(base)


def test_finance_user_allowed_internal_finance_doc():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc(allowed_departments=["Finance"], allowed_roles=["Finance"])
    decision = AuthorizationGatekeeper().check_access(user, doc, TODAY)
    assert decision.allowed


def test_marketing_user_denied_restricted_executive_doc():
    user = User("U205", "Marketing", "Marketing", "Internal")
    doc = make_doc(
        classification="Restricted",
        allowed_departments=["Executive"],
        allowed_roles=["Executive"],
    )
    decision = AuthorizationGatekeeper().check_access(user, doc, TODAY)
    assert not decision.allowed


def test_department_match_alone_is_not_enough_if_clearance_insufficient():
    # Same department/role as required, but clearance too low -- must still deny.
    user = User("U999", "Finance", "Finance", "Public")
    doc = make_doc(
        classification="Confidential",
        allowed_departments=["Finance"],
        allowed_roles=["Finance"],
    )
    decision = AuthorizationGatekeeper().check_access(user, doc, TODAY)
    assert not decision.allowed
    assert "clearance" in decision.reason


def test_future_effective_date_denied():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc(
        allowed_departments=["Finance"],
        allowed_roles=["Finance"],
        effective_date="2099-01-01",
    )
    decision = AuthorizationGatekeeper().check_access(user, doc, TODAY)
    assert not decision.allowed


def test_revoked_document_denied_even_if_otherwise_permitted():
    user = User("U102", "Finance", "Finance", "Internal")
    doc = make_doc(
        allowed_departments=["Finance"],
        allowed_roles=["Finance"],
        status="revoked",
    )
    decision = AuthorizationGatekeeper().check_access(user, doc, TODAY)
    assert not decision.allowed


def test_no_acl_restrictions_means_open_within_classification():
    user = User("U400", "Anything", "Anything", "Public")
    doc = make_doc(classification="Public", allowed_departments=[], allowed_roles=[])
    decision = AuthorizationGatekeeper().check_access(user, doc, TODAY)
    assert decision.allowed


def test_filter_splits_allowed_and_denied_correctly():
    user = User("U102", "Finance", "Finance", "Internal")
    allowed_doc = make_doc(document_id="DOC-A", allowed_departments=["Finance"], allowed_roles=["Finance"])
    denied_doc = make_doc(document_id="DOC-B", classification="Restricted", allowed_departments=["Executive"])
    allowed_docs, decisions = AuthorizationGatekeeper().filter(user, [allowed_doc, denied_doc], TODAY)

    assert [d.document_id for d in allowed_docs] == ["DOC-A"]
    assert len(decisions) == 2
