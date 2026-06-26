/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow cross-origin requests to the local FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/:path*',
      },
    ];
  },
  // Needed for @react-three/fiber
  transpilePackages: ['three'],
  webpack(config) {
    config.module.rules.push({
      test: /\.(glb|gltf)$/,
      type: 'asset/resource',
    });
    return config;
  },
};

export default nextConfig;
