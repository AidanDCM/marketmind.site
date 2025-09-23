export default function TermsPage() {
  return (
    <div className="mm-card p-6">
      <h1 className="text-2xl font-semibold mb-3">Terms of Service</h1>
      <p className="text-gray-700 text-sm mb-3">
        This console includes a brief Terms of Service summary. The authoritative version is maintained at the repository root in TERMS_OF_SERVICE.md.
      </p>
      <ul className="list-disc pl-6 text-sm text-gray-700 space-y-1">
        <li>Use of MarketMind is governed by the license and terms provided with the software.</li>
        <li>Availability targets and support policies are described in the Runbook and Oncall documentation.</li>
        <li>By using this console, you agree to abide by RBAC permissions and acceptable use policies.</li>
      </ul>
    </div>
  );
}
