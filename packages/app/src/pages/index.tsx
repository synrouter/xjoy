/**
 * Today 页面 — 首页
 *
 * 每日经文卡片 + Verse of the Day
 * 参考截图中的 Today Tab 布局。
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import type { Verse } from '@xjoy/shared';
import { fetchVerse } from '@/lib/api';
import PageHeader from '@/components/ui/PageHeader';

// 一些推荐的每日经文参考
const DAILY_VERSES = [
  'John 3:16',
  'Psalm 23:1',
  'Philippians 4:13',
  'Proverbs 3:5-6',
  'Isaiah 41:10',
  'Romans 8:28',
  'Jeremiah 29:11',
  'Matthew 6:33',
];

function getDailyVerseRef(): string {
  const today = new Date();
  const dayOfYear = Math.floor(
    (today.getTime() - new Date(today.getFullYear(), 0, 0).getTime()) /
      86400000
  );
  return DAILY_VERSES[dayOfYear % DAILY_VERSES.length];
}

export default function TodayPage() {
  const [verse, setVerse] = useState<Verse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ref = getDailyVerseRef();
    fetchVerse(ref)
      .then(setVerse)
      .catch(() => setVerse(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Today"
        subtitle={new Date().toLocaleDateString('zh-CN', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          weekday: 'long',
        })}
      />

      <div className="flex-1 overflow-y-auto px-5 pb-6 space-y-5">
        {/* 每日经文卡片 */}
        <div className="bg-gradient-to-br from-parchment-100 to-parchment-200 rounded-2xl p-6 border border-parchment-300">
          <h2 className="text-[10px] font-semibold uppercase tracking-widest text-parchment-500 mb-3">
            Verse of the Day
          </h2>
          {loading ? (
            <p className="text-parchment-400 text-sm">加载中...</p>
          ) : verse ? (
            <div>
              <p className="text-lg font-serif text-parchment-800 leading-relaxed italic mb-3">
                &ldquo;{verse.text}&rdquo;
              </p>
              <p className="text-sm font-semibold text-parchment-600">
                — {verse.reference}
              </p>
              <Link
                href={`/bible/${encodeURIComponent(verse.book_name)}/${verse.chapter}`}
                className="inline-block mt-3 text-xs text-parchment-500 hover:text-parchment-700 underline underline-offset-2"
              >
                Read in context →
              </Link>
            </div>
          ) : (
            <p className="text-parchment-500 text-sm">今日经文加载失败</p>
          )}
        </div>

        {/* 快捷入口 */}
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/bible"
            className="flex flex-col items-center justify-center bg-white border border-parchment-200 rounded-xl px-4 py-5 text-center hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
          >
            <span className="text-2xl mb-2">📖</span>
            <span className="text-sm font-medium text-parchment-700">
              Read Bible
            </span>
            <span className="text-[10px] text-parchment-400 mt-0.5">
              KJV Scripture
            </span>
          </Link>

          <Link
            href="/chat"
            className="flex flex-col items-center justify-center bg-white border border-parchment-200 rounded-xl px-4 py-5 text-center hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
          >
            <span className="text-2xl mb-2">💬</span>
            <span className="text-sm font-medium text-parchment-700">
              AI Chat
            </span>
            <span className="text-[10px] text-parchment-400 mt-0.5">
              Study Helper
            </span>
          </Link>

          <Link
            href="/search"
            className="flex flex-col items-center justify-center bg-white border border-parchment-200 rounded-xl px-4 py-5 text-center hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
          >
            <span className="text-2xl mb-2">🔍</span>
            <span className="text-sm font-medium text-parchment-700">
              Search
            </span>
            <span className="text-[10px] text-parchment-400 mt-0.5">
              Find verses
            </span>
          </Link>

          <Link
            href="/bible/Psalms/23"
            className="flex flex-col items-center justify-center bg-white border border-parchment-200 rounded-xl px-4 py-5 text-center hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
          >
            <span className="text-2xl mb-2">🙏</span>
            <span className="text-sm font-medium text-parchment-700">
              Psalm 23
            </span>
            <span className="text-[10px] text-parchment-400 mt-0.5">
              Start reading
            </span>
          </Link>
        </div>

        {/* 晨祷提醒 */}
        <div className="bg-white border border-parchment-200 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-parchment-700 mb-1">
            Morning Prayer
          </h3>
          <p className="text-xs text-parchment-500 leading-relaxed">
            O Lord, open our eyes to behold wondrous things out of Thy law.
            Guide us this day in Thy truth. Amen.
          </p>
        </div>
      </div>
    </div>
  );
}
