import type { Metadata } from "next";
import "../globals.css";

export const metadata: Metadata = {
  title: "NoblePort — Accredited Investor Portal",
  description: "SEC Rule 506(c) compliant accredited investor verification portal for NoblePort ETF.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-nb-navy text-white antialiased">
        <header className="border-b border-nb-slate/50 px-6 py-4">
          <div className="mx-auto flex max-w-5xl items-center justify-between">
            <a href="/" className="text-xl font-bold tracking-tight">
              <span className="text-nb-gold">Noble</span>Port
            </a>
            <span className="text-xs uppercase tracking-widest text-gray-400">
              Accredited Investors Only
            </span>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-12">{children}</main>
        <footer className="border-t border-nb-slate/50 px-6 py-6 text-center text-xs text-gray-500">
          Securities offered under SEC Rule 506(c). Available to verified accredited investors only.
        </footer>
      </body>
    </html>
  );
}
