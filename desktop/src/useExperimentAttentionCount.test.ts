import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useExperimentAttentionCount } from "./useExperimentAttentionCount";

vi.mock("./api/client", () => ({
  fetchExperimentPortfolio: vi.fn(),
}));

import { fetchExperimentPortfolio } from "./api/client";

describe("useExperimentAttentionCount", () => {
  beforeEach(() => {
    vi.mocked(fetchExperimentPortfolio).mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns zero when API is offline", () => {
    const { result } = renderHook(() => useExperimentAttentionCount(false));
    expect(result.current).toBe(0);
    expect(fetchExperimentPortfolio).not.toHaveBeenCalled();
  });

  it("loads needs_attention from portfolio when API is online", async () => {
    vi.mocked(fetchExperimentPortfolio).mockResolvedValue({
      total_experiments: 2,
      active: 2,
      ended: 0,
      needs_attention: 3,
      by_ruling: {},
      lessons_recorded: 0,
    });

    const { result } = renderHook(() => useExperimentAttentionCount(true));

    await waitFor(() => {
      expect(result.current).toBe(3);
    });
  });
});
