const ATTENTION_RULINGS = new Set(["kill", "pause_ads", "scale_requires_approval"]);

export function experimentNeedsAttention(exp: { ruling: string | null }): boolean {
  return exp.ruling != null && ATTENTION_RULINGS.has(exp.ruling);
}
