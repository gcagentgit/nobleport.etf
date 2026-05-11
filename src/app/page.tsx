export default function LandingPage() {
  return (
    <div className="flex flex-col items-center gap-8 py-16 text-center">
      <h1 className="text-4xl font-bold leading-tight md:text-5xl">
        Institutional-Grade Real Estate,
        <br />
        <span className="text-nb-gold">On-Chain</span>
      </h1>
      <p className="max-w-2xl text-lg text-gray-300">
        NoblePort ETF tokenizes Newburyport real estate into a regulated,
        blockchain-settled fund. Participation is limited to verified accredited
        investors under SEC Rule 506(c).
      </p>
      <a
        href="/investor"
        className="rounded-lg bg-nb-gold px-8 py-3 text-lg font-semibold text-nb-navy transition hover:brightness-110"
      >
        Begin Accreditation
      </a>
      <div className="mt-12 grid max-w-3xl grid-cols-1 gap-6 text-left md:grid-cols-3">
        <div className="rounded-lg border border-nb-slate p-5">
          <h3 className="mb-2 font-semibold text-nb-gold">506(c) Compliant</h3>
          <p className="text-sm text-gray-400">
            Every investor verified through SEC-recognized methods before fund access.
          </p>
        </div>
        <div className="rounded-lg border border-nb-slate p-5">
          <h3 className="mb-2 font-semibold text-nb-gold">AES-256 Encrypted</h3>
          <p className="text-sm text-gray-400">
            PII encrypted at rest with AES-256-GCM. Email hashed for dedup without decryption.
          </p>
        </div>
        <div className="rounded-lg border border-nb-slate p-5">
          <h3 className="mb-2 font-semibold text-nb-gold">Blockchain Settled</h3>
          <p className="text-sm text-gray-400">
            NBPT token with TWAP oracle, reserve vault, and human-approval governance.
          </p>
        </div>
      </div>
    </div>
  );
}
