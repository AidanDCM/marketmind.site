import { useEffect, useState } from "react";
import { fetchPendingApprovals } from "./api/client";

export function usePendingApprovalCount(apiOk: boolean | null, refreshToken = 0): number {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!apiOk) {
      setCount(0);
      return;
    }

    const refresh = () =>
      fetchPendingApprovals()
        .then((rows) => setCount(rows.length))
        .catch(() => setCount(0));

    refresh();
    const id = window.setInterval(refresh, 15_000);
    return () => window.clearInterval(id);
  }, [apiOk, refreshToken]);

  return count;
}
