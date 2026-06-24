import { describe, it, expect } from "vitest";
import {
  LOOKBACK_DAY_OPTIONS,
  DEFAULT_LOOKBACK_DAYS,
  isLookbackDayOption,
} from "../lookbackOptions";

describe("lookbackOptions", () => {
  it("includes 60 and 90 day windows", () => {
    expect(LOOKBACK_DAY_OPTIONS).toEqual([7, 14, 30, 60, 90]);
  });

  it("defaults to 14 days", () => {
    expect(DEFAULT_LOOKBACK_DAYS).toBe(14);
  });

  it("validates supported lookback values", () => {
    expect(isLookbackDayOption(60)).toBe(true);
    expect(isLookbackDayOption(91)).toBe(false);
  });
});
