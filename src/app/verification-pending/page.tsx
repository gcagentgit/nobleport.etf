export default function VerificationPendingPage() {
  return (
    <div className="mx-auto max-w-lg py-16 text-center">
      <div className="mb-6 text-5xl">&#9745;</div>
      <h1 className="mb-4 text-2xl font-bold">Application Received</h1>
      <p className="mb-6 text-gray-300">
        Your accredited investor application has been submitted. Our compliance
        team will contact you within 2 business days to request verification
        documents.
      </p>
      <div className="rounded-lg border border-nb-slate p-6 text-left text-sm">
        <h2 className="mb-3 font-semibold text-nb-gold">What Happens Next</h2>
        <ol className="flex flex-col gap-3 text-gray-400">
          <li>
            <strong className="text-gray-200">1. Document Request</strong> — We will
            email you with a secure link to upload verification documents.
          </li>
          <li>
            <strong className="text-gray-200">2. Review</strong> — A third-party
            verification provider reviews your accreditation status.
          </li>
          <li>
            <strong className="text-gray-200">3. Access Granted</strong> — Once
            verified, you will receive portal access to view fund details and
            subscription documents.
          </li>
        </ol>
      </div>
      <a
        href="/"
        className="mt-8 inline-block text-sm text-nb-gold hover:underline"
      >
        Return to Home
      </a>
    </div>
  );
}
