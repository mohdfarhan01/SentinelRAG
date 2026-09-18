"""SentinelRAG GUI -- Streamlit frontend for the FastAPI backend.

Run (with the API already running on port 8000):
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="SentinelRAG", page_icon=":lock:", layout="centered")


def login(username: str, password: str):
    try:
        resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password}, timeout=10)
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API. Is `uvicorn api:app --port 8000` running?")
        return None
    if resp.status_code != 200:
        return None
    return resp.json()


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state['token']}"}


def render_login() -> None:
    st.title(":lock: SentinelRAG")
    st.caption("Secure enterprise research agent")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        result = login(username, password)
        if result is None:
            st.error("Invalid username or password")
        else:
            st.session_state["token"] = result["access_token"]
            st.session_state["user"] = result["user"]
            st.rerun()


def render_sidebar() -> None:
    user = st.session_state["user"]
    st.sidebar.markdown(f"**{user['username']}**")
    st.sidebar.write(f"Role: {user['role']}")
    st.sidebar.write(f"Department: {user['department']}")
    st.sidebar.write(f"Clearance: {user['clearance']}")
    if user["is_admin"]:
        st.sidebar.success("Admin")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()


def render_chat() -> None:
    st.header("Ask the enterprise knowledge base")
    question = st.text_input("Your question", key="question_input")
    if st.button("Ask") and question:
        resp = requests.post(f"{API_BASE}/query", json={"question": question}, headers=auth_headers(), timeout=30)
        if resp.status_code != 200:
            st.error(f"Error: {resp.text}")
            return
        result = resp.json()

        stats = result["evidence_firewall"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Retrieved", stats["retrieved"])
        col2.metric("Authorized", stats["authorized"])
        col3.metric("Blocked", stats["blocked"])

        st.subheader("Answer")
        st.write(result["answer"])

        if result["citations"]:
            st.subheader("Citations")
            for c in result["citations"]:
                st.write(f"- {c['document_id']} — {c['title']} v{c['version']}")
        else:
            st.caption("No citations -- no authorized evidence was used.")

        if result.get("conflicts"):
            st.warning(f"Unresolved conflicts flagged for: {', '.join(result['conflicts'])}")


def render_admin_upload() -> None:
    st.header("Admin: Upload Document")
    st.caption(
        "Classification and access rules are set here explicitly -- they are "
        "never inferred from the document's content."
    )

    mode = st.radio("Type", ["New document", "New version of an existing title"])
    title = st.text_input("Title")
    classification = st.selectbox("Classification", ["Public", "Internal", "Confidential", "Restricted"])
    allowed_departments = st.text_input("Allowed departments (comma-separated)")
    allowed_roles = st.text_input("Allowed roles (comma-separated)")
    effective_date = st.date_input("Effective date")

    version = None
    if mode == "New version of an existing title":
        version = st.text_input("Version (leave blank to auto-increment)") or None

    source = st.radio("Content source", ["Upload file (.txt, .md, .pdf, .docx)", "Paste text"])
    file = None
    text_content = None
    if source.startswith("Upload"):
        file = st.file_uploader("File", type=["txt", "md", "pdf", "docx"])
    else:
        text_content = st.text_area("Document text")

    if st.button("Upload"):
        if not title or not allowed_departments or not allowed_roles:
            st.error("Title, allowed departments, and allowed roles are required.")
            return

        data = {
            "title": title,
            "classification": classification,
            "allowed_departments": allowed_departments,
            "allowed_roles": allowed_roles,
            "effective_date": str(effective_date),
        }
        if version:
            data["version"] = version

        files = None
        if file is not None:
            files = {"file": (file.name, file.getvalue())}
        elif text_content:
            data["text_content"] = text_content
        else:
            st.error("Provide a file or paste text.")
            return

        resp = requests.post(f"{API_BASE}/documents", data=data, files=files, headers=auth_headers(), timeout=60)
        if resp.status_code == 200:
            st.success(f"Uploaded: {resp.json()}")
        else:
            st.error(f"Error: {resp.text}")

    st.divider()
    st.subheader("Existing documents")
    resp = requests.get(f"{API_BASE}/documents", headers=auth_headers(), timeout=10)
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Error loading documents: {resp.text}")


def main() -> None:
    if "token" not in st.session_state:
        render_login()
        return

    render_sidebar()
    user = st.session_state["user"]

    if user["is_admin"]:
        tab_chat, tab_admin = st.tabs(["Chat", "Admin Upload"])
        with tab_chat:
            render_chat()
        with tab_admin:
            render_admin_upload()
    else:
        render_chat()


if __name__ == "__main__":
    main()
