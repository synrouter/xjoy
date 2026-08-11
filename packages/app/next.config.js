/** @type {import('next').NextConfig} */
const isStaticExport = process.env.STATIC_EXPORT === '1';

/** @type {import('next').NextConfig} */
const baseConfig = {
  // GitHub Pages 静态导出：STATIC_EXPORT=1 pnpm run build:static
  output: isStaticExport ? 'export' : undefined,

  // 静态导出不支持图片优化
  images: {
    unoptimized: isStaticExport ? true : false,
  },

  // 静态导出时启用 trailingSlash（GitHub Pages 友好）
  trailingSlash: isStaticExport ? true : false,
};

// 条件性添加 rewrites（静态导出模式下不支持）
const rewritesConfig = (!isStaticExport && process.env.NODE_ENV !== 'production')
  ? {
      async rewrites() {
        return [
          {
            source: '/api/:path*',
            destination: 'http://localhost:8000/api/:path*',
          },
        ];
      },
    }
  : {};

const nextConfig = { ...baseConfig, ...rewritesConfig };

module.exports = nextConfig;
