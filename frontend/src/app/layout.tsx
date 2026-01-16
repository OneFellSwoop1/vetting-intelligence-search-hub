import { Inter } from 'next/font/google';
import './globals.css';
import type { Metadata } from 'next';

const inter = Inter({ subsets: ['latin'] });

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://poissonai.com';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'POISSON AI® - Vetting Intelligence Search Hub | Government Transparency Platform',
    template: '%s | POISSON AI®'
  },
  description: 'Enterprise Government Transparency & Due Diligence Platform. Search 15M+ government records across FEC, NYC Contracts, Federal Lobbying, and more. Replace $10,000+/year tools with AI-powered intelligence.',
  keywords: [
    'government transparency',
    'due diligence',
    'compliance research',
    'vetting intelligence',
    'government data search',
    'lobbying records',
    'campaign finance',
    'federal spending',
    'NYC contracts',
    'FEC data',
    'Senate LDA',
    'compliance tools',
    'KYC screening',
    'third-party risk',
    'vendor due diligence',
    'POISSON AI'
  ],
  authors: [{ name: 'POISSON AI', url: siteUrl }],
  creator: 'POISSON AI',
  publisher: 'POISSON AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  
  // Open Graph metadata for social sharing
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: siteUrl,
    siteName: 'POISSON AI® Vetting Intelligence',
    title: 'POISSON AI® - Vetting Intelligence Search Hub',
    description: 'Enterprise Government Transparency & Due Diligence Platform. Search 15M+ government records. Replace $10K+/year commercial tools.',
    images: [
      {
        url: '/images/og-image.png',
        width: 1200,
        height: 630,
        alt: 'POISSON AI Vetting Intelligence Search Hub',
        type: 'image/png',
      },
      {
        url: '/images/poissonai_logo.png',
        width: 512,
        height: 512,
        alt: 'POISSON AI Logo',
        type: 'image/png',
      }
    ],
  },
  
  // Twitter Card metadata
  twitter: {
    card: 'summary_large_image',
    site: '@poissonai',
    creator: '@poissonai',
    title: 'POISSON AI® - Vetting Intelligence Search Hub',
    description: 'Enterprise Government Transparency Platform. Search 15M+ records across FEC, NYC Contracts, Federal Lobbying, and more.',
    images: ['/images/twitter-image.png'],
  },
  
  // Robots directives
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  
  // Icons and manifest
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      {
        rel: 'icon',
        url: '/android-chrome-192x192.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        rel: 'icon',
        url: '/android-chrome-512x512.png',
        sizes: '512x512',
        type: 'image/png',
      },
    ],
  },
  manifest: '/site.webmanifest',
  
  // Additional metadata
  category: 'technology',
  classification: 'Business Intelligence, Government Data, Compliance Software',
  
  // Verification tags (add your actual verification codes when available)
  verification: {
    google: 'your-google-verification-code',
    // yandex: 'your-yandex-verification-code',
    // bing: 'your-bing-verification-code',
  },
  
  // Alternate languages (if you expand internationally)
  alternates: {
    canonical: siteUrl,
    languages: {
      'en-US': siteUrl,
    },
  },
  
  // App-specific metadata
  applicationName: 'POISSON AI Vetting Intelligence',
  appleWebApp: {
    capable: true,
    title: 'POISSON AI',
    statusBarStyle: 'black-translucent',
  },
  
  // Other
  other: {
    'apple-mobile-web-app-capable': 'yes',
    'mobile-web-app-capable': 'yes',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Additional SEO tags */}
        <link rel="canonical" href={siteUrl} />
        <meta name="theme-color" content="#6366f1" />
        <meta name="color-scheme" content="dark light" />
      </head>
      <body className={inter.className}>
        <div className="relative min-h-screen bg-background">
          {children}
        </div>
      </body>
    </html>
  );
} 