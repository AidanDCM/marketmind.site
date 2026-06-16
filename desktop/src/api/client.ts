const BASE = "http://127.0.0.1:8000";

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

// ---- Health ----
export async function fetchHealth(): Promise<{ status: string; version: string }> {
  return req("GET", "/health");
}

// ---- Daily report ----
export interface DailyMetrics {
  date: string;
  orders: number;
  revenue: number;
  ad_spend: number;
  cac: number;
  contribution_dollars: number;
  conversion_rate: number;
  refund_rate: number;
  break_even_cac: number;
}
export interface DailyReport {
  date: string;
  metrics: DailyMetrics;
  pending_approvals: number;
  risks: string[];
  recommendations: string[];
}

export function fetchDailyReport(date: string): Promise<DailyReport> {
  return req("GET", `/report/daily?date=${date}`);
}

// ---- Approvals ----
export interface ApprovalRecord {
  approval_id: string;
  action: string;
  risk_level: string;
  status: string;
  summary: string;
  expected_cost: number;
  rollback_plan: string;
  reason: string;
  created_at: string;
  updated_at: string;
  approver_note: string;
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

// ---- Scoring ----
export interface CriterionScore {
  name: string;
  raw_score: number;
  weight: number;
  weighted_score: number;
  reason: string;
}
export interface ScoreResult {
  verdict: string;
  score: number;
  confidence: string;
  channel: string;
  breakdown: CriterionScore[];
  risks: string[];
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

// ---- Spec ----
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
export interface OfferSpec {
  headline: string;
  subheadline: string;
  bundle_items: { name: string; description: string }[];
  faq: { question: string; answer: string }[];
  cta: string;
  trust_signals: string[];
  safety_flags: string[];
}

export function generateSpec(input: SpecRequest): Promise<OfferSpec> {
  return req("POST", "/spec", input);
}
