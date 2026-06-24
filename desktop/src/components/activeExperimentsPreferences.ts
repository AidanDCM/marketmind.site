export const ACTIVE_ATTENTION_ONLY_KEY = "marketmind_active_attention_only";
export const ACTIVE_STATUS_FILTER_KEY = "marketmind_active_status_filter";

export const ACTIVE_STATUS_FILTERS = ["all", "active", "ended"] as const;
export type ActiveStatusFilter = (typeof ACTIVE_STATUS_FILTERS)[number];

export function isActiveStatusFilter(value: string): value is ActiveStatusFilter {
  return (ACTIVE_STATUS_FILTERS as readonly string[]).includes(value);
}

export function readActiveAttentionOnlyPreference(): boolean {
  try {
    return localStorage.getItem(ACTIVE_ATTENTION_ONLY_KEY) === "true";
  } catch {
    return false;
  }
}

export function writeActiveAttentionOnlyPreference(value: boolean): void {
  try {
    localStorage.setItem(ACTIVE_ATTENTION_ONLY_KEY, value ? "true" : "false");
  } catch {
    // ignore storage errors in non-browser contexts
  }
}

export function readActiveStatusFilterPreference(): ActiveStatusFilter {
  try {
    const raw = localStorage.getItem(ACTIVE_STATUS_FILTER_KEY);
    if (raw && isActiveStatusFilter(raw)) {
      return raw;
    }
  } catch {
    // ignore storage errors in non-browser contexts
  }
  return "active";
}

export function writeActiveStatusFilterPreference(value: ActiveStatusFilter): void {
  try {
    localStorage.setItem(ACTIVE_STATUS_FILTER_KEY, value);
  } catch {
    // ignore storage errors in non-browser contexts
  }
}
