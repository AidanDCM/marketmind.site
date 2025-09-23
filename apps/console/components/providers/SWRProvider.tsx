"use client";

import React from "react";
import { SWRConfig } from "swr";
import { getJson } from "../../lib/api";

export default function SWRProvider({ children }: { children: React.ReactNode }){
  return (
    <SWRConfig value={{
      // Global SWR defaults for a smoother UX
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      focusThrottleInterval: 30000,
      dedupingInterval: 2000,
      shouldRetryOnError: true,
      errorRetryCount: 2,
      errorRetryInterval: 2000,
      fetcher: (key: string) => getJson(key),
    }}>
      {children}
    </SWRConfig>
  );
}
