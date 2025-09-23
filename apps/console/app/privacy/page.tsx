export default function PrivacyPage() {
  return (
    <div className="mm-card p-6">
      <h1 className="text-2xl font-semibold mb-3">Privacy Policy</h1>
      <p className="text-gray-700 text-sm mb-3">
        This console exposes a concise Privacy Policy. For the full version maintained with releases, see the repository root file PRIVACY_POLICY.md.
      </p>
      <ul className="list-disc pl-6 text-sm text-gray-700 space-y-1">
        <li>We minimize data collection and process only what is necessary to operate MarketMind.</li>
        <li>Credentials and secrets are stored securely following best practices; no secrets are committed to the repository.</li>
        <li>Telemetry (if enabled) is environment-gated and excludes PII by default.</li>
        <li>Data deletion and retention follow documented policies; contact support for DSAR requests.</li>
      </ul>
    </div>
  );
}
