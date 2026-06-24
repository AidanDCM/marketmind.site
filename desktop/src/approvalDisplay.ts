import type { ApprovalRecord } from "./api/client";

export function pendingApprovalBannerText(pending: ApprovalRecord[]): string {
  const count = pending.length;
  if (count === 0) return "";

  const noun = count === 1 ? "approval" : "approvals";
  const first = pending[0];
  const example = first.summary?.trim() || first.action;
  const exampleSuffix = example ? ` — e.g. ${example}` : "";

  return `${count} pending ${noun} require your review${exampleSuffix} — open queue`;
}
