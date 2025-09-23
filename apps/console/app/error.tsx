"use client";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="mm-card p-8 text-center">
      <h1 className="text-2xl font-semibold mb-2">Something went wrong</h1>
      <p className="text-gray-600 text-sm mb-4">An unexpected error occurred while rendering this page.</p>
      {error?.message && (<div className="text-xs text-red-600 mb-3">{error.message}</div>)}
      <div className="flex items-center justify-center gap-2">
        <button onClick={() => reset()} className="mm-btn">Try again</button>
        <a href="/" className="mm-btn">Go to Overview</a>
      </div>
    </div>
  );
}
