import {
  LOOKBACK_DAY_OPTIONS,
  DEFAULT_LOOKBACK_DAYS,
  isLookbackDayOption,
  type LookbackDayOption,
} from "../lookbackOptions";

export const ATTENTION_ONLY_KEY = "marketmind_attention_only";
export const TREND_DAYS_KEY = "marketmind_trend_days";
export const OVERVIEW_DATE_KEY = "marketmind_overview_date";
export const TREND_DAY_OPTIONS = LOOKBACK_DAY_OPTIONS;

export type TrendDayOption = LookbackDayOption;

export function readAttentionOnlyPreference(): boolean {
  try {
    return localStorage.getItem(ATTENTION_ONLY_KEY) === "true";
  } catch {
    return false;
  }
}

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

export function isValidOverviewDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    return false;
  }
  return value <= todayStr();
}

export function readOverviewDatePreference(): string {
  try {
    const raw = localStorage.getItem(OVERVIEW_DATE_KEY);
    if (raw && isValidOverviewDate(raw)) {
      return raw;
    }
  } catch {
    // ignore storage errors in non-browser contexts
  }
  return todayStr();
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
