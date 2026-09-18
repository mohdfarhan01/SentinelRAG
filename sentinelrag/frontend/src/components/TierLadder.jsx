const TIERS = [
  {
    tier: "public",
    name: "Public",
    audience: "Everyone in the company",
    example: "Employee handbook — company holiday calendar",
    lock: "open",
  },
  {
    tier: "internal",
    name: "Internal",
    audience: "Your own department or role",
    example: "Engineering release roadmap — Engineering only",
    lock: "half",
  },
  {
    tier: "confidential",
    name: "Confidential",
    audience: "Named departments only",
    example: "Vendor contract terms — Finance, Legal",
    lock: "half",
  },
  {
    tier: "restricted",
    name: "Restricted",
    audience: "Named roles only",
    example: "Board compensation review — Executive role only",
    lock: "closed",
  },
];

const SHACKLE_PATH = {
  open: "M5.5 7V5A2.5 2.5 0 0 1 10 3.3",
  half: "M5.5 7V5A2.5 2.5 0 0 1 10.5 5V6",
  closed: "M5.5 7V5A2.5 2.5 0 0 1 10.5 5V7",
};

function LockGlyph({ state }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className={`lock-glyph lock-${state}`}
    >
      <rect x="3.5" y="7" width="9" height="6.5" rx="1.3" stroke="currentColor" strokeWidth="1.3" />
      <path d={SHACKLE_PATH[state]} stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Four tiers of escalating restriction, rendered so the hierarchy is
 * legible at a glance (widening border weight, progressively-closing
 * lock glyph) rather than implied by reading order in a bulleted list.
 */
export default function TierLadder() {
  return (
    <ol className="tier-ladder">
      {TIERS.map((t) => (
        <li key={t.tier} className={`tier-rung tier-rung-${t.tier}`}>
          <div className="tier-rung-head">
            <span className={`tier-rung-lock tier-${t.tier}`}>
              <LockGlyph state={t.lock} />
            </span>
            <span className="tier-rung-name">{t.name}</span>
          </div>
          <p className="tier-rung-audience">{t.audience}</p>
          <p className="tier-rung-example">{t.example}</p>
        </li>
      ))}
    </ol>
  );
}
