import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { usePendingApprovalCount } from "./usePendingApprovalCount";

vi.mock("./api/client", () => ({
  fetchPendingApprovals: vi.fn(),
}));

import { fetchPendingApprovals } from "./api/client";

describe("usePendingApprovalCount", () => {
  beforeEach(() => {
    vi.mocked(fetchPendingApprovals).mockReset();
  });

  it("returns zero when API is offline", () => {
    const { result } = renderHook(() => usePendingApprovalCount(false));
    expect(result.current).toBe(0);
    expect(fetchPendingApprovals).not.toHaveBeenCalled();
  });

  it("loads pending approval count when API is online", async () => {
    vi.mocked(fetchPendingApprovals).mockResolvedValue([
      { id: "a1", status: "pending" } as never,
      { id: "a2", status: "pending" } as never,
    ]);

    const { result } = renderHook(() => usePendingApprovalCount(true));

    await waitFor(() => {
      expect(result.current).toBe(2);
    });
  });
});
