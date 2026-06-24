import {
  LOOKBACK_DAY_OPTIONS,
  DEFAULT_LOOKBACK_DAYS,
  isLookbackDayOption,
  type LookbackDayOption,
} from "../lookbackOptions";

export const ATTENTION_ONLY_KEY = "marketmind_attention_only";
export const TREND_DAYS_KEY = "marketmind_trend_days";
export const TREND_DAY_OPTIONS = LOOKBACK_DAY_OPTIONS;

export type TrendDayOption = LookbackDayOption;

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
    if (isLookbackDayOption(raw)) {
      return raw;
    }
  } catch {
    // ignore storage errors in non-browser contexts
  }
  return DEFAULT_LOOKBACK_DAYS;
}

export function isSnapshotStale(snapshotDate: string | null, asOf: string): boolean {
  return snapshotDate != null && snapshotDate < asOf;
}
