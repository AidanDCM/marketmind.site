export type PreflightSummaryAction = "approvals" | "attention";

export function preflightSummaryActions(input: {
  safeToOperate: boolean;
  pendingApprovals: number;
  experimentsNeedingAttention: number;
}): PreflightSummaryAction[] {
  if (input.safeToOperate) {
    return [];
  }
  const actions: PreflightSummaryAction[] = [];
  if (input.pendingApprovals > 0) {
    actions.push("approvals");
  }
  if (input.experimentsNeedingAttention > 0) {
    actions.push("attention");
  }
  return actions;
}

export function preflightSummaryActionLabel(action: PreflightSummaryAction): string {
  return action === "approvals" ? "Open queue" : "Show attention";
}
