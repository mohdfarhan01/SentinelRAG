import { tierSlug } from "../api";

/**
 * The one bold element in this UI. Every document the retriever looked at
 * gets a chip in the same row -- the ones the requester is authorized to
 * see render clean and tier-colored; the ones that were blocked render as
 * a redacted bar in the exact same slot, with no title, id, or
 * classification revealed. This is "relevant is not the same as
 * authorized" made visible, not just stated in a stat row.
 */
export default function EvidenceFirewall({ stats, citations }) {
  const chips = [];

  citations.forEach((c) => {
    chips.push(
      <div
        key={c.document_id}
        className={`evidence-chip allowed tier-${tierSlug(c.classification)}`}
        title={`${c.title} — authorized (${c.classification})`}
      >
        <span className="chip-id mono">{c.document_id}</span>
        <span className="chip-tier">{c.classification}</span>
      </div>
    );
  });

  for (let i = 0; i < stats.blocked; i++) {
    chips.push(
      <div
        key={`blocked-${i}`}
        className="evidence-chip blocked"
        title="Blocked by the Evidence Firewall -- not shown to you or the model"
      >
        <span className="redact-line long" />
        <span className="redact-line short" />
        <span className="chip-blocked-label">Blocked</span>
      </div>
    );
  }

  return (
    <div className="firewall-block">
      <div className="firewall-summary">
        <strong>{stats.retrieved}</strong> document
        {stats.retrieved === 1 ? "" : "s"} reviewed:{" "}
        <strong>{stats.authorized}</strong> authorized and{" "}
        <strong>{stats.blocked}</strong> blocked before reaching the model.
      </div>
      <div className="evidence-gate">{chips}</div>
    </div>
  );
}
