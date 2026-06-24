import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { OperatorReadinessBanner } from "./OperatorReadinessBanner";
import type { OperatorReadiness } from "../api/client";

const base: OperatorReadiness = {
  ready: true,
  blockers: [],
  warnings: [],
  safe_to_operate: true,
  gmail: { mode: "simulate", live_ready: false },
  commerce: {
    stripe: { configured: false, live_ready: false },
    shopify: { configured: false, live_ready: false },
  },
  snapshot_gaps: {
    snapshot_date: "2026-06-23",
    active_count: 0,
    missing_count: 0,
    missing: [],
    all_recorded: false,
  },
};

describe("OperatorReadinessBanner", () => {
  it("renders ready state", () => {
    render(<OperatorReadinessBanner readiness={base} />);
    expect(screen.getByText(/Operator readiness: ready/)).toBeInTheDocument();
    expect(screen.getByText(/Gmail simulate/)).toBeInTheDocument();
  });

  it("renders blockers when not ready", () => {
    render(
      <OperatorReadinessBanner
        readiness={{
          ...base,
          ready: false,
          blockers: ["2 pending approval(s) have not been reviewed"],
        }}
      />,
    );
    expect(screen.getByText(/not ready/)).toBeInTheDocument();
    expect(screen.getByText(/pending approval/)).toBeInTheDocument();
  });
});
