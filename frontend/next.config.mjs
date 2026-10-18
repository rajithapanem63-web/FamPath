// @ts-check
import createNextIntlPlugin from "next-intl/plugin";

// Points to our getRequestConfig entry file
const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable ESLint and TypeScript checks during build (for faster deployment)
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },

  // Allow build to succeed even with prerendering errors (next-intl needs dynamic rendering)
  staticPageGenerationTimeout: 1000,
  
  // Experimental features
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },

  // Image optimisation
  images: {
    domains: ["localhost"],
    formats: ["image/avif", "image/webp"],
  },

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },

  reactStrictMode: true,
};

export default withNextIntl(nextConfig);
