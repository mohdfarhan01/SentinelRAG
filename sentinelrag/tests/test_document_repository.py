from sentinel.document_repository import DocumentRepository


def build_repo() -> DocumentRepository:
    return DocumentRepository(":memory:")


def test_add_and_retrieve_document():
    repo = build_repo()
    doc = repo.add_document(
        title="HR Leave Policy",
        classification="Internal",
        content="Employees get 20 days of paid leave per year.",
        allowed_departments=["HR"],
        allowed_roles=["HR"],
        effective_date="2026-01-01",
        uploaded_by="UADMIN",
    )
    all_docs = repo.all()
    assert len(all_docs) == 1
    assert all_docs[0].document_id == doc.document_id
    assert all_docs[0].allowed_departments == ["HR"]
    assert all_docs[0].version == "1.0"


def test_next_version_auto_increments():
    repo = build_repo()
    repo.add_document(
        title="Q4 Forecast", classification="Internal", content="v1 content",
        allowed_departments=["Finance"], allowed_roles=["Finance"],
        effective_date="2026-06-01", uploaded_by="UADMIN",
    )
    assert repo.next_version("Q4 Forecast") == "2.0"

    repo.add_document(
        title="Q4 Forecast", classification="Internal", content="v2 content",
        allowed_departments=["Finance"], allowed_roles=["Finance"],
        effective_date="2026-09-01", uploaded_by="UADMIN",
    )
    versions = sorted(d.version for d in repo.all() if d.title == "Q4 Forecast")
    assert versions == ["1.0", "2.0"]


def test_revoke_marks_document_inactive():
    repo = build_repo()
    doc = repo.add_document(
        title="Old Policy", classification="Internal", content="outdated",
        allowed_departments=["HR"], allowed_roles=["HR"],
        effective_date="2020-01-01", uploaded_by="UADMIN",
    )
    repo.revoke(doc.document_id)
    reloaded = next(d for d in repo.all() if d.document_id == doc.document_id)
    assert reloaded.status == "revoked"


def test_list_metadata_excludes_content():
    repo = build_repo()
    repo.add_document(
        title="Secret Plan", classification="Restricted", content="the actual secret content",
        allowed_departments=["Executive"], allowed_roles=["Executive"],
        effective_date="2026-01-01", uploaded_by="UADMIN",
    )
    rows = repo.list_metadata()
    assert len(rows) == 1
    assert "content" not in rows[0]
    assert rows[0]["title"] == "Secret Plan"
