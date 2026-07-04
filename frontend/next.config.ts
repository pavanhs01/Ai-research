import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  images: {
    remotePatterns: [{ protocol: "https", hostname: "img.clerk.com" }],
  },
};

export default nextConfig;
