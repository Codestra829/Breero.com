import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd(), "../.."),
  transpilePackages: ["@breero/ui"],
  // Local screenshot runs may bypass the image cache on disk-constrained hosts. Production keeps
  // Next/Image optimization enabled unless this explicit build-time flag is set.
  images: { unoptimized: process.env.NEXT_IMAGE_UNOPTIMIZED === "1" },
};

export default nextConfig;
