export default function LoadingFinance() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="h-6 w-40 bg-gray-200 rounded" />
        <div className="h-8 w-28 bg-gray-200 rounded" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-xl border p-5">
            <div className="h-3 w-2/3 bg-gray-200 rounded mb-2" />
            <div className="h-5 w-1/3 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="bg-white rounded-xl border p-4">
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((__, j) => (
                <div key={j} className="h-3 w-full bg-gray-200 rounded" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
