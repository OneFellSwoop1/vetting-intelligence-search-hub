import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Vetting Intelligence Search Hub',
  description: 'Search and analyze government data across multiple jurisdictions and data sources',
  keywords: 'government data, vetting, search, transparency, lobbying, campaign finance',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <div className="relative min-h-screen bg-background">
          {children}
        </div>
      </body>
    </html>
  );
} 