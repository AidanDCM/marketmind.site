import { useEffect, useState } from "react";
import { fetchPendingApprovals } from "./api/client";

export interface PendingApprovalSummary {
  count: number;
  firstApprovalId: string | null;
}

const EMPTY_SUMMARY: PendingApprovalSummary = { count: 0, firstApprovalId: null };

export function usePendingApprovalSummary(
  apiOk: boolean | null,
  refreshToken = 0,
): PendingApprovalSummary {
  const [summary, setSummary] = useState<PendingApprovalSummary>(EMPTY_SUMMARY);

  useEffect(() => {
    if (!apiOk) {
      setSummary(EMPTY_SUMMARY);
      return;
    }

    const refresh = () =>
      fetchPendingApprovals()
        .then((rows) => setSummary({
          count: rows.length,
          firstApprovalId: rows[0]?.approval_id ?? null,
        }))
        .catch(() => setSummary(EMPTY_SUMMARY));

    refresh();
    const id = window.setInterval(refresh, 15_000);
    return () => window.clearInterval(id);
  }, [apiOk, refreshToken]);

  return summary;
}
