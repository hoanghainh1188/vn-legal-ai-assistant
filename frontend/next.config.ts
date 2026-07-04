import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";

// CSP static (pragmatic, Pha 4). connect-src cho phép Supabase (auth) + same-origin
// (proxy /api/query). Dev thêm ws/http localhost cho HMR. Siết nonce-based ở Pha 6.
const connectSrc = [
  "'self'",
  supabaseUrl,
  isDev ? "ws://localhost:* http://localhost:*" : "",
]
  .filter(Boolean)
  .join(" ");

const csp = [
  "default-src 'self'",
  // 'unsafe-eval' CHỈ ở dev (React dev-mode cần eval để debug); production KHÔNG có.
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self'",
  `connect-src ${connectSrc}`,
  "frame-ancestors 'none'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()",
  },
  // HSTS chỉ khi production (HTTPS thật — Pha 6).
  ...(isDev
    ? []
    : [
        {
          key: "Strict-Transport-Security",
          value: "max-age=31536000; includeSubDomains",
        },
      ]),
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
