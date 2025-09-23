export default function LoadingPricing() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="h-6 w-40 bg-gray-200 rounded" />
        <div className="h-8 w-32 bg-gray-200 rounded" />
      </div>
      <div className="mm-card p-4 space-y-3">
        <div className="h-4 w-56 bg-gray-200 rounded" />
        <div className="flex flex-wrap gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-8 w-32 bg-gray-100 rounded" />
          ))}
        </div>
      </div>
      <div className="mm-card p-4 space-y-2">
        <div className="h-4 w-64 bg-gray-200 rounded" />
        <div className="overflow-x-auto">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-8 w-full bg-gray-100 rounded mb-2" />
          ))}
        </div>
      </div>
    </div>
  );
}
