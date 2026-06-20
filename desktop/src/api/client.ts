const BASE = "http://127.0.0.1:8000";

// Optional bearer token. When the backend has MARKETMIND_API_TOKEN set, store the
// matching token here (e.g. localStorage "marketmind_api_token") and it is sent
// on every request. Unset for the default open localhost setup.
function authToken(): string | null {
  try {
    return localStorage.getItem("marketmind_api_token");
  } catch {
    return null;
  }
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = authToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail ?? JSON.stringify(j);
    } catch {
      detail = await res.text().catch(() => res.statusText);
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ---- Health ----
export async function fetchHealth(): Promise<{ status: string; version: string }> {
  return req("GET", "/health");
}

// ---- Daily report (matches DailyMetrics / DailyReport.to_dict) ----
export interface DailyMetrics {
  date: string;
  revenue: number;
  orders: number;
  ad_spend: number;
  refund_count: number;
  contribution_profit: number;
  cac: number;
  conversion_rate: number;
  add_to_cart_rate: number;
  refund_rate: number;
}
export interface DailyReport {
  date: string;
  metrics: DailyMetrics;
  pending_approvals: string[];
  recommendations: string[];
  risks: string[];
  lessons: string[];
}

export function fetchDailyReport(date: string): Promise<DailyReport> {
  return req("GET", `/report/daily?date=${date}`);
}

// ---- Approvals (matches ApprovalRecord.to_dict) ----
export interface ApprovalRecord {
  approval_id: string;
  action: string;
  risk_level: string;
  status: string;
  summary: string;
  expected_cost: number;
  rollback_plan: string;
  reason: string;
}

export function fetchApprovals(status?: string): Promise<ApprovalRecord[]> {
  const qs = status ? `?status=${status}` : "";
  return req("GET", `/approvals${qs}`);
}

export function fetchPendingApprovals(): Promise<ApprovalRecord[]> {
  return req("GET", "/approvals/pending");
}

export function approveRecord(id: string, note: string): Promise<ApprovalRecord> {
  return req("POST", `/approvals/${id}/approve`, { note });
}

export function denyRecord(id: string, note: string): Promise<ApprovalRecord> {
  return req("POST", `/approvals/${id}/deny`, { note });
}

// ---- Scoring (matches ScoreResult.to_dict) ----
export interface CriterionScore {
  name: string;
  raw: number;      // 0-1 sub-score
  weight: number;
  reason: string;
}
export interface ChannelRecommendation {
  channel: string;
  strategy: string;
  confidence: number;
  reason: string;
}
export interface ScoreResult {
  name: string;
  overall_score: number;   // 0-1
  verdict: string;         // pass | review | reject
  confidence: number;      // 0-1
  criteria: CriterionScore[];
  risks: string[];
  reason_summary: string;
  channel: ChannelRecommendation | null;
}

export interface ProductInput {
  product_name: string;
  est_sale_price: number;
  est_product_cost: number;
  est_shipping_cost: number;
  competition: number;
  return_risk: number;
  compliance_risk: number;
  content_potential: number;
  repeat_purchase_potential: number;
  personal_fit: number;
  supplier_reliability: number;
  evidence_quality: number;
  niche: string;
}

export function scoreProduct(input: ProductInput): Promise<ScoreResult> {
  return req("POST", "/score/product", input);
}

export interface NicheInput {
  niche_name: string;
  demand: number;
  competition: number;
  margin_potential: number;
  content_potential: number;
  personal_fit: number;
  supplier_availability: number;
  repeat_purchase_potential: number;
  regulatory_risk: number;
  evidence_quality: number;
}

export function scoreNiche(input: NicheInput): Promise<ScoreResult> {
  return req("POST", "/score/niche", input);
}

// ---- Offer spec (matches OfferSpec.to_dict) ----
export interface BundleItem { name: string; description: string }
export interface FaqItem { question: string; answer: string }
export interface AnalyticsEvent { name: string; trigger: string; properties: string[] }
export interface OfferSpec {
  product_name: string;
  headline: string;
  subheadline: string;
  bundle_items: BundleItem[];
  faq: FaqItem[];
  cta_primary: string;
  cta_button_label: string;
  analytics_events: AnalyticsEvent[];
  trust_signals: string[];
  codex_build_notes: string;
  safety_flags: string[];
}
export interface SpecRequest {
  product_name: string;
  sale_price: number;
  key_benefit: string;
  target_customer: string;
  secondary_benefits: string[];
  common_objections: string[];
  shipping_note: string;
  return_policy: string;
  niche: string;
}

export function generateSpec(input: SpecRequest): Promise<OfferSpec> {
  return req("POST", "/spec", input);
}

// ---- Unit economics (matches UnitEconomicsResult.to_dict) ----
export interface EconomicsInput {
  product_name: string;
  sale_price: number;
  product_cost: number;
  packaging_cost: number;
  shipping_cost: number;
  platform_fee: number;
  payment_fee: number;
  refund_allowance: number;
  software_allocation: number;
  estimated_cac: number;
}
export interface EconomicsResult {
  product_name: string;
  sale_price: number;
  total_non_ad_cost: number;
  gross_profit_before_ads: number;
  break_even_cac: number;
  safe_cac_low: number;
  safe_cac_high: number;
  estimated_cac: number;
  estimated_contribution_profit: number;
  gross_margin_before_ads: number;
  contribution_margin_after_ads: number;
  margin_status: string;
  recommended_action: string;
  risks: string[];
  reason_summary: string;
}

export function calculateEconomics(input: EconomicsInput): Promise<EconomicsResult> {
  return req("POST", "/economics", input);
}

// ---- Experiment evaluation (matches ExperimentRulingResult.to_dict) ----
export interface ExperimentInput {
  experiment_id: string;
  product_name: string;
  break_even_cac: number;
  qualified_visits: number;
  orders: number;
  total_ad_spend: number;
  total_revenue: number;
  refund_count: number;
  actual_shipping_cost: number;
  planned_shipping_cost: number;
  add_to_cart_count: number;
  consecutive_losing_periods: number;
  budget_cap: number;
}
export interface ExperimentResult {
  experiment_id: string;
  product_name: string;
  ruling: string;
  risks: string[];
  reason_summary: string;
  requires_approval: boolean;
}

export function evaluateExperiment(input: ExperimentInput): Promise<ExperimentResult> {
  return req("POST", "/experiment/evaluate", input);
}

// ---- Active experiments list (Slice 36) ----
export interface ActiveExperiment {
  experiment_id: string;
  product_name: string;
  break_even_cac: number;
  status: string;
  started_at: string;
  ended_at: string | null;
  latest_snapshot_date: string | null;
  ruling: string | null;
  risks: string[];
  actual_cac: number | null;
}

export function listActiveExperiments(): Promise<ActiveExperiment[]> {
  return req("GET", "/experiment/active");
}

export function patchExperimentStatus(
  experimentId: string,
  status: "active" | "ended",
): Promise<{ experiment_id: string; status: string; ended_at: string | null }> {
  return req("PATCH", `/experiment/${encodeURIComponent(experimentId)}/status`, { status });
}

// ---- Experiment notes (Slice 38) ----
export interface ExperimentNote {
  id: number;
  experiment_id: string;
  created_at: string;
  body: string;
}

export function addExperimentNote(experimentId: string, body: string): Promise<ExperimentNote> {
  return req("POST", `/experiment/${encodeURIComponent(experimentId)}/notes`, { body });
}

export function getExperimentNotes(experimentId: string): Promise<ExperimentNote[]> {
  return req("GET", `/experiment/${encodeURIComponent(experimentId)}/notes`);
}

// ---- Pipeline: offer -> approval ----
export interface PrepareOfferRequest {
  product_name: string;
  sale_price: number;
  key_benefit: string;
  target_customer: string;
  secondary_benefits: string[];
  common_objections: string[];
  shipping_note: string;
  return_policy: string;
  niche: string;
  channel: string;
  vendor: string;
  product_type: string;
}

export function prepareOffer(input: PrepareOfferRequest): Promise<ApprovalRecord> {
  return req("POST", "/pipeline/prepare-offer", input);
}

// ---- Execution (matches ExecutionResult.to_dict) ----
export interface ExecutionResult {
  approval_id: string;
  action: string;
  executed: boolean;
  dry_run: boolean;
  reason: string;
  detail: Record<string, unknown>;
}

export function executeApproved(approvalId: string, dryRun = true): Promise<ExecutionResult> {
  return req("POST", `/execute/${approvalId}`, { dry_run: dryRun });
}

export interface ExecutionLogEntry {
  id: number;
  event_type: string;
  event_id: string;
  created_at: string;
  payload: Record<string, unknown>;
}

export function fetchExecutionLog(): Promise<ExecutionLogEntry[]> {
  return req("GET", "/execute/log");
}

// ---- Live data sources (read-only, Slice 27/28) ----
export interface ImportRow {
  status: string;
  data: Record<string, string>;
  review_note: string;
}
export interface ImportResult {
  source: string;
  total_rows: number;
  ok_count: number;
  review_count: number;
  ok_rows: ImportRow[];
  review_rows: ImportRow[];
}

export function fetchStripeOrders(limit = 100): Promise<ImportResult> {
  return req("POST", `/sources/stripe/orders?limit=${limit}`);
}

export function fetchShopifyOrders(limit = 50): Promise<ImportResult> {
  return req("POST", `/sources/shopify/orders?limit=${limit}`);
}

export function fetchShopifyProducts(limit = 50): Promise<ImportResult> {
  return req("POST", `/sources/shopify/products?limit=${limit}`);
}

// ---- Import history (Slice 29) — persisting pulls ----
export interface ImportBatch {
  id: number;
  source: string;
  pulled_at: string;
  total_rows: number;
  ok_count: number;
  review_count: number;
}

export interface ImportBatchDetail extends ImportBatch {
  rows: Record<string, string>[];
}

export function pullAndSaveStripeOrders(limit = 100): Promise<ImportResult & { batch_id: number }> {
  return req("POST", `/imports/pull/stripe/orders?limit=${limit}`);
}

export function pullAndSaveShopifyOrders(limit = 50): Promise<ImportResult & { batch_id: number }> {
  return req("POST", `/imports/pull/shopify/orders?limit=${limit}`);
}

export function pullAndSaveShopifyProducts(limit = 50): Promise<ImportResult & { batch_id: number }> {
  return req("POST", `/imports/pull/shopify/products?limit=${limit}`);
}

export function listImportHistory(source?: string): Promise<ImportBatch[]> {
  const qs = source ? `?source=${encodeURIComponent(source)}` : "";
  return req("GET", `/imports${qs}`);
}

export function getImportBatch(batchId: number): Promise<ImportBatchDetail> {
  return req("GET", `/imports/${batchId}`);
}

// ---- Snapshots (Slice 34) ----
export interface SnapshotRequest {
  experiment_id: string;
  product_name: string;
  break_even_cac: number;
  snapshot_date?: string;
  qualified_visits?: number;
  orders?: number;
  total_ad_spend?: number;
  total_revenue?: number;
  refund_count?: number;
  actual_shipping_cost?: number;
  planned_shipping_cost?: number;
  add_to_cart_count?: number;
  consecutive_losing_periods?: number;
  budget_cap?: number;
}

export interface SnapshotRecord {
  experiment_id: string;
  product_name: string;
  break_even_cac: number;
  snapshot_date: string;
  qualified_visits: number;
  orders: number;
  total_ad_spend: number;
  total_revenue: number;
  conversion_rate: number;
  actual_cac: number;
  add_to_cart_rate: number;
  refund_rate: number;
}

export function submitSnapshot(input: SnapshotRequest): Promise<{ recorded: boolean; experiment_id: string; snapshot_date: string }> {
  return req("POST", "/snapshots", input);
}

export function listSnapshots(snapshotDate?: string): Promise<SnapshotRecord[]> {
  const qs = snapshotDate ? `?snapshot_date=${snapshotDate}` : "";
  return req("GET", `/snapshots${qs}`);
}

export function getSnapshotTrend(experimentId: string, days = 30): Promise<SnapshotRecord[]> {
  return req("GET", `/snapshots/trend/${encodeURIComponent(experimentId)}?days=${days}`);
}
