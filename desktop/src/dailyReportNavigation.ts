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
export const NO_EXPERIMENTS_RECOMMENDATION =
  "No experiments active today. Pick a product candidate to test.";
export const POSITIVE_CONTRIBUTION_PREFIX = "Positive contribution today";
export const ZERO_ORDER_SPEND_RISK =
  "Spend with zero orders today — check targeting and offer.";

export type DailyReportLineAction =
  | { kind: "experiment"; experimentId: string }
  | { kind: "approvals" }
  | { kind: "score" }
  | { kind: "activeList" };

export function isGenericPortfolioRisk(text: string): boolean {
  if (text === ZERO_ORDER_SPEND_RISK) {
    return true;
  }
  if (text.startsWith("Refund rate ") && text.includes("review product quality")) {
    return true;
  }
  if (text.startsWith("Add-to-cart rate ") && text.includes("creative or price needs revision")) {
    return true;
  }
  return false;
}

export function isScaleApprovalRecommendation(text: string): boolean {
  return text.toLowerCase().includes(SCALE_APPROVAL_PHRASE);
}

export function resolveDailyReportLineAction(
  text: string,
  lookup: Map<string, string>,
): DailyReportLineAction | null {
  const experimentId = resolveExperimentIdForReportLine(text, lookup);
  if (experimentId) {
    if (isScaleApprovalRecommendation(text)) {
      return { kind: "approvals" };
    }
    return { kind: "experiment", experimentId };
  }
  if (text === NO_EXPERIMENTS_RECOMMENDATION) {
    return { kind: "score" };
  }
  if (text.startsWith(POSITIVE_CONTRIBUTION_PREFIX)) {
    return { kind: "activeList" };
  }
  if (isGenericPortfolioRisk(text)) {
    return { kind: "activeList" };
  }
  return null;
}

export function dailyReportLineActionLabel(action: DailyReportLineAction): string {
  switch (action.kind) {
    case "approvals":
      return "Open queue";
    case "experiment":
      return "View experiment";
    case "score":
      return "Score product";
    case "activeList":
      return "View experiments";
  }
}

export type DailyReportLessonAction =
  | { kind: "approvals" }
  | { kind: "live" }
  | { kind: "lessons" }
  | { kind: "activeList" };

const PENDING_APPROVALS_LESSON =
  /^(\d+) approval\(s\) pending — unblocking these may unlock next steps\.$/;
const NO_ORDERS_LESSON_PREFIX =
  "No orders: verify that the payment link / checkout is live and working.";
const PAST_LESSON_PREFIX = "Past lesson: ";
const ROAS_SCALE_LESSON_PHRASE = "confirm with experiment rules before scaling.";
const LOW_ROAS_LESSON_MARKER = "(below 1.0)";

export function resolveDailyReportLessonAction(text: string): DailyReportLessonAction | null {
  if (PENDING_APPROVALS_LESSON.test(text)) {
    return { kind: "approvals" };
  }
  if (text === NO_ORDERS_LESSON_PREFIX) {
    return { kind: "live" };
  }
  if (text.startsWith(PAST_LESSON_PREFIX)) {
    return { kind: "lessons" };
  }
  if (text.includes(ROAS_SCALE_LESSON_PHRASE)) {
    return { kind: "activeList" };
  }
  if (text.startsWith("ROAS is ") && text.includes(LOW_ROAS_LESSON_MARKER)) {
    return { kind: "activeList" };
  }
  return null;
}

export function dailyReportLessonActionLabel(action: DailyReportLessonAction): string {
  switch (action.kind) {
    case "approvals":
      return "Open queue";
    case "live":
      return "Check Live Data";
    case "lessons":
      return "View library";
    case "activeList":
      return "View experiments";
  }
}
