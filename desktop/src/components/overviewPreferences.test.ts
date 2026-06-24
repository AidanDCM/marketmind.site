import { describe, it, expect, beforeEach } from "vitest";
import {
  readTrendDaysPreference,
  TREND_DAYS_KEY,
  TREND_DAY_OPTIONS,
  isSnapshotStale,
} from "./overviewPreferences";

describe("overviewPreferences", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("defaults trend lookback to 14 days", () => {
    expect(readTrendDaysPreference()).toBe(14);
  });

  it("reads saved trend lookback when valid", () => {
    localStorage.setItem(TREND_DAYS_KEY, "60");
    expect(readTrendDaysPreference()).toBe(60);
    expect(TREND_DAY_OPTIONS).toContain(60);
  });

  it("flags snapshot stale when before as-of date", () => {
    expect(isSnapshotStale("2026-06-20", "2026-06-23")).toBe(true);
    expect(isSnapshotStale("2026-06-23", "2026-06-23")).toBe(false);
    expect(isSnapshotStale(null, "2026-06-23")).toBe(false);
  });
});
