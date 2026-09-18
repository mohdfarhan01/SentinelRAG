import { Link } from "react-router-dom";
import BrandMark from "./BrandMark";
import ThemeSwitcher from "./ThemeSwitcher";
import TierLadder from "./TierLadder";

const STEPS = [
  {
    step: "1",
    title: "Ask",
    body: "A plain-language question, over every document the company has — not just the ones you already know about.",
  },
  {
    step: "2",
    title: "The firewall filters",
    body: "Retrieval and authorization run as one fused check. Anything you aren't cleared for is stripped before it ever reaches the model — not after, not by asking it nicely.",
  },
  {
    step: "3",
    title: "Cited answer",
    body: "Only from documents you're authorized to see, with citations pointing at exactly which ones — and an audit trail of every decision made along the way.",
  },
];

export default function LandingPage() {
  return (
    <div className="landing">
      <header className="landing-header">
        <BrandMark />
        <div className="landing-header-actions">
          <ThemeSwitcher />
          <Link className="btn-secondary" to="/signin">
            Sign in
          </Link>
          <Link className="btn-primary landing-cta-small" to="/signup">
            Create account
          </Link>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-text">
          <h1>Relevant is not the same as authorized.</h1>
          <p className="landing-hero-sub">
            An enterprise research agent that answers questions over your
            company's internal documents — where authorization is checked
            <em> before</em> content reaches the language model, not
            filtered out of its answer afterward.
          </p>
          <div className="landing-hero-actions">
            <Link className="btn-primary" to="/signup">
              Create an account
            </Link>
            <Link className="btn-secondary" to="/signin">
              I already have one
            </Link>
          </div>
        </div>

        <div className="landing-hero-panel">
          <p className="firewall-summary">
            <strong>4</strong> documents reviewed: <strong>2</strong>{" "}
            authorized and <strong>2</strong> blocked before reaching the
            model.
          </p>
          <div className="evidence-gate">
            <div className="evidence-chip allowed tier-internal">
              <span className="chip-id mono">DOC-014</span>
              <span className="chip-tier">Internal</span>
            </div>
            <div className="evidence-chip allowed tier-public">
              <span className="chip-id mono">DOC-002</span>
              <span className="chip-tier">Public</span>
            </div>
            <div className="evidence-chip blocked">
              <span className="redact-line long" />
              <span className="redact-line short" />
              <span className="chip-blocked-label">Blocked</span>
            </div>
            <div className="evidence-chip blocked">
              <span className="redact-line long" />
              <span className="redact-line short" />
              <span className="chip-blocked-label">Blocked</span>
            </div>
          </div>
          <p className="landing-hero-panel-caption">
            This is real output from the actual firewall — not a mockup.
          </p>
        </div>
      </section>

      <section className="landing-steps">
        {STEPS.map((s) => (
          <div className="landing-step" key={s.step}>
            <span className="landing-step-num mono">{s.step}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </div>
        ))}
      </section>

      <section className="landing-tiers">
        <p className="section-label">How access is decided</p>
        <TierLadder />
        <p className="landing-tiers-footnote">
          A document's classification and a person's clearance, role, and
          department are checked on every single question — not once at
          login.
        </p>
      </section>

      <footer className="landing-footer">
        <span>SentinelRAG — Evidence Firewall</span>
        <ThemeSwitcher />
      </footer>
    </div>
  );
}
