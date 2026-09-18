import { useState } from "react";
import BrandMark from "./BrandMark";
import { login } from "../api";

const TIERS = [
  { name: "Public", tier: "public", note: "Visible to everyone in the company" },
  { name: "Internal", tier: "internal", note: "Visible to your department or role" },
  { name: "Confidential", tier: "confidential", note: "Visible only to named departments" },
  { name: "Restricted", tier: "restricted", note: "Visible only to named roles, such as Executive" },
];

export default function LoginScreen({ onLoggedIn }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await login(username.trim(), password);
      onLoggedIn(result);
    } catch (err) {
      setError("That username or password isn't recognized.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-form-side">
        <div className="login-card">
          <BrandMark />
          <h1>Sign in to your workspace</h1>
          <p className="subtitle">
            Answers are scoped to what your role, department, and clearance
            actually permit.
          </p>

          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                autoComplete="username"
              />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="demo-hint">
            Demo accounts (password <span className="mono">password123</span>):{" "}
            <span className="mono">u102</span> Finance,{" "}
            <span className="mono">u205</span> Marketing,{" "}
            <span className="mono">u301</span> Finance,{" "}
            <span className="mono">admin</span> Admin.
          </div>
        </div>
      </div>

      <div className="login-ledger-side">
        <p className="ledger-eyebrow">How access is decided</p>
        <ul className="ledger-tier-list">
          {TIERS.map((t) => (
            <li key={t.tier} className="ledger-tier-row">
              <span className={`ledger-tier-swatch tier-${t.tier}`} />
              <span className="ledger-tier-text">
                <span className="ledger-tier-name">{t.name}</span>
                <span className="ledger-tier-note">{t.note}</span>
              </span>
            </li>
          ))}
        </ul>
        <p className="ledger-footnote">
          A document's classification and a person's clearance are checked
          before any content reaches the model, not after.
        </p>
      </div>
    </div>
  );
}
