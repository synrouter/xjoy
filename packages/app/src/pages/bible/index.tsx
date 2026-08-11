/**
 * 书卷选择页面
 *
 * 展示旧约/新约分区的书卷网格，每卷显示章节数。
 * 参考截图中的"Choose a book"选择器。
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import type { Book } from '@xjoy/shared';
import { fetchBooks } from '@/lib/api';
import PageHeader from '@/components/ui/PageHeader';

interface GroupedBooks {
  OT: Book[];
  NT: Book[];
}

export default function BibleBooksPage() {
  const [books, setBooks] = useState<GroupedBooks | null>(null);
  const [testament, setTestament] = useState<'OT' | 'NT'>('OT');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBooks()
      .then((allBooks) => {
        const grouped: GroupedBooks = { OT: [], NT: [] };
        allBooks.forEach((b) => {
          grouped[b.testament].push(b);
        });
        setBooks(grouped);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-parchment-400 text-sm">加载书卷列表...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-500 text-sm">加载失败: {error}</p>
      </div>
    );
  }

  const current = books?.[testament] || [];

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Bible" subtitle="Choose a book" />

      {/* 旧约/新约切换 */}
      <div className="shrink-0 px-5 pb-3">
        <div className="flex bg-parchment-100 rounded-lg p-1">
          {(['OT', 'NT'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTestament(t)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                testament === t
                  ? 'bg-white text-parchment-700 shadow-sm'
                  : 'text-parchment-400 hover:text-parchment-500'
              }`}
            >
              {t === 'OT' ? '旧约' : '新约'}
            </button>
          ))}
        </div>
      </div>

      {/* 书卷网格 */}
      <div className="flex-1 overflow-y-auto px-5 pb-6">
        <div className="grid grid-cols-3 gap-3">
          {current.map((book) => (
            <Link
              key={book.id}
              href={`/bible/${encodeURIComponent(book.name)}`}
              className="flex flex-col items-center justify-center bg-white border border-parchment-200 rounded-xl px-3 py-4 text-center hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
            >
              <span className="text-sm font-semibold text-parchment-700 leading-tight">
                {book.name}
              </span>
              <span className="text-[10px] text-parchment-400 mt-1">
                {book.chapters} ch
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
