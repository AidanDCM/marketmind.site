export default function NotFound() {
  return (
    <div className="mm-card p-8 text-center">
      <h1 className="text-2xl font-semibold mb-2">Page not found</h1>
      <p className="text-gray-600 text-sm mb-4">The page you are looking for does not exist or has moved.</p>
      <div className="flex items-center justify-center gap-2">
        <a href="/" className="mm-btn">Go to Overview</a>
        <a href="/onboarding" className="mm-btn">Onboarding</a>
      </div>
    </div>
  );
}
