import { useEffect, useState } from "react";
import { listDocuments, tierSlug, uploadDocument } from "../api";

const CLASSIFICATIONS = ["Public", "Internal", "Confidential", "Restricted"];

export default function AdminUpload({ token }) {
  const [mode, setMode] = useState("new");
  const [title, setTitle] = useState("");
  const [classification, setClassification] = useState("Internal");
  const [allowedDepartments, setAllowedDepartments] = useState("");
  const [allowedRoles, setAllowedRoles] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [version, setVersion] = useState("");
  const [contentSource, setContentSource] = useState("file");
  const [file, setFile] = useState(null);
  const [textContent, setTextContent] = useState("");
  const [status, setStatus] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [docs, setDocs] = useState([]);
  const [docsError, setDocsError] = useState("");

  async function refreshDocs() {
    try {
      const rows = await listDocuments(token);
      setDocs(rows);
      setDocsError("");
    } catch (err) {
      setDocsError(err.message || "Could not load documents.");
    }
  }

  useEffect(() => {
    refreshDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus(null);

    if (!title.trim()) {
      setStatus({ ok: false, message: "Title is required." });
      return;
    }
    if (contentSource === "file" && !file) {
      setStatus({ ok: false, message: "Choose a file to upload." });
      return;
    }
    if (contentSource === "text" && !textContent.trim()) {
      setStatus({ ok: false, message: "Paste some text, or switch to file upload." });
      return;
    }

    setSubmitting(true);
    try {
      const fields = {
        title: title.trim(),
        classification,
        allowed_departments: allowedDepartments.trim(),
        allowed_roles: allowedRoles.trim(),
        effective_date: effectiveDate || new Date().toISOString().slice(0, 10),
      };
      if (mode === "version" && version.trim()) fields.version = version.trim();
      if (contentSource === "text") fields.text_content = textContent;

      const result = await uploadDocument(token, fields, contentSource === "file" ? file : null);
      setStatus({
        ok: true,
        message: `Uploaded as ${result.document_id} (version ${result.version}).`,
      });
      setTitle("");
      setAllowedDepartments("");
      setAllowedRoles("");
      setVersion("");
      setFile(null);
      setTextContent("");
      refreshDocs();
    } catch (err) {
      setStatus({ ok: false, message: err.message || "Upload failed." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="main-panel">
      <h1 className="panel-heading">Upload a document</h1>
      <p className="panel-subtext">
        Classification and access rules are set here, by hand. They are
        never guessed from the file's content.
      </p>

      <form className="upload-form" onSubmit={handleSubmit}>
        <section className="form-section">
          <p className="form-section-title">Identity</p>
          <div className="radio-group">
            <label className="radio-option">
              <input
                type="radio"
                checked={mode === "new"}
                onChange={() => setMode("new")}
              />
              New document
            </label>
            <label className="radio-option">
              <input
                type="radio"
                checked={mode === "version"}
                onChange={() => setMode("version")}
              />
              New version of an existing title
            </label>
          </div>

          <div className="field">
            <label htmlFor="title">Title</label>
            <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>

          {mode === "version" && (
            <div className="field">
              <label htmlFor="version">Version</label>
              <input
                id="version"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="Leave blank to auto-increment"
              />
            </div>
          )}
        </section>

        <section className="form-section">
          <p className="form-section-title">Classification &amp; access</p>
          <div className="field-row">
            <div className="field">
              <label htmlFor="classification">Classification</label>
              <select
                id="classification"
                value={classification}
                onChange={(e) => setClassification(e.target.value)}
              >
                {CLASSIFICATIONS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="effective-date">Effective date</label>
              <input
                id="effective-date"
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
              />
            </div>
          </div>

          <div className="field-row">
            <div className="field">
              <label htmlFor="departments">Allowed departments</label>
              <input
                id="departments"
                value={allowedDepartments}
                onChange={(e) => setAllowedDepartments(e.target.value)}
                placeholder="Finance, Executive"
              />
            </div>
            <div className="field">
              <label htmlFor="roles">Allowed roles</label>
              <input
                id="roles"
                value={allowedRoles}
                onChange={(e) => setAllowedRoles(e.target.value)}
                placeholder="Finance, Executive"
              />
            </div>
          </div>
          <p className="help-text">
            Leave either blank to mean "no restriction on that axis." Comma-separated.
          </p>
        </section>

        <section className="form-section">
          <p className="form-section-title">Content</p>
          <div className="radio-group">
            <label className="radio-option">
              <input
                type="radio"
                checked={contentSource === "file"}
                onChange={() => setContentSource("file")}
              />
              Upload a file
            </label>
            <label className="radio-option">
              <input
                type="radio"
                checked={contentSource === "text"}
                onChange={() => setContentSource("text")}
              />
              Paste text
            </label>
          </div>

          {contentSource === "file" ? (
            <div className="field">
              <label htmlFor="file">File (.txt, .md, .pdf, .docx)</label>
              <input
                id="file"
                type="file"
                accept=".txt,.md,.pdf,.docx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>
          ) : (
            <div className="field">
              <label htmlFor="text-content">Document text</label>
              <textarea
                id="text-content"
                rows={5}
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
              />
            </div>
          )}
        </section>

        <button className="btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Uploading..." : "Upload document"}
        </button>

        {status && (
          <div className={`upload-status ${status.ok ? "success" : "error"}`}>
            {status.message}
          </div>
        )}
      </form>

      <p className="section-label">Documents in the system</p>
      {docsError && <div className="error-banner">{docsError}</div>}
      {docs.length === 0 && !docsError ? (
        <p className="empty-note">No documents uploaded yet.</p>
      ) : (
        <table className="doc-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Classification</th>
              <th>Version</th>
              <th>Effective</th>
              <th>Status</th>
              <th>Document ID</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.document_id}>
                <td>{d.title}</td>
                <td>
                  <span className={`tier-tag tier-${tierSlug(d.classification)}`}>
                    {d.classification}
                  </span>
                </td>
                <td className="mono">{d.version}</td>
                <td className="mono">{d.effective_date}</td>
                <td>
                  <span className={`status-tag ${d.status === "revoked" ? "revoked" : ""}`}>
                    {d.status}
                  </span>
                </td>
                <td className="mono">{d.document_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
