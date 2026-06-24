export type ExperimentProductLookup = {
  experiment_id: string;
  product_name: string;
};

export function parseDailyReportProductPrefix(text: string): string | null {
  const idx = text.indexOf(": ");
  if (idx <= 0) {
    return null;
  }
  const prefix = text.slice(0, idx).trim();
  return prefix || null;
}

export function buildExperimentProductLookup(
  sources: ExperimentProductLookup[][],
): Map<string, string> {
  const lookup = new Map<string, string>();
  for (const list of sources) {
    for (const item of list) {
      lookup.set(item.product_name.toLowerCase(), item.experiment_id);
    }
  }
  return lookup;
}

export function resolveExperimentIdForReportLine(
  text: string,
  lookup: Map<string, string>,
): string | undefined {
  const productName = parseDailyReportProductPrefix(text);
  if (!productName) {
    return undefined;
  }
  return lookup.get(productName.toLowerCase());
}
