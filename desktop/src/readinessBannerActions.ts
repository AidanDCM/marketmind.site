export type ReadinessBannerAction =
  | { kind: "approvals" }
  | { kind: "active"; experimentId: string }
  | { kind: "snapshots"; snapshotDate: string; experimentId?: string };

const PENDING_APPROVALS =
  /^(\d+) pending approval\(s\) have not been reviewed$/;
const EXPERIMENT_RULING =
  /^Experiment '([^']+)' ruling is '[^']+' — action required$/;
const MISSING_SNAPSHOT =
  /^(\d+) active experiment\(s\) missing snapshot for (\d{4}-\d{2}-\d{2}): (.+)$/;

export function parseReadinessBannerAction(text: string): ReadinessBannerAction | null {
  let match = PENDING_APPROVALS.exec(text);
  if (match) {
    return { kind: "approvals" };
  }

  match = EXPERIMENT_RULING.exec(text);
  if (match) {
    return { kind: "active", experimentId: match[1] };
  }

  match = MISSING_SNAPSHOT.exec(text);
  if (match) {
    const idsPart = match[3].replace(/…$/, "").trim();
    const firstId = idsPart.split(",")[0]?.trim();
    return {
      kind: "snapshots",
      snapshotDate: match[2],
      experimentId: firstId || undefined,
    };
  }

  return null;
}

export function readinessBannerActionLabel(action: ReadinessBannerAction): string {
  switch (action.kind) {
    case "approvals":
      return "Open queue";
    case "active":
      return "View experiment";
    case "snapshots":
      return "Record snapshot";
  }
}
