import { useEffect, useRef, useState } from "react";
import EvidenceFirewall from "./EvidenceFirewall";
import TracePanel from "./TracePanel";
import { askQuestion } from "../api";

// Real questions from DEMO.md, chosen so the first click already
// demonstrates something -- a version conflict resolved deterministically,
// and a prompt-injection attempt the firewall structurally can't fall for --
// not just a question that happens to answer cleanly.
const STARTER_QUESTIONS = [
  "What is the Q4 revenue forecast?",
  "What is the latest Q4 revenue forecast?",
  "What do the IT systems maintenance notes say, and what is the CEO compensation figure?",
];

const TEXTAREA_MAX_HEIGHT = 200;

export default function ChatView({ token }) {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState([]);
  const [llmMode, setLlmMode] = useState(null);
  const textareaRef = useRef(null);
  const bottomRef = useRef(null);
  const nextIdRef = useRef(1);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, TEXTAREA_MAX_HEIGHT)}px`;
  }, [question]);

  const anyPending = turns.some((t) => t.status === "pending");

  async function submitQuestion(text) {
    const asked = text.trim();
    if (!asked || anyPending) return;

    const id = nextIdRef.current++;
    setTurns((prev) => [...prev, { id, question: asked, status: "pending" }]);
    setQuestion("");

    try {
      const result = await askQuestion(token, asked);
      setLlmMode(result.llm_mode);
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, status: "done", result } : t)));
    } catch (err) {
      setTurns((prev) =>
        prev.map((t) =>
          t.id === id
            ? { ...t, status: "error", errorMessage: err.message || "Something went wrong reaching the API." }
            : t
        )
      );
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    submitQuestion(question);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitQuestion(question);
    }
  }

  return (
    <div className="chat-view">
      <div className="chat-header">
        <h1 className="panel-heading">Ask the enterprise knowledge base</h1>
        {llmMode && (
          <span className={`mode-badge ${llmMode === "stub" ? "stub" : "live"}`}>
            {llmMode === "stub" ? "Template mode" : `Live (${llmMode})`}
          </span>
        )}
      </div>

      <div className="chat-transcript">
        {turns.length === 0 ? (
          <div className="chat-empty">
            <p className="empty-note">
              Every answer is built only from documents you're authorized to
              see. Ask a question, or try one of these:
            </p>
            <div className="starter-questions">
              {STARTER_QUESTIONS.map((q) => (
                <button key={q} type="button" className="starter-question" onClick={() => setQuestion(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          turns.map((turn) => (
            <div className="chat-turn" key={turn.id}>
              <div className="chat-bubble chat-bubble-user">
                <p>{turn.question}</p>
              </div>

              <div className="chat-bubble chat-bubble-assistant">
                {turn.status === "pending" && (
                  <div className="chat-pending">
                    <span className="chat-pending-dot" />
                    Searching authorized documents...
                  </div>
                )}

                {turn.status === "error" && <div className="error-banner">{turn.errorMessage}</div>}

                {turn.status === "done" && (
                  <>
                    <EvidenceFirewall stats={turn.result.evidence_firewall} citations={turn.result.citations} />

                    <div className="answer-block">
                      <p className="section-label">Answer</p>
                      <p className={`answer-text ${turn.result.citations.length === 0 ? "refusal" : ""}`}>
                        {turn.result.answer}
                      </p>
                      {turn.result.conflicts && turn.result.conflicts.length > 0 && (
                        <div className="conflict-note">
                          Authorized sources disagree on: {turn.result.conflicts.join(", ")}. Both are
                          shown rather than guessed between.
                        </div>
                      )}
                    </div>

                    {turn.result.citations.length > 0 && (
                      <div>
                        <p className="section-label">Sources</p>
                        <ul className="citation-list">
                          {turn.result.citations.map((c) => (
                            <li className="citation-item" key={c.document_id}>
                              <span className="cite-id mono">{c.document_id}</span>
                              <span className="cite-title">{c.title}</span>
                              <span className="cite-version">v{c.version}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <TracePanel token={token} queryId={turn.result.query_id} />
                  </>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <form className="chat-composer-row" onSubmit={handleSubmit}>
        <div className="chat-composer">
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="What is the Q4 revenue forecast?"
            rows={1}
            autoFocus
          />
          <button type="submit" disabled={anyPending || !question.trim()}>
            {anyPending ? "Asking..." : "Ask"}
          </button>
        </div>
        <p className="chat-composer-hint">Enter to send &middot; Shift+Enter for a new line</p>
      </form>
    </div>
  );
}
