import { describe, it, expect } from "vitest";
import { experimentNeedsAttention, experimentCardNeedsHighlight } from "./experimentAttention";

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

describe("experimentCardNeedsHighlight", () => {
  it("highlights ruling attention and CAC above break-even", () => {
    expect(experimentCardNeedsHighlight({
      ruling: "continue",
      actual_cac: 30,
      break_even_cac: 20,
    })).toBe(true);
    expect(experimentCardNeedsHighlight({
      ruling: "kill",
      actual_cac: 10,
      break_even_cac: 20,
    })).toBe(true);
    expect(experimentCardNeedsHighlight({
      ruling: "continue",
      actual_cac: 10,
      break_even_cac: 20,
    })).toBe(false);
  });
});
