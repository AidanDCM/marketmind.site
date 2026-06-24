import { describe, it, expect } from "vitest";

function isSnapshotStale(snapshotDate: string | null, asOf: string): boolean {
  return snapshotDate != null && snapshotDate < asOf;
}

describe("Overview trend helpers", () => {
  it("flags snapshot stale when before as-of date", () => {
    expect(isSnapshotStale("2026-06-20", "2026-06-23")).toBe(true);
    expect(isSnapshotStale("2026-06-23", "2026-06-23")).toBe(false);
    expect(isSnapshotStale(null, "2026-06-23")).toBe(false);
  });
});
