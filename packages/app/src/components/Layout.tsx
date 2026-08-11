'use client';

import { useRouter } from 'next/router';
import React from 'react';
import Link from 'next/link';

interface Tab {
  key: string;
  label: string;
  icon: string;
  path: string;
}

const TABS: Tab[] = [
  { key: 'today', label: 'Today', icon: '📅', path: '/' },
  { key: 'bible', label: 'Bible', icon: '📖', path: '/bible' },
  { key: 'study', label: 'Study', icon: '🎓', path: '/study' },
  { key: 'me', label: 'Me', icon: '👤', path: '/me' },
];

/** 判断当前路径属于哪个 Tab */
function activeTab(pathname: string): string {
  if (pathname === '/') return 'today';
  if (pathname.startsWith('/bible')) return 'bible';
  if (pathname.startsWith('/study')) return 'study';
  if (pathname.startsWith('/me')) return 'me';
  // search, chat etc. default to bible context
  if (pathname.startsWith('/search') || pathname.startsWith('/chat')) return 'bible';
  return 'today';
}

interface Props {
  children: React.ReactNode;
}

export default function Layout({ children }: Props) {
  const router = useRouter();
  const active = activeTab(router.pathname);

  return (
    <div className="flex flex-col h-dvh bg-parchment-50 max-w-lg mx-auto relative">
      {/* 主内容区域 */}
      <main className="flex-1 overflow-y-auto relative">{children}

        {/* 浮动反馈按钮 — 不在反馈页面或聊天页面时显示，避免遮挡输入区域 */}
        {router.pathname !== '/feedback' && router.pathname !== '/chat' && (
          <Link
            href="/feedback"
            className="fixed bottom-20 right-4 z-40 w-11 h-11 bg-white border border-parchment-300
                       rounded-full shadow-lg flex items-center justify-center text-lg
                       hover:shadow-xl hover:border-parchment-400 active:scale-90 transition-all"
            title="发送反馈"
          >
            💬
          </Link>
        )}
      </main>

      {/* 底部标签导航 */}
      <nav className="shrink-0 bg-white border-t border-parchment-200 safe-bottom">
        <div className="flex justify-around items-center h-14 px-2">
          {TABS.map((tab) => {
            const isActive = active === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => router.push(tab.path)}
                className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                  isActive
                    ? 'text-parchment-700'
                    : 'text-parchment-400 hover:text-parchment-500'
                }`}
              >
                <span className="text-lg leading-none mb-0.5">{tab.icon}</span>
                <span className="text-[10px] font-medium leading-none">
                  {tab.label}
                </span>
                {isActive && (
                  <span className="w-5 h-0.5 bg-parchment-600 rounded-full mt-1" />
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
