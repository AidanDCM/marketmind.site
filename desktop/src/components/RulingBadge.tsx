const RULING_COLOR: Record<string, string> = {
  continue: "var(--green)",
  scale_requires_approval: "var(--accent)",
  pause_ads: "var(--yellow, #f5a623)",
  revise_offer: "var(--yellow, #f5a623)",
  kill: "var(--red)",
};

const RULING_LABEL: Record<string, string> = {
  continue: "Continue",
  scale_requires_approval: "Scale (needs approval)",
  pause_ads: "Pause ads",
  revise_offer: "Revise offer",
  kill: "Kill",
};

export function RulingBadge({ ruling }: { ruling: string | null }) {
  if (!ruling) return <span className="badge badge-pending">No data</span>;
  const color = RULING_COLOR[ruling] ?? "var(--text-muted)";
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600,
      background: `${color}22`, color, border: `1px solid ${color}55`,
      whiteSpace: "nowrap",
    }}>
      {RULING_LABEL[ruling] ?? ruling.replace(/_/g, " ")}
    </span>
  );
}
