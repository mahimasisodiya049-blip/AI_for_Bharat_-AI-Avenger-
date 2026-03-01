import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'KiroFeed - Document Assistant',
  description: 'Multilingual document assistant powered by AI',
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
