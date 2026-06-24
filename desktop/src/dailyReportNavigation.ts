export type ExperimentProductLookup = {
  experiment_id: string;
  product_name: string;
};

export function parseDailyReportProductPrefix(text: string): string | null {
  const idx = text.indexOf(": ");
  if (idx <= 0) {
    return null;
  }
  const prefix = text.slice(0, idx).trim();
  return prefix || null;
}

export function buildExperimentProductLookup(
  sources: ExperimentProductLookup[][],
): Map<string, string> {
  const lookup = new Map<string, string>();
  for (const list of sources) {
    for (const item of list) {
      lookup.set(item.product_name.toLowerCase(), item.experiment_id);
    }
  }
  return lookup;
}

export function resolveExperimentIdForReportLine(
  text: string,
  lookup: Map<string, string>,
): string | undefined {
  const productName = parseDailyReportProductPrefix(text);
  if (!productName) {
    return undefined;
  }
  return lookup.get(productName.toLowerCase());
}

export const SCALE_APPROVAL_PHRASE = "submit scale request for approval";

export type DailyReportLineAction =
  | { kind: "experiment"; experimentId: string }
  | { kind: "approvals" };

export function isScaleApprovalRecommendation(text: string): boolean {
  return text.toLowerCase().includes(SCALE_APPROVAL_PHRASE);
}

export function resolveDailyReportLineAction(
  text: string,
  lookup: Map<string, string>,
): DailyReportLineAction | null {
  const experimentId = resolveExperimentIdForReportLine(text, lookup);
  if (!experimentId) {
    return null;
  }
  if (isScaleApprovalRecommendation(text)) {
    return { kind: "approvals" };
  }
  return { kind: "experiment", experimentId };
}

export function dailyReportLineActionLabel(action: DailyReportLineAction): string {
  return action.kind === "approvals" ? "Open queue" : "View experiment";
}

export type DailyReportLessonAction =
  | { kind: "approvals" }
  | { kind: "live" };

const PENDING_APPROVALS_LESSON =
  /^(\d+) approval\(s\) pending — unblocking these may unlock next steps\.$/;
const NO_ORDERS_LESSON_PREFIX =
  "No orders: verify that the payment link / checkout is live and working.";

export function resolveDailyReportLessonAction(text: string): DailyReportLessonAction | null {
  if (PENDING_APPROVALS_LESSON.test(text)) {
    return { kind: "approvals" };
  }
  if (text === NO_ORDERS_LESSON_PREFIX) {
    return { kind: "live" };
  }
  return null;
}

export function dailyReportLessonActionLabel(action: DailyReportLessonAction): string {
  return action.kind === "approvals" ? "Open queue" : "Check Live Data";
}
