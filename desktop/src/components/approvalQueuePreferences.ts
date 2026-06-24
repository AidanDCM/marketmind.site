export const APPROVAL_FILTER_KEY = "marketmind_approval_filter";

export const APPROVAL_FILTERS = [
  "pending",
  "all",
  "approved",
  "denied",
  "blocked",
  "auto_allowed",
] as const;

export type ApprovalFilter = (typeof APPROVAL_FILTERS)[number];

export function isApprovalFilter(value: string): value is ApprovalFilter {
  return (APPROVAL_FILTERS as readonly string[]).includes(value);
}

export function readApprovalFilterPreference(): ApprovalFilter {
  try {
    const raw = localStorage.getItem(APPROVAL_FILTER_KEY);
    if (raw && isApprovalFilter(raw)) {
      return raw;
    }
  } catch {
    // ignore storage errors in non-browser contexts
  }
  return "pending";
}

export function writeApprovalFilterPreference(value: ApprovalFilter): void {
  try {
    localStorage.setItem(APPROVAL_FILTER_KEY, value);
  } catch {
    // ignore storage errors in non-browser contexts
  }
}
