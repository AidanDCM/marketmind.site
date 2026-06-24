import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RulingBadge } from "./RulingBadge";

describe("RulingBadge", () => {
  it("renders kill ruling in red styling", () => {
    render(<RulingBadge ruling="kill" />);
    expect(screen.getByText("Kill")).toBeInTheDocument();
  });

  it("renders no data badge when ruling is null", () => {
    render(<RulingBadge ruling={null} />);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });
});
