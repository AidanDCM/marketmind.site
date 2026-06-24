export const ATTENTION_ONLY_KEY = "marketmind_attention_only";
export const TREND_DAYS_KEY = "marketmind_trend_days";
export const TREND_DAY_OPTIONS = [7, 14, 30] as const;

export type TrendDayOption = (typeof TREND_DAY_OPTIONS)[number];

export function readAttentionOnlyPreference(): boolean {
  try {
    return localStorage.getItem(ATTENTION_ONLY_KEY) === "true";
  } catch {
    return false;
  }
}

export function readTrendDaysPreference(): TrendDayOption {
  try {
    const raw = Number(localStorage.getItem(TREND_DAYS_KEY));
    if ((TREND_DAY_OPTIONS as readonly number[]).includes(raw)) {
      return raw as TrendDayOption;
    }
  } catch {
    // ignore storage errors in non-browser contexts
  }
  return 14;
}

export function isSnapshotStale(snapshotDate: string | null, asOf: string): boolean {
  return snapshotDate != null && snapshotDate < asOf;
}
