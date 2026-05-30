/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy API calls to the FastAPI backend so the browser sees a same-origin
  // endpoint and we avoid CORS entirely in dev.
  async rewrites() {
    const backend = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
