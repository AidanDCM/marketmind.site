import type { OperatorReadiness } from "../api/client";

interface OperatorReadinessBannerProps {
  readiness: OperatorReadiness;
}

export function OperatorReadinessBanner({ readiness }: OperatorReadinessBannerProps) {
  const gmail = readiness.gmail as { mode?: string; live_ready?: boolean };
  const commerce = readiness.commerce as {
    stripe?: { configured?: boolean; live_ready?: boolean };
    shopify?: { configured?: boolean; live_ready?: boolean };
  };

  return (
    <div
      className={`alert ${readiness.ready ? "alert-ok" : "alert-error"}`}
      style={{ marginBottom: 14 }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>
        Operator readiness: {readiness.ready ? "ready" : "not ready"}
      </div>
      <div style={{ fontSize: 13, marginBottom: readiness.blockers.length || readiness.warnings.length ? 8 : 0 }}>
        Gmail {gmail.mode ?? "unknown"}
        {gmail.live_ready ? " · live-ready" : ""}
        {" · "}
        Stripe {commerce.stripe?.configured ? "configured" : "missing"}
        {" · "}
        Shopify {commerce.shopify?.configured ? "configured" : "missing"}
      </div>
      {readiness.blockers.length > 0 && (
        <ul style={{ margin: "0 0 6px", paddingLeft: 18, fontSize: 13 }}>
          {readiness.blockers.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      )}
      {readiness.warnings.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--text-muted)" }}>
          {readiness.warnings.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
