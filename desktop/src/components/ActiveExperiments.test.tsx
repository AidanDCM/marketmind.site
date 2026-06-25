import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ActiveExperiments } from "./ActiveExperiments";
import type { ActiveExperiment } from "../api/client";

vi.mock("../api/client", () => ({
  listActiveExperiments: vi.fn(),
  patchExperimentStatus: vi.fn(),
  addExperimentNote: vi.fn(),
  getExperimentNotes: vi.fn().mockResolvedValue([]),
  fetchExperimentChecklist: vi.fn().mockResolvedValue({
    ready: false,
    blockers: [],
    items: [],
  }),
  fetchExperimentMistakes: vi.fn().mockResolvedValue({ recorded: [], suggested: [] }),
  recordMistake: vi.fn(),
}));

vi.mock("./activeExperimentsPreferences", () => ({
  ACTIVE_STATUS_FILTERS: ["all", "active", "ended"],
  readActiveAttentionOnlyPreference: () => false,
  readActiveStatusFilterPreference: () => "all",
  writeActiveAttentionOnlyPreference: vi.fn(),
  writeActiveStatusFilterPreference: vi.fn(),
}));

import {
  listActiveExperiments,
  patchExperimentStatus,
  fetchExperimentChecklist,
  fetchExperimentMistakes,
} from "../api/client";

const baseExp = (overrides: Partial<ActiveExperiment> = {}): ActiveExperiment => ({
  experiment_id: "exp-ok",
  product_name: "Widget",
  break_even_cac: 25,
  status: "active",
  started_at: "2026-06-01T00:00:00Z",
  ended_at: null,
  latest_snapshot_date: "2026-06-14",
  ruling: "continue",
  risks: [],
  actual_cac: 10,
  ...overrides,
});

async function renderActive(
  experiments: ActiveExperiment[],
  props: Partial<{
    focusExperimentId: string | null;
    initialAttentionOnly: boolean;
    onOpenTrend: (experimentId: string) => void;
  }> = {},
) {
  vi.mocked(listActiveExperiments).mockResolvedValue(experiments);
  render(
    <ActiveExperiments
      focusExperimentId={props.focusExperimentId ?? null}
      initialAttentionOnly={props.initialAttentionOnly ?? false}
      onOpenTrend={props.onOpenTrend}
    />,
  );
  await waitFor(() => {
    expect(document.querySelector(".loading-row")).toBeNull();
  });
}

describe("ActiveExperiments lifecycle wiring", () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
    vi.mocked(listActiveExperiments).mockReset();
    vi.mocked(patchExperimentStatus).mockReset();
    vi.mocked(patchExperimentStatus).mockResolvedValue({
      experiment_id: "exp-ok",
      status: "ended",
      ended_at: "2026-06-15T00:00:00Z",
    });
  });

  it("shows attention banner when experiments need action", async () => {
    await renderActive([
      baseExp(),
      baseExp({
        experiment_id: "exp-kill",
        ruling: "kill",
        actual_cac: 50,
      }),
    ]);

    expect(screen.getByText(/1 experiment require attention/i)).toBeInTheDocument();
  });

  it("filters to needs-attention experiments", async () => {
    await renderActive([
      baseExp(),
      baseExp({
        experiment_id: "exp-pause",
        ruling: "pause_ads",
        actual_cac: 40,
      }),
    ]);

    fireEvent.click(screen.getByLabelText("Needs attention"));

    await waitFor(() => {
      expect(screen.getByText("exp-pause")).toBeInTheDocument();
      expect(screen.queryByText("exp-ok")).toBeNull();
    });
  });

  it("filters by ended status", async () => {
    await renderActive([
      baseExp(),
      baseExp({
        experiment_id: "exp-ended",
        status: "ended",
        ended_at: "2026-06-10T00:00:00Z",
      }),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "ended" }));

    await waitFor(() => {
      expect(screen.getByText("exp-ended")).toBeInTheDocument();
      expect(screen.queryByText("exp-ok")).toBeNull();
    });
  });

  it("opens focused experiment card by default", async () => {
    await renderActive([baseExp()], { focusExperimentId: "exp-ok" });

    expect(screen.getByText("Break-even CAC")).toBeInTheDocument();
  });

  it("opens trend chart from experiment card", async () => {
    const onOpenTrend = vi.fn();
    await renderActive([baseExp()], { onOpenTrend });

    fireEvent.click(screen.getByRole("button", { name: "Chart" }));
    expect(onOpenTrend).toHaveBeenCalledWith("exp-ok");
  });

  it("ends an active experiment from the expanded card", async () => {
    await renderActive([baseExp()], { focusExperimentId: "exp-ok" });

    fireEvent.click(screen.getByRole("button", { name: "End experiment" }));

    await waitFor(() => {
      expect(patchExperimentStatus).toHaveBeenCalledWith("exp-ok", "ended");
    });
  });

  it("does not show scale ruling in attention filter when only continue experiments exist", async () => {
    await renderActive([baseExp({ ruling: "continue" })]);

    fireEvent.click(screen.getByLabelText("Needs attention"));

    await waitFor(() => {
      expect(screen.getByText(/No experiments need attention/i)).toBeInTheDocument();
    });
  });

  it("includes scale_requires_approval in attention filter", async () => {
    await renderActive([
      baseExp(),
      baseExp({
        experiment_id: "exp-scale",
        ruling: "scale_requires_approval",
        actual_cac: 20,
      }),
    ]);

    fireEvent.click(screen.getByLabelText("Needs attention"));

    await waitFor(() => {
      expect(screen.getByText("exp-scale")).toBeInTheDocument();
      expect(screen.queryByText("exp-ok")).toBeNull();
    });
  });

  it("reactivates an ended experiment from the expanded card", async () => {
    vi.mocked(patchExperimentStatus).mockResolvedValue({
      experiment_id: "exp-ended",
      status: "active",
      ended_at: null,
    });
    await renderActive(
      [
        baseExp({
          experiment_id: "exp-ended",
          status: "ended",
          ended_at: "2026-06-10T00:00:00Z",
        }),
      ],
      { focusExperimentId: "exp-ended" },
    );

    fireEvent.click(screen.getByRole("button", { name: "Reactivate" }));

    await waitFor(() => {
      expect(patchExperimentStatus).toHaveBeenCalledWith("exp-ended", "active");
    });
  });

  it("loads scale-readiness checklist when card is focused", async () => {
    vi.mocked(fetchExperimentChecklist).mockResolvedValue({
      ready: false,
      blockers: ["Need more visits"],
      items: [
        {
          item_id: "visits",
          description: "Minimum qualified visits",
          passed: false,
          evidence: "50 / 100",
        },
      ],
    });
    await renderActive([baseExp()], { focusExperimentId: "exp-ok" });

    await waitFor(() => {
      expect(screen.getByText("Scale-readiness checklist")).toBeInTheDocument();
      expect(screen.getByText("Not ready")).toBeInTheDocument();
      expect(screen.getByText("Minimum qualified visits")).toBeInTheDocument();
    });
    expect(fetchExperimentChecklist).toHaveBeenCalledWith("exp-ok");
  });

  it("loads mistake tracker when card is focused", async () => {
    vi.mocked(fetchExperimentMistakes).mockResolvedValue({
      recorded: [
        {
          mistake_id: "m1",
          category: "scale_too_early",
          summary: "Scaled before checklist passed",
          lesson: "Wait for visits threshold",
          tags: ["scale"],
          created_at: "2026-06-01T00:00:00Z",
        },
      ],
      suggested: [],
    });
    await renderActive([baseExp()], { focusExperimentId: "exp-ok" });

    await waitFor(() => {
      expect(screen.getByText("Lessons learned")).toBeInTheDocument();
      expect(screen.getByText("Scaled before checklist passed")).toBeInTheDocument();
    });
    expect(fetchExperimentMistakes).toHaveBeenCalledWith("exp-ok");
  });
});
