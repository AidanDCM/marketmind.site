const ATTENTION_RULINGS = new Set(["kill", "pause_ads", "scale_requires_approval"]);

export function experimentNeedsAttention(exp: { ruling: string | null }): boolean {
  return exp.ruling != null && ATTENTION_RULINGS.has(exp.ruling);
}

export function experimentCardNeedsHighlight(exp: {
  ruling: string | null;
  actual_cac: number | null;
  break_even_cac: number;
}): boolean {
  return experimentNeedsAttention(exp)
    || (exp.actual_cac != null && exp.actual_cac > exp.break_even_cac);
}
