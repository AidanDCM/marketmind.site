import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  fetchHealth,
  executeApproved,
  scoreProduct,
  fetchOperatorPreflight,
  fetchExperimentChecklist,
  fetchOperatorMistakes,
  recordMistake,
  fetchExperimentPortfolio,
  importAdCsv,
  fetchAdSpendSummary,
} from "./client";

function mockFetch(value: unknown, ok = true, status = 200) {
  const fn = vi.fn().mockResolvedValue({
    ok,
    status,
    statusText: "Err",
    json: async () => value,
    text: async () => JSON.stringify(value),
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("issues a GET to the right URL", async () => {
    const fn = mockFetch({ status: "ok", version: "0.2.0" });
    const r = await fetchHealth();
    expect(r.status).toBe("ok");
    expect(fn).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/health",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("sends a JSON body on POST", async () => {
    const fn = mockFetch({ verdict: "pass" });
    await scoreProduct({
      product_name: "Kit", est_sale_price: 59, est_product_cost: 12, est_shipping_cost: 5,
      competition: 0.5, return_risk: 0.3, compliance_risk: 0, content_potential: 0.5,
      repeat_purchase_potential: 0.3, personal_fit: 0.5, supplier_reliability: 0.5,
      evidence_quality: 0.3, niche: "",
    });
    const [, opts] = fn.mock.calls[0];
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body).product_name).toBe("Kit");
  });

  it("adds Authorization header when a token is stored", async () => {
    localStorage.setItem("marketmind_api_token", "tok123");
    const fn = mockFetch({});
    await executeApproved("apr_1", true);
    const [, opts] = fn.mock.calls[0];
    expect(opts.headers["Authorization"]).toBe("Bearer tok123");
  });

  it("defaults executeApproved to dry_run true when omitted", async () => {
    const fn = mockFetch({ executed: true, dry_run: true, approval_id: "apr_1", action: "x" });
    await executeApproved("apr_1");
    const [, opts] = fn.mock.calls[0];
    expect(JSON.parse(opts.body).dry_run).toBe(true);
  });

  it("omits Authorization header when no token is stored", async () => {
    const fn = mockFetch({ status: "ok", version: "x" });
    await fetchHealth();
    const [, opts] = fn.mock.calls[0];
    expect(opts.headers["Authorization"]).toBeUndefined();
  });

  it("throws with status + detail on an error response", async () => {
    mockFetch({ detail: "nope" }, false, 409);
    await expect(fetchHealth()).rejects.toThrow("409: nope");
  });

  it("fetches operator preflight from /operator/preflight", async () => {
    const fn = mockFetch({
      safe_to_operate: true,
      pending_approvals: 0,
      experiments_needing_attention: [],
      operator_log_exists: true,
      blockers: [],
      summary: "SAFE: all clear",
    });
    const r = await fetchOperatorPreflight();
    expect(r.safe_to_operate).toBe(true);
    expect(fn).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/operator/preflight",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("fetches experiment checklist from /experiment/{id}/checklist", async () => {
    const fn = mockFetch({
      experiment_id: "exp_001",
      product_name: "Widget",
      ready: false,
      blockers: ["min visits not met"],
      items: [{ item_id: "visits", description: "Min visits", required: true, passed: false, evidence: "50/100" }],
    });
    const r = await fetchExperimentChecklist("exp_001");
    expect(r.ready).toBe(false);
    expect(fn).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/experiment/exp_001/checklist",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("records a mistake via POST /operator/mistakes", async () => {
    const fn = mockFetch({
      recorded: true,
      mistake: {
        mistake_id: "mistake-abc",
        category: "offer_miss",
        experiment_id: "exp_001",
        summary: "Weak headline",
        lesson: "Test benefit-led copy",
        source: "manual",
        created_at: "2026-06-23T00:00:00+00:00",
        tags: [],
      },
    });
    const r = await recordMistake({
      category: "offer_miss",
      experiment_id: "exp_001",
      summary: "Weak headline",
      lesson: "Test benefit-led copy",
    });
    expect(r.recorded).toBe(true);
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/operator/mistakes");
  });

  it("lists operator mistakes", async () => {
    const fn = mockFetch({ count: 1, mistakes: [] });
    await fetchOperatorMistakes({ experimentId: "exp_001", limit: 10 });
    expect(fn.mock.calls[0][0]).toContain("/operator/mistakes?");
    expect(fn.mock.calls[0][0]).toContain("experiment_id=exp_001");
  });

  it("fetches experiment portfolio", async () => {
    const fn = mockFetch({
      total_experiments: 2,
      active: 1,
      ended: 1,
      needs_attention: 0,
      by_ruling: {},
      lessons_recorded: 3,
    });
    const r = await fetchExperimentPortfolio();
    expect(r.total_experiments).toBe(2);
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/experiment/portfolio");
  });

  it("fetches experiment trend summary", async () => {
    const fn = mockFetch({ days: 14, as_of: "2026-06-20", needs_attention_count: 0, experiments: [] });
    const { fetchExperimentTrendSummary } = await import("./client");
    await fetchExperimentTrendSummary(30, "2026-06-20");
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/experiment/trend-summary?days=30&as_of=2026-06-20");
  });

  it("fetches attention-only trend summary", async () => {
    const fn = mockFetch({ days: 14, as_of: "2026-06-20", needs_attention_count: 1, experiments: [] });
    const { fetchExperimentTrendSummary } = await import("./client");
    await fetchExperimentTrendSummary(14, "2026-06-20", true);
    expect(fn.mock.calls[0][0]).toBe(
      "http://127.0.0.1:8000/experiment/trend-summary?days=14&as_of=2026-06-20&attention_only=true",
    );
  });

  it("fetches operator readiness", async () => {
    const fn = mockFetch({
      ready: true,
      blockers: [],
      warnings: [],
      safe_to_operate: true,
      gmail: { mode: "draft_file_only" },
      commerce: { stripe: { configured: false }, shopify: { configured: false } },
      snapshot_gaps: { snapshot_date: "2026-06-23", active_count: 0, missing_count: 0, missing: [], all_recorded: false },
    });
    const { fetchOperatorReadiness } = await import("./client");
    const r = await fetchOperatorReadiness("2026-06-20", true);
    expect(r.ready).toBe(true);
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/operator/readiness?date=2026-06-20&strict=true");
  });

  it("imports ad CSV via POST /imports/ads/csv", async () => {
    const fn = mockFetch({ batch_id: 1, ok_count: 1, review_count: 0, total_rows: 1, ok_rows: [], review_rows: [], source: "ad_report_csv" });
    await importAdCsv("campaign_name,spend\nA,5");
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/imports/ads/csv");
  });

  it("fetches ad spend summary", async () => {
    const fn = mockFetch({ has_data: true, summary: { total_spend: 10, campaigns: 1 } });
    const r = await fetchAdSpendSummary();
    expect(r.has_data).toBe(true);
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/imports/ads/summary");
  });

  it("fetches operator health panel", async () => {
    const fn = mockFetch({
      safe_to_operate: true,
      warnings: [],
      preflight: { safe_to_operate: true, pending_approvals: 0, blockers: [], summary: "SAFE", experiments_needing_attention: [], operator_log_exists: true },
      integrations: { gmail: { mode: "draft_file_only", enabled: false, wired: false, dry_run: true, live_ready: false }, stripe: { configured: false, dry_run: true, live_ready: false }, shopify: { configured: false, read_only: true, live_ready: false }, ad_imports: { csv_available: true, has_latest_batch: false, latest_batch_id: null }, scheduler: { prune_on_cycle: false, prune_apply: false }, live_writes: { enabled: false } },
      portfolio: { total_experiments: 0, active: 0, ended: 0, needs_attention: 0, by_ruling: {}, lessons_recorded: 0 },
      ad_spend: { has_data: false, summary: null },
      checklist: { min_visits: 100, min_orders: 5, min_spend: 50 },
      last_cycle: null,
      snapshot_gaps: { snapshot_date: "2026-06-23", active_count: 0, missing_count: 0, missing: [], all_recorded: false },
    });
    const { fetchOperatorHealthPanel } = await import("./client");
    const r = await fetchOperatorHealthPanel();
    expect(r.safe_to_operate).toBe(true);
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/operator/health-panel");
  });

  it("fetches operator health panel for a date", async () => {
    const fn = mockFetch({
      safe_to_operate: true,
      warnings: [],
      preflight: { safe_to_operate: true, pending_approvals: 0, blockers: [], summary: "SAFE", experiments_needing_attention: [], operator_log_exists: true },
      integrations: { gmail: { mode: "draft_file_only", enabled: false, wired: false, dry_run: true, live_ready: false }, stripe: { configured: false, dry_run: true, live_ready: false }, shopify: { configured: false, read_only: true, live_ready: false }, ad_imports: { csv_available: true, has_latest_batch: false, latest_batch_id: null }, scheduler: { prune_on_cycle: false, prune_apply: false }, live_writes: { enabled: false } },
      portfolio: { total_experiments: 0, active: 0, ended: 0, needs_attention: 0, by_ruling: {}, lessons_recorded: 0 },
      ad_spend: { has_data: false, summary: null },
      checklist: { min_visits: 100, min_orders: 5, min_spend: 50 },
      last_cycle: null,
      snapshot_gaps: { snapshot_date: "2026-06-20", active_count: 0, missing_count: 0, missing: [], all_recorded: false },
    });
    const { fetchOperatorHealthPanel } = await import("./client");
    await fetchOperatorHealthPanel("2026-06-20");
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/operator/health-panel?date=2026-06-20");
  });

  it("runs operator daily cycle via POST", async () => {
    const fn = mockFetch({ date: "2026-06-23", rulings: [], approvals_created: [] });
    const { runOperatorDailyCycle } = await import("./client");
    await runOperatorDailyCycle("2026-06-23");
    expect(fn.mock.calls[0][0]).toBe("http://127.0.0.1:8000/operator/run-cycle?date=2026-06-23");
    expect(fn.mock.calls[0][1].method).toBe("POST");
  });
});
