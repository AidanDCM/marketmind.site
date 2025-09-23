/** @type {import('next').NextConfig} */
const isPages = !!process.env.NEXT_PUBLIC_BASEPATH;
const isProduction = process.env.NODE_ENV === 'production';

const nextConfig = {
  output: isPages ? 'export' : undefined,
  // When deploying to GitHub Pages project site (e.g., /marketmind.site)
  basePath: process.env.NEXT_PUBLIC_BASEPATH || undefined,
  assetPrefix: process.env.NEXT_PUBLIC_BASEPATH || undefined,
  
  // Production security headers
  async headers() {
    if (!isProduction) return [];
    
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'geolocation=(), microphone=(), camera=()',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Production: Tightened script policy - remove unsafe-eval, only allow specific sources
              isProduction 
                ? "script-src 'self' 'strict-dynamic'" // Use strict-dynamic for better security
                : "script-src 'self' 'unsafe-eval'", // Dev: Keep unsafe-eval for Next.js HMR
              // Production: Restrict inline styles, allow specific Tailwind patterns
              isProduction
                ? "style-src 'self' https://fonts.googleapis.com" // Remove unsafe-inline in prod
                : "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com", // Dev: Keep for development
              "img-src 'self' data: https: blob:",
              "font-src 'self' data: https://fonts.gstatic.com",
              "connect-src 'self' " + (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001') + " wss:",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "object-src 'none'",
              "media-src 'self' blob:",
              "worker-src 'self' blob:",
              "manifest-src 'self'",
              "upgrade-insecure-requests",
            ].join('; '),
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains',
          },
        ],
      },
    ];
  },
  
  // Environment variable validation
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  },
  
  // Production optimizations
  ...(isProduction && {
    poweredByHeader: false,
    generateEtags: true,
    compress: true,
  }),
};

module.exports = nextConfig;
