import { useState } from "react";
import { getAuditTrace } from "../api";

export default function TracePanel({ token, queryId }) {
  const [state, setState] = useState({ status: "collapsed" });

  async function toggle() {
    if (state.status === "ready" || state.status === "error") {
      setState({ status: "collapsed" });
      return;
    }
    setState({ status: "loading" });
    try {
      const data = await getAuditTrace(token, queryId);
      setState({ status: "ready", data });
    } catch (err) {
      setState({ status: "error", message: err.message || "Could not load the trace." });
    }
  }

  return (
    <div className="trace-block">
      <button type="button" className="trace-toggle" onClick={toggle}>
        {state.status === "ready" ? "Hide execution trace" : "Show execution trace"}
      </button>

      {state.status === "loading" && <p className="empty-note">Loading trace...</p>}
      {state.status === "error" && <div className="error-banner">{state.message}</div>}

      {state.status === "ready" && (
        <div className="trace-panel">
          <ol className="trace-steps">
            {state.data.steps.map((step, i) => (
              <li className="trace-step" key={i}>
                <span className="trace-stage">{step.stage.replace(/_/g, " ")}</span>
                <span className="trace-detail">{step.detail}</span>
              </li>
            ))}
          </ol>

          {state.data.agent_tool_calls.length > 0 && (
            <div className="trace-searches">
              <p className="section-label">Agent searches</p>
              <ul className="trace-search-list">
                {state.data.agent_tool_calls.map((call) => (
                  <li key={call.call_index}>
                    <span className="mono trace-search-query">&quot;{call.query}&quot;</span>
                    <span className="trace-search-stats">
                      {call.retrieved} retrieved, {call.authorized} authorized, {call.blocked} blocked
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!state.data.is_full_trace && (
            <p className="trace-footnote">
              Blocked documents are shown here only as a count. An admin view
              would additionally show which specific documents were denied
              and why.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
