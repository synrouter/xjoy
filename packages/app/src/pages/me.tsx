/**
 * Me 页面 — 用户个人中心
 *
 * 展示阅读进度、笔记、书签等真实统计数据。
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { fetchUserStats, fetchProgress } from '@/lib/api';
import type { ReadingProgress } from '@xjoy/shared';
import PageHeader from '@/components/ui/PageHeader';

interface UserStats {
  notes: number;
  bookmarks: number;
  books_started: number;
  total_chapters_read: number;
}

export default function MePage() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [progress, setProgress] = useState<ReadingProgress[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchUserStats().catch(() => null),
      fetchProgress().catch(() => []),
    ]).then(([s, p]) => {
      if (s) setStats(s);
      setProgress(p);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Me" />

      <div className="flex-1 overflow-y-auto px-5 pb-6 space-y-4">
        {/* 灵修统计 */}
        <div className="bg-white border border-parchment-200 rounded-2xl p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-parchment-400 mb-3">
            Time Connected With God
          </h2>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <p className="text-2xl font-semibold text-parchment-700">
                {loading ? '—' : stats?.total_chapters_read ?? 0}
              </p>
              <p className="text-[10px] text-parchment-400 mt-0.5">
                Chapters Read
              </p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-parchment-700">
                {loading ? '—' : stats?.books_started ?? 0}
              </p>
              <p className="text-[10px] text-parchment-400 mt-0.5">
                Books Started
              </p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-parchment-700">
                {loading ? '—' : '66'}
              </p>
              <p className="text-[10px] text-parchment-400 mt-0.5">
                Total Books
              </p>
            </div>
          </div>
        </div>

        {/* 信仰成就 */}
        <div className="bg-white border border-parchment-200 rounded-2xl p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-parchment-400 mb-3">
            Faith Achievement
          </h2>
          <div className="grid grid-cols-2 gap-3">
            <Link
              href="/study/notes"
              className="flex items-center justify-between bg-parchment-50 rounded-lg px-3 py-2.5 hover:bg-parchment-100 transition-colors active:scale-95"
            >
              <span className="text-xs text-parchment-600">Notes</span>
              <span className="text-sm font-semibold text-parchment-500">
                {loading ? '—' : stats?.notes ?? 0}
              </span>
            </Link>
            <Link
              href="/study/bookmarks"
              className="flex items-center justify-between bg-parchment-50 rounded-lg px-3 py-2.5 hover:bg-parchment-100 transition-colors active:scale-95"
            >
              <span className="text-xs text-parchment-600">Bookmarks</span>
              <span className="text-sm font-semibold text-parchment-500">
                {loading ? '—' : stats?.bookmarks ?? 0}
              </span>
            </Link>
            <div className="flex items-center justify-between bg-parchment-50 rounded-lg px-3 py-2.5">
              <span className="text-xs text-parchment-600">Highlights</span>
              <span className="text-sm font-semibold text-parchment-400">—</span>
            </div>
            <div className="flex items-center justify-between bg-parchment-50 rounded-lg px-3 py-2.5">
              <span className="text-xs text-parchment-600">Favorites</span>
              <span className="text-sm font-semibold text-parchment-400">—</span>
            </div>
          </div>
        </div>

        {/* 读经进度 */}
        <div className="bg-white border border-parchment-200 rounded-2xl p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-parchment-400 mb-3">
            Bible Study Progress
          </h2>
          {progress.length > 0 ? (
            <div className="space-y-2">
              {progress.slice(0, 5).map((p) => (
                <Link
                  key={p.book_name}
                  href={`/bible/${encodeURIComponent(p.book_name)}/${Math.max(1, p.chapters_read)}`}
                  className="flex items-center justify-between bg-parchment-50 rounded-lg px-3 py-2.5 hover:bg-parchment-100 transition-colors"
                >
                  <span className="text-sm text-parchment-700 font-medium">
                    {p.book_name}
                  </span>
                  <span className="text-xs text-parchment-400">
                    {p.chapters_read}/{p.total_chapters} ch.
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <Link
              href="/bible"
              className="block text-center py-3 text-sm text-parchment-500 hover:text-parchment-700 transition-colors bg-parchment-50 rounded-lg"
            >
              {loading ? '加载中...' : 'Start reading →'}
            </Link>
          )}
        </div>

        {/* 设置 */}
        <div className="space-y-0.5">
          {[
            { label: 'Data Sync', detail: 'Sync across devices' },
            { label: 'Reading Reminders', detail: 'Set daily reminders' },
            { label: 'Appearance', detail: 'Font size & theme' },
          ].map((item) => (
            <div
              key={item.label}
              className="flex items-center justify-between bg-white border border-parchment-200 rounded-xl px-4 py-3"
            >
              <span className="text-sm text-parchment-700">{item.label}</span>
              <span className="text-xs text-parchment-400">{item.detail}</span>
            </div>
          ))}
          <Link
            href="/feedback"
            className="flex items-center justify-between bg-white border border-parchment-200 rounded-xl px-4 py-3 hover:bg-parchment-50 transition-colors active:scale-[0.98]"
          >
            <span className="text-sm text-parchment-700">Send Feedback</span>
            <span className="text-xs text-parchment-500">→</span>
          </Link>
          <div
            className="flex items-center justify-between bg-white border border-parchment-200 rounded-xl px-4 py-3"
          >
            <span className="text-sm text-parchment-700">About</span>
            <span className="text-xs text-parchment-400">Xjoy v0.1.0</span>
          </div>
        </div>

        <p className="text-center text-[10px] text-parchment-400 pt-2 pb-4">
          Xjoy v0.1.0 · AI-Powered KJV Bible
        </p>
      </div>
    </div>
  );
}
