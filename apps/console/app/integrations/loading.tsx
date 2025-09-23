export default function LoadingIntegrations() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="h-6 w-40 bg-gray-200 rounded" />
        <div className="h-8 w-24 bg-gray-200 rounded" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="mm-card p-4 space-y-2">
            <div className="h-3 w-1/2 bg-gray-200 rounded" />
            <div className="h-3 w-1/3 bg-gray-100 rounded" />
            <div className="h-3 w-full bg-gray-100 rounded" />
          </div>
        ))}
      </div>
      <section>
        <div className="h-4 w-48 bg-gray-200 rounded mb-2" />
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-8 w-full bg-gray-100 rounded" />
          ))}
        </div>
      </section>
    </div>
  );
}
