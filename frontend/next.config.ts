import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployments
  output: 'standalone',
  
  // Image optimization
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'i.ytimg.com' },
      { protocol: 'https', hostname: 'yt3.ggpht.com' }
    ], // YouTube thumbnails
    formats: ['image/avif', 'image/webp'],
  },
  
  // Strict mode for better development experience
  reactStrictMode: true,
  
  // Disable powered by header
  poweredByHeader: false,
};

export default nextConfig;
