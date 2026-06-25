// Shared lookback day options for Overview and Trend pages.

export const LOOKBACK_DAY_OPTIONS = [7, 14, 30, 60, 90] as const;

export type LookbackDayOption = (typeof LOOKBACK_DAY_OPTIONS)[number];

export const DEFAULT_LOOKBACK_DAYS: LookbackDayOption = 14;

export function isLookbackDayOption(value: number): value is LookbackDayOption {
  return (LOOKBACK_DAY_OPTIONS as readonly number[]).includes(value);
}
