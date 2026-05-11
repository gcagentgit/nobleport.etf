export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-4 text-2xl font-bold">Investor Dashboard</h1>
      <div className="rounded-lg border border-nb-slate p-8 text-center">
        <p className="mb-4 text-gray-400">
          This page is gated on <code className="text-nb-gold">VERIFIED</code> investor status.
        </p>
        <p className="text-sm text-gray-500">
          Session authentication (NextAuth) and status-gated access will be wired
          here. Once connected, verified investors will see fund performance,
          subscription documents, and distribution history.
        </p>
      </div>
      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-nb-slate p-5">
          <h3 className="mb-1 text-sm font-semibold text-nb-gold">Fund NAV</h3>
          <p className="text-2xl font-bold">—</p>
          <p className="text-xs text-gray-500">Requires verified access</p>
        </div>
        <div className="rounded-lg border border-nb-slate p-5">
          <h3 className="mb-1 text-sm font-semibold text-nb-gold">Your Allocation</h3>
          <p className="text-2xl font-bold">—</p>
          <p className="text-xs text-gray-500">Requires verified access</p>
        </div>
        <div className="rounded-lg border border-nb-slate p-5">
          <h3 className="mb-1 text-sm font-semibold text-nb-gold">Distributions</h3>
          <p className="text-2xl font-bold">—</p>
          <p className="text-xs text-gray-500">Requires verified access</p>
        </div>
      </div>
    </div>
  );
}
