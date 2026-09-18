import { useState } from "react";
import { Link } from "react-router-dom";
import BrandMark from "./BrandMark";
import ThemeSwitcher from "./ThemeSwitcher";
import { signup } from "../api";

export default function SignUp({ onLoggedIn }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await signup(username.trim(), password);
      onLoggedIn(result);
    } catch (err) {
      setError(err.message || "Couldn't create that account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-screen-top">
        <Link to="/" className="auth-brand-link">
          <BrandMark />
        </Link>
        <ThemeSwitcher />
      </div>

      <div className="auth-card-wrap">
        <div className="auth-card">
          <h1>Create an account</h1>
          <p className="subtitle">
            Start asking questions over the company's documents in under a
            minute.
          </p>

          <div className="clearance-notice">
            <span className="clearance-notice-badge tier-public">Public</span>
            <p>
              New accounts start at <strong>Public</strong> clearance, with
              no department or role restrictions. Elevated access is
              assigned by an administrator afterward — it isn't something
              you choose here. That's not a limitation of this form; it's
              the same rule the whole system enforces on every request.
            </p>
          </div>

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
                autoComplete="new-password"
              />
            </div>
            <div className="field">
              <label htmlFor="confirm-password">Confirm password</label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link to="/signin">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
