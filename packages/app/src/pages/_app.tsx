import { useState, useEffect } from 'react';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import Layout from '@/components/Layout';
import Onboarding from '@/components/Onboarding';
import '@/styles/globals.css';

const ONBOARDING_KEY = 'xjoy_onboarding_completed';

export default function App({ Component, pageProps, router }: AppProps) {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // 检查是否需要显示引导
    const completed = localStorage.getItem(ONBOARDING_KEY);
    if (!completed) {
      setShowOnboarding(true);
    }
    setReady(true);
  }, []);

  const handleOnboardingComplete = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setShowOnboarding(false);
  };

  // 在客户端就绪前不渲染，避免 SSR 闪烁
  if (!ready) {
    return (
      <div className="flex items-center justify-center h-dvh bg-parchment-50">
        <div className="flex flex-col items-center gap-4">
          <span className="text-4xl">📖</span>
          <p className="text-parchment-500 text-sm">Xjoy</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
      </Head>
      {showOnboarding && <Onboarding onComplete={handleOnboardingComplete} />}
      <Layout>
        <Component {...pageProps} key={router.asPath} />
      </Layout>
    </>
  );
}
