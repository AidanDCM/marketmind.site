import { describe, it, expect, vi } from "vitest";
import { runOverviewDailyCycle, type OverviewCycleData } from "./overviewDailyCycle";

const sampleData = [{}, [], {}, {}, {}] as OverviewCycleData;

describe("runOverviewDailyCycle", () => {
  it("notifies after a successful cycle and refetch", async () => {
    const onCycleComplete = vi.fn();
    const runCycle = vi.fn().mockResolvedValue({});
    const fetchOverviewData = vi.fn().mockResolvedValue(sampleData);

    const result = await runOverviewDailyCycle({
      date: "2026-06-23",
      trendDays: 14,
      attentionOnly: false,
      runCycle,
      fetchOverviewData,
      onCycleComplete,
    });

    expect(runCycle).toHaveBeenCalledWith("2026-06-23");
    expect(fetchOverviewData).toHaveBeenCalledWith("2026-06-23", 14, false);
    expect(onCycleComplete).toHaveBeenCalledOnce();
    expect(result).toBe(sampleData);
  });

  it("does not notify when the cycle fails", async () => {
    const onCycleComplete = vi.fn();
    const runCycle = vi.fn().mockRejectedValue(new Error("cycle failed"));
    const fetchOverviewData = vi.fn();

    await expect(
      runOverviewDailyCycle({
        date: "2026-06-23",
        trendDays: 14,
        attentionOnly: false,
        runCycle,
        fetchOverviewData,
        onCycleComplete,
      }),
    ).rejects.toThrow("cycle failed");

    expect(fetchOverviewData).not.toHaveBeenCalled();
    expect(onCycleComplete).not.toHaveBeenCalled();
  });
});
