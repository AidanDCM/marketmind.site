import type { OperatorReadiness } from "../api/client";
import {
  parseReadinessBannerAction,
  readinessBannerActionLabel,
  type ReadinessBannerAction,
} from "../readinessBannerActions";

interface OperatorReadinessBannerProps {
  readiness: OperatorReadiness;
  onOpenApprovals?: () => void;
  onOpenActive?: (experimentId: string) => void;
  onOpenSnapshots?: (snapshotDate: string, experimentId?: string) => void;
}

function runReadinessAction(
  action: ReadinessBannerAction,
  handlers: Pick<
    OperatorReadinessBannerProps,
    "onOpenApprovals" | "onOpenActive" | "onOpenSnapshots"
  >,
): void {
  switch (action.kind) {
    case "approvals":
      handlers.onOpenApprovals?.();
      break;
    case "active":
      handlers.onOpenActive?.(action.experimentId);
      break;
    case "snapshots":
      handlers.onOpenSnapshots?.(action.snapshotDate, action.experimentId);
      break;
  }
}

function ReadinessListItem({
  text,
  muted,
  onOpenApprovals,
  onOpenActive,
  onOpenSnapshots,
}: {
  text: string;
  muted?: boolean;
  onOpenApprovals?: () => void;
  onOpenActive?: (experimentId: string) => void;
  onOpenSnapshots?: (snapshotDate: string, experimentId?: string) => void;
}) {
  const action = parseReadinessBannerAction(text);
  const handlers = { onOpenApprovals, onOpenActive, onOpenSnapshots };
  const canAct = action != null && (
    (action.kind === "approvals" && onOpenApprovals)
    || (action.kind === "active" && onOpenActive)
    || (action.kind === "snapshots" && onOpenSnapshots)
  );

  return (
    <li style={muted ? { color: "var(--text-muted)" } : undefined}>
      {text}
      {canAct && action && (
        <button
          type="button"
          className={`inline-link${muted ? "" : " inline-link-danger"}`}
          style={{ marginLeft: 6, fontSize: 13 }}
          onClick={() => runReadinessAction(action, handlers)}
        >
          {readinessBannerActionLabel(action)}
        </button>
      )}
    </li>
  );
}

export function OperatorReadinessBanner({
  readiness,
  onOpenApprovals,
  onOpenActive,
  onOpenSnapshots,
}: OperatorReadinessBannerProps) {
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
            <ReadinessListItem
              key={i}
              text={item}
              onOpenApprovals={onOpenApprovals}
              onOpenActive={onOpenActive}
              onOpenSnapshots={onOpenSnapshots}
            />
          ))}
        </ul>
      )}
      {readiness.warnings.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
          {readiness.warnings.map((item, i) => (
            <ReadinessListItem
              key={i}
              text={item}
              muted
              onOpenApprovals={onOpenApprovals}
              onOpenActive={onOpenActive}
              onOpenSnapshots={onOpenSnapshots}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
