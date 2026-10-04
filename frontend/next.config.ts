import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep Turbopack scoped to this application. The parent OneDrive directory
  // contains an unrelated lockfile that must not become part of this build.
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
