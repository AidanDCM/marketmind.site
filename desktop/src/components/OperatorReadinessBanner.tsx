import type { OperatorReadiness } from "../api/client";
import { OperatorMessageListItem } from "./OperatorMessageListItem";

interface OperatorReadinessBannerProps {
  readiness: OperatorReadiness;
  onOpenApprovals?: () => void;
  onOpenActive?: (experimentId: string) => void;
  onOpenSnapshots?: (snapshotDate: string, experimentId?: string) => void;
  onOpenLiveData?: () => void;
}

export function OperatorReadinessBanner({
  readiness,
  onOpenApprovals,
  onOpenActive,
  onOpenSnapshots,
  onOpenLiveData,
}: OperatorReadinessBannerProps) {
  const gmail = readiness.gmail as { mode?: string; live_ready?: boolean };
  const commerce = readiness.commerce as {
    stripe?: { configured?: boolean; live_ready?: boolean };
    shopify?: { configured?: boolean; live_ready?: boolean };
  };
  const messageHandlers = { onOpenApprovals, onOpenActive, onOpenSnapshots, onOpenLiveData };

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
            <OperatorMessageListItem key={i} text={item} {...messageHandlers} />
          ))}
        </ul>
      )}
      {readiness.warnings.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
          {readiness.warnings.map((item, i) => (
            <OperatorMessageListItem key={i} text={item} muted {...messageHandlers} />
          ))}
        </ul>
      )}
    </div>
  );
}
