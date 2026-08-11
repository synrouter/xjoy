/**
 * Study 页面 — 学习工具入口
 *
 * 笔记、书签、Quiz、Jigsaw 等学习功能。
 */

import Link from 'next/link';
import PageHeader from '@/components/ui/PageHeader';

export default function StudyPage() {
  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Study" subtitle="Bible study &amp; tools" />

      <div className="flex-1 overflow-y-auto px-5 pb-6 space-y-4">
        {/* Notes & Bookmarks */}
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/study/notes"
            className="flex flex-col items-center justify-center bg-white border border-parchment-200 rounded-xl px-4 py-5 text-center hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
          >
            <span className="text-2xl mb-2">📝</span>
            <span className="text-sm font-medium text-parchment-700">
              My Notes
            </span>
            <span className="text-[10px] text-parchment-400 mt-0.5">
              Verse journal
            </span>
          </Link>

          <Link
            href="/study/bookmarks"
            className="flex flex-col items-center justify-center bg-white border border-parchment-200 rounded-xl px-4 py-5 text-center hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
          >
            <span className="text-2xl mb-2">🔖</span>
            <span className="text-sm font-medium text-parchment-700">
              Bookmarks
            </span>
            <span className="text-[10px] text-parchment-400 mt-0.5">
              Saved verses
            </span>
          </Link>
        </div>

        {/* Bible Quiz */}
        <div className="bg-white border border-parchment-200 rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">❓</span>
            <div>
              <h2 className="text-sm font-semibold text-parchment-700">
                Bible Quiz
              </h2>
              <p className="text-[10px] text-parchment-400">
                5 multiple-choice questions daily
              </p>
            </div>
          </div>
          <p className="text-xs text-parchment-500 leading-relaxed mb-4">
            Test your knowledge of Scripture with daily quizzes.
            Compete with friends and track your progress.
          </p>
          <button
            disabled
            className="w-full py-2.5 bg-parchment-100 text-parchment-400 text-sm font-medium rounded-xl cursor-not-allowed"
          >
            Coming Soon
          </button>
        </div>

        {/* Weekly Jigsaw */}
        <div className="bg-white border border-parchment-200 rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">🧩</span>
            <div>
              <h2 className="text-sm font-semibold text-parchment-700">
                Weekly Jigsaw
              </h2>
              <p className="text-[10px] text-parchment-400">
                Answer questions → earn puzzle pieces
              </p>
            </div>
          </div>
          <p className="text-xs text-parchment-500 leading-relaxed mb-4">
            Complete 5 daily lessons each week to earn the Jigsaw Trophy.
          </p>
          <button
            disabled
            className="w-full py-2.5 bg-parchment-100 text-parchment-400 text-sm font-medium rounded-xl cursor-not-allowed"
          >
            Coming Soon
          </button>
        </div>

        {/* 学习建议 */}
        <div className="bg-gradient-to-br from-parchment-100 to-parchment-200 rounded-2xl p-5 border border-parchment-300">
          <h2 className="text-sm font-semibold text-parchment-700 mb-2">
            📚 Study Tip
          </h2>
          <p className="text-xs text-parchment-600 leading-relaxed">
            &ldquo;Study to shew thyself approved unto God, a workman that
            needeth not to be ashamed, rightly dividing the word of truth.&rdquo;
          </p>
          <p className="text-[10px] text-parchment-400 mt-2">
            — 2 Timothy 2:15
          </p>
          <Link
            href="/bible/2 Timothy/2"
            className="inline-block mt-2 text-xs text-parchment-500 hover:text-parchment-700 underline underline-offset-2"
          >
            Read in context →
          </Link>
        </div>
      </div>
    </div>
  );
}
