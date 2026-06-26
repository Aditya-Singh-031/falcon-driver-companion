/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow serving .glb from /public/models
  webpack(config) {
    config.module.rules.push({
      test: /\.(glb|gltf)$/,
      type: 'asset/resource',
    });
    return config;
  },
  // Transpile three.js ecosystem
  transpilePackages: ['three', '@react-three/fiber', '@react-three/drei'],
};

export default nextConfig;
