import {
  parseReadinessBannerAction,
  readinessBannerActionLabel,
  type ReadinessBannerAction,
} from "../readinessBannerActions";

export type OperatorMessageHandlers = {
  onOpenApprovals?: () => void;
  onOpenActive?: (experimentId: string) => void;
  onOpenSnapshots?: (snapshotDate: string, experimentId?: string) => void;
  onOpenLiveData?: () => void;
};

export function runReadinessBannerAction(
  action: ReadinessBannerAction,
  handlers: OperatorMessageHandlers,
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
    case "live":
      handlers.onOpenLiveData?.();
      break;
  }
}

export function OperatorMessageListItem({
  text,
  muted,
  onOpenApprovals,
  onOpenActive,
  onOpenSnapshots,
  onOpenLiveData,
}: {
  text: string;
  muted?: boolean;
} & OperatorMessageHandlers) {
  const action = parseReadinessBannerAction(text);
  const handlers = { onOpenApprovals, onOpenActive, onOpenSnapshots, onOpenLiveData };
  const canAct = action != null && (
    (action.kind === "approvals" && onOpenApprovals)
    || (action.kind === "active" && onOpenActive)
    || (action.kind === "snapshots" && onOpenSnapshots)
    || (action.kind === "live" && onOpenLiveData)
  );

  return (
    <li style={muted ? { color: "var(--text-muted)" } : undefined}>
      {text}
      {canAct && action && (
        <button
          type="button"
          className={`inline-link${muted ? "" : " inline-link-danger"}`}
          style={{ marginLeft: 6, fontSize: 13 }}
          onClick={() => runReadinessBannerAction(action, handlers)}
        >
          {readinessBannerActionLabel(action)}
        </button>
      )}
    </li>
  );
}
