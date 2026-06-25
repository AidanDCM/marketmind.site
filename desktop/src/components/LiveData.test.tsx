import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LiveData } from "./LiveData";

vi.mock("../api/client", () => ({
  listImportHistory: vi.fn().mockResolvedValue([]),
  pullAndSaveStripeOrders: vi.fn(),
  pullAndSaveShopifyOrders: vi.fn(),
  pullAndSaveShopifyProducts: vi.fn(),
  fetchOrderLifecycle: vi.fn().mockResolvedValue({ orders: [] }),
  importAdCsv: vi.fn(),
  fetchAdSpendSummary: vi.fn().mockResolvedValue({ has_data: false, summary: null }),
}));

import {
  pullAndSaveStripeOrders,
  listImportHistory,
  fetchOrderLifecycle,
  fetchAdSpendSummary,
} from "../api/client";

describe("LiveData commerce wiring", () => {
  beforeEach(() => {
    vi.mocked(pullAndSaveStripeOrders).mockReset();
    vi.mocked(pullAndSaveStripeOrders).mockResolvedValue({
      batch_id: 1,
      source: "stripe_charges",
      total_rows: 2,
      ok_count: 2,
      review_count: 0,
      ok_rows: [{ data: { id: "ch_1", amount: "59.00" } }],
    });
    vi.mocked(listImportHistory).mockResolvedValue([]);
    vi.mocked(fetchOrderLifecycle).mockResolvedValue({ orders: [] });
    vi.mocked(fetchAdSpendSummary).mockResolvedValue({ has_data: false, summary: null });
  });

  it("pulls Stripe orders when Pull Now is clicked", async () => {
    render(<LiveData />);

    fireEvent.click(screen.getByRole("button", { name: "Pull Now" }));

    await waitFor(() => {
      expect(pullAndSaveStripeOrders).toHaveBeenCalled();
    });
  });
});
