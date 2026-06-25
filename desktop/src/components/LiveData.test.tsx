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
  pullAndSaveShopifyOrders,
  listImportHistory,
  fetchOrderLifecycle,
  fetchAdSpendSummary,
  importAdCsv,
} from "../api/client";

describe("LiveData commerce wiring", () => {
  beforeEach(() => {
    vi.mocked(pullAndSaveStripeOrders).mockReset();
    vi.mocked(pullAndSaveShopifyOrders).mockReset();
    vi.mocked(pullAndSaveStripeOrders).mockResolvedValue({
      batch_id: 1,
      source: "stripe_charges",
      total_rows: 2,
      ok_count: 2,
      review_count: 0,
      ok_rows: [{ data: { id: "ch_1", amount: "59.00" } }],
    });
    vi.mocked(pullAndSaveShopifyOrders).mockResolvedValue({
      batch_id: 3,
      source: "shopify_orders",
      total_rows: 1,
      ok_count: 1,
      review_count: 0,
      ok_rows: [{ data: { id: "ord_1", total_price: "59.00" } }],
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

  it("pulls Shopify orders when Shopify Orders tab is active", async () => {
    render(<LiveData />);

    fireEvent.click(screen.getByRole("button", { name: "Shopify Orders" }));
    fireEvent.click(screen.getByRole("button", { name: "Pull Now" }));

    await waitFor(() => {
      expect(pullAndSaveShopifyOrders).toHaveBeenCalled();
      expect(pullAndSaveStripeOrders).not.toHaveBeenCalled();
    });
  });

  it("imports ad CSV when Import CSV is clicked", async () => {
    vi.mocked(importAdCsv).mockResolvedValue({
      batch_id: 2,
      source: "ad_report_csv",
      total_rows: 1,
      ok_count: 1,
      review_count: 0,
      ok_rows: [],
    });
    render(<LiveData />);

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "campaign_name,spend\nWidget,25.00" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Import CSV" }));

    await waitFor(() => {
      expect(importAdCsv).toHaveBeenCalledWith(
        "campaign_name,spend\nWidget,25.00",
      );
    });
  });
});
