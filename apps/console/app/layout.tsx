import React from 'react';
import '../styles/globals.css';
import Sidebar from '../components/layout/Sidebar';
import Topbar from '../components/layout/Topbar';
import AuthGate from '../components/auth/AuthGate';
import { ToastProvider } from '../components/ui/Toast';
import ErrorBoundary from '../components/ui/ErrorBoundary';
import SWRProvider from '../components/providers/SWRProvider';

const isProd = process.env.NODE_ENV === 'production';
const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
const apiBase = process.env.NEXT_PUBLIC_API_BASE || '';
const connectSrc = ["'self'", apiUrl, apiBase, 'wss:'].filter(Boolean).join(' ');
const csp = [
  "default-src 'self'",
  "script-src 'self' 'strict-dynamic'",
  "style-src 'self' https://fonts.googleapis.com",
  "img-src 'self' data: https: blob:",
  "font-src 'self' data: https://fonts.gstatic.com",
  `connect-src ${connectSrc}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "media-src 'self' blob:",
  "worker-src 'self' blob:",
  "manifest-src 'self'",
  "upgrade-insecure-requests",
].join('; ');

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {isProd && <meta httpEquiv="Content-Security-Policy" content={csp} />}
        <meta httpEquiv="Referrer-Policy" content="strict-origin-when-cross-origin" />
        {/* Inter font for polished typography (allowed by CSP) */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-slate-50 text-gray-900 font-sans">
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <Topbar />
            <main className="p-6 max-w-7xl w-full mx-auto">
              <ToastProvider>
                <SWRProvider>
                  <ErrorBoundary>
                    <AuthGate>
                      {children}
                    </AuthGate>
                    <footer className="mt-10 pt-6 border-t text-xs text-gray-500 flex items-center gap-3">
                      <a href="/privacy" className="hover:text-gray-700">Privacy</a>
                      <span>•</span>
                      <a href="/terms" className="hover:text-gray-700">Terms</a>
                    </footer>
                  </ErrorBoundary>
                </SWRProvider>
              </ToastProvider>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
