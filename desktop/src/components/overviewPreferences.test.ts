import { describe, it, expect, beforeEach } from "vitest";
import {
  readTrendDaysPreference,
  TREND_DAYS_KEY,
  TREND_DAY_OPTIONS,
  isSnapshotStale,
  isValidOverviewDate,
  readOverviewDatePreference,
  OVERVIEW_DATE_KEY,
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

  it("defaults overview date to today when unset", () => {
    const today = new Date().toISOString().slice(0, 10);
    expect(readOverviewDatePreference()).toBe(today);
  });

  it("reads saved overview date when valid", () => {
    localStorage.setItem(OVERVIEW_DATE_KEY, "2026-06-20");
    expect(readOverviewDatePreference()).toBe("2026-06-20");
  });

  it("rejects future or invalid overview dates", () => {
    expect(isValidOverviewDate("not-a-date")).toBe(false);
    expect(isValidOverviewDate("2026-13-40")).toBe(false);
    const tomorrow = new Date();
    tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
    const future = tomorrow.toISOString().slice(0, 10);
    expect(isValidOverviewDate(future)).toBe(false);
    localStorage.setItem(OVERVIEW_DATE_KEY, future);
    expect(readOverviewDatePreference()).toBe(new Date().toISOString().slice(0, 10));
  });
});
