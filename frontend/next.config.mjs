// @ts-check
import createNextIntlPlugin from "next-intl/plugin";

// Points to our getRequestConfig entry file
const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
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

  // Standalone output for Docker
  output: "standalone",
};

export default withNextIntl(nextConfig);
