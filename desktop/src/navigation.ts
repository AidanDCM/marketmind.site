export type Page =
  | "overview"
  | "approvals"
  | "score"
  | "niche"
  | "economics"
  | "experiment"
  | "spec"
  | "prepare"
  | "supplier"
  | "lessons"
  | "live"
  | "history"
  | "snapshots"
  | "trend"
  | "active";

export type PageContext = {
  experimentId?: string;
  trendDays?: number;
  attentionOnly?: boolean;
};
