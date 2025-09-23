"use client";

import React from "react";

export function InlineError({ title = "Unable to load data", message, onRetry }:{ title?: string; message?: string; onRetry?: () => void }){
  return (
    <div className="p-3 rounded-md border bg-red-50 border-red-200 text-red-800 flex items-start justify-between gap-3">
      <div>
        <div className="text-sm font-medium">{title}</div>
        {message && <div className="text-xs mt-0.5 text-red-700/90">{message}</div>}
      </div>
      {onRetry && <button className="text-xs px-2 py-1 rounded border border-red-300 hover:bg-red-100" onClick={onRetry}>Retry</button>}
    </div>
  );
}
