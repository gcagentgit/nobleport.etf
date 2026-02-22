import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'NoblePort SSI Architecture',
  description: 'Self-Sovereign Identity & ENS DID Resolution Dashboard for NoblePort ETF',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
