import { useEffect, useState } from "react";
import { fetchExperimentPortfolio } from "./api/client";

export function useExperimentAttentionCount(apiOk: boolean | null, refreshToken = 0): number {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!apiOk) {
      setCount(0);
      return;
    }

    const refresh = () =>
      fetchExperimentPortfolio()
        .then((portfolio) => setCount(portfolio.needs_attention))
        .catch(() => setCount(0));

    refresh();
    const id = window.setInterval(refresh, 15_000);
    return () => window.clearInterval(id);
  }, [apiOk, refreshToken]);

  return count;
}
