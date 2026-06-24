import { describe, it, expect } from "vitest";
import { experimentNeedsAttention } from "./experimentAttention";

describe("experimentNeedsAttention", () => {
  it("flags kill, pause, and scale rulings", () => {
    expect(experimentNeedsAttention({ ruling: "kill" })).toBe(true);
    expect(experimentNeedsAttention({ ruling: "pause_ads" })).toBe(true);
    expect(experimentNeedsAttention({ ruling: "scale_requires_approval" })).toBe(true);
  });

  it("ignores continue and missing rulings", () => {
    expect(experimentNeedsAttention({ ruling: "continue" })).toBe(false);
    expect(experimentNeedsAttention({ ruling: null })).toBe(false);
  });
});
