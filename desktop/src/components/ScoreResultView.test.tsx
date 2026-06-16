import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreResultView } from "./ScoreResultView";
import type { ScoreResult } from "../api/client";

const result: ScoreResult = {
  name: "Test Kit",
  overall_score: 0.72,
  verdict: "pass",
  confidence: 0.68,
  criteria: [{ name: "margin", raw: 1.0, weight: 0.22, reason: "gross margin ~71%" }],
  risks: ["insufficient_evidence"],
  reason_summary: "Pass: clears the bar.",
  channel: {
    channel: "stripe_payment_link",
    strategy: "storefront_first",
    confidence: 0.66,
    reason: "Validate demand first.",
  },
};

describe("ScoreResultView", () => {
  it("renders the verdict, name, and reason", () => {
    render(<ScoreResultView result={result} />);
    expect(screen.getByText("PASS")).toBeInTheDocument();
    expect(screen.getByText(/Test Kit/)).toBeInTheDocument();
    expect(screen.getByText(/clears the bar/)).toBeInTheDocument();
  });

  it("renders criterion rows and risks", () => {
    render(<ScoreResultView result={result} />);
    expect(screen.getByText("margin")).toBeInTheDocument();
    expect(screen.getByText(/insufficient evidence/)).toBeInTheDocument();
  });

  it("shows the recommended channel when present", () => {
    render(<ScoreResultView result={result} />);
    expect(screen.getByText(/stripe payment link/)).toBeInTheDocument();
  });
});
