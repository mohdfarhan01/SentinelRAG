import { useState } from "react";
import { Link } from "react-router-dom";
import BrandMark from "./BrandMark";
import ThemeSwitcher from "./ThemeSwitcher";
import { login } from "../api";

export default function SignIn({ onLoggedIn }) {
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
    <div className="auth-screen">
      <div className="auth-screen-top">
        <Link to="/" className="auth-brand-link">
          <BrandMark />
        </Link>
        <ThemeSwitcher />
      </div>

      <div className="auth-card-wrap">
        <div className="auth-card">
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

          <p className="auth-switch">
            New here? <Link to="/signup">Create an account</Link>
          </p>

          <div className="demo-hint">
            Demo accounts (password <span className="mono">password123</span>):{" "}
            <span className="mono">u102</span> Finance,{" "}
            <span className="mono">u205</span> Marketing,{" "}
            <span className="mono">u301</span> Finance,{" "}
            <span className="mono">admin</span> Admin.
          </div>
        </div>
      </div>
    </div>
  );
}
