import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { usePendingApprovalSummary } from "./usePendingApprovalSummary";

vi.mock("./api/client", () => ({
  fetchPendingApprovals: vi.fn(),
}));

import { fetchPendingApprovals } from "./api/client";

describe("usePendingApprovalSummary", () => {
  beforeEach(() => {
    vi.mocked(fetchPendingApprovals).mockReset();
  });

  it("returns empty summary when API is offline", () => {
    const { result } = renderHook(() => usePendingApprovalSummary(false));
    expect(result.current).toEqual({ count: 0, firstApprovalId: null });
    expect(fetchPendingApprovals).not.toHaveBeenCalled();
  });

  it("loads count and first approval id when API is online", async () => {
    vi.mocked(fetchPendingApprovals).mockResolvedValue([
      { approval_id: "a1", status: "pending" } as never,
      { approval_id: "a2", status: "pending" } as never,
    ]);

    const { result } = renderHook(() => usePendingApprovalSummary(true));

    await waitFor(() => {
      expect(result.current).toEqual({ count: 2, firstApprovalId: "a1" });
    });
  });

  it("refetches when refresh token changes", async () => {
    vi.mocked(fetchPendingApprovals)
      .mockResolvedValueOnce([{ approval_id: "a1", status: "pending" } as never])
      .mockResolvedValueOnce([]);

    const { result, rerender } = renderHook(
      ({ token }) => usePendingApprovalSummary(true, token),
      { initialProps: { token: 0 } },
    );

    await waitFor(() => expect(result.current.count).toBe(1));
    rerender({ token: 1 });
    await waitFor(() => expect(result.current).toEqual({ count: 0, firstApprovalId: null }));
  });
});
