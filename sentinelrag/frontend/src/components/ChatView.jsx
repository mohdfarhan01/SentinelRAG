import { useState } from "react";
import EvidenceFirewall from "./EvidenceFirewall";
import { askQuestion } from "../api";

export default function ChatView({ token }) {
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim() || asking) return;
    setError("");
    setAsking(true);
    const asked = question.trim();
    try {
      const result = await askQuestion(token, asked);
      setEntries((prev) => [{ question: asked, ...result }, ...prev]);
      setQuestion("");
    } catch (err) {
      setError(err.message || "Something went wrong reaching the API.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="main-panel">
      <h1 className="panel-heading">Ask the enterprise knowledge base</h1>
      <p className="panel-subtext">
        Every answer is built only from documents you're authorized to see.
      </p>

      <form className="ask-row" onSubmit={handleAsk}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What is the Q4 revenue forecast?"
          autoFocus
        />
        <button type="submit" disabled={asking}>
          {asking ? "Asking..." : "Ask"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {entries.length === 0 && !error && (
        <p className="empty-note">
          Ask a question to see the evidence firewall in action.
        </p>
      )}

      {entries.map((entry, idx) => (
        <div key={entry.query_id + idx}>
          {idx > 0 && <hr className="history-divider" />}

          <p className="section-label">{entry.question}</p>

          <EvidenceFirewall
            stats={entry.evidence_firewall}
            citations={entry.citations}
          />

          <div className="answer-block">
            <p className="section-label">Answer</p>
            <p
              className={`answer-text ${
                entry.citations.length === 0 ? "refusal" : ""
              }`}
            >
              {entry.answer}
            </p>
            {entry.conflicts && entry.conflicts.length > 0 && (
              <div className="conflict-note">
                Authorized sources disagree on: {entry.conflicts.join(", ")}.
                Both are shown rather than guessed between.
              </div>
            )}
          </div>

          {entry.citations.length > 0 && (
            <div>
              <p className="section-label">Sources</p>
              <ul className="citation-list">
                {entry.citations.map((c) => (
                  <li className="citation-item" key={c.document_id}>
                    <span className="cite-id mono">{c.document_id}</span>
                    <span className="cite-title">{c.title}</span>
                    <span className="cite-version">v{c.version}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
