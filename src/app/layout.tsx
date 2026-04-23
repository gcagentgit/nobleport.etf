import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'NoblePort ETF — Intake',
  description: 'Submit your project for a proposal and deposit.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'system-ui, -apple-system, sans-serif', background: '#f8f9fb' }}>
        {children}
      </body>
    </html>
  );
}
