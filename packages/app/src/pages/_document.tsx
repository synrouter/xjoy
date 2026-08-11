import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="zh-CN">
      <Head>
        {/* PWA Manifest */}
        <link rel="manifest" href="/manifest.json" />

        {/* Apple touch icon (iOS 主屏幕) */}
        <link rel="apple-touch-icon" href="/icons/icon-192.svg" />

        {/* 主题颜色 */}
        <meta name="theme-color" content="#8b6914" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Xjoy" />

        {/* SEO */}
        <meta name="description" content="AI-Powered KJV Bible Study App — 英王钦定本圣经智能研经助手" />
      </Head>
      <body className="min-h-screen flex flex-col">
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
