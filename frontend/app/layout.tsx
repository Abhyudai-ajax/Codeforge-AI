import type { Metadata } from 'next';
import './globals.css';
import { Providers } from '@/providers';
import AuthGuard from '@/components/auth/AuthGuard';

export const metadata: Metadata = {
  title: 'CodeForge AI - AI-Powered Collaborative Coding Platform',
  description:
    'An intelligent platform combining the best of LeetCode, GitHub Copilot, Replit, and CodeSandbox for collaborative coding.',
  keywords: ['coding', 'ai', 'collaborative', 'leetcode', 'copilot', 'replit'],
  authors: [{ name: 'CodeForge AI Team' }],
  creator: 'CodeForge AI',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://codeforge.ai',
    title: 'CodeForge AI',
    description: 'AI-Powered Collaborative Coding Platform',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'CodeForge AI',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CodeForge AI',
    description: 'AI-Powered Collaborative Coding Platform',
    images: ['/og-image.png'],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <Providers>
          <AuthGuard>{children}</AuthGuard>
        </Providers>
      </body>
    </html>
  );
}
