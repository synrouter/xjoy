/**
 * 书签列表页面
 *
 * 展示用户所有书签，支持查看经文和删除。
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import type { Bookmark } from '@xjoy/shared';
import { fetchBookmarks, deleteBookmark } from '@/lib/api';
import PageHeader from '@/components/ui/PageHeader';

export default function BookmarksPage() {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBookmarks({ limit: 100 })
      .then(setBookmarks)
      .catch(() => setBookmarks([]))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteBookmark(id);
      setBookmarks((prev) => prev.filter((b) => b.id !== id));
    } catch {
      // 静默处理
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-parchment-400 text-sm">加载书签中...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Bookmarks"
        subtitle={`${bookmarks.length} ${bookmarks.length === 1 ? 'verse' : 'verses'} saved`}
        bordered
        actions={
          <Link
            href="/study"
            className="text-xs text-parchment-400 hover:text-parchment-600"
          >
            ← Study
          </Link>
        }
      />

      <div className="flex-1 overflow-y-auto">
        {bookmarks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-5 text-center">
            <span className="text-4xl mb-3">🔖</span>
            <p className="text-parchment-600 text-sm font-medium mb-1">
              暂无书签
            </p>
            <p className="text-parchment-400 text-xs leading-relaxed">
              阅读经文时，点击节号即可添加/移除书签。
              <br />
              收藏的经文会在这里集中展示。
            </p>
          </div>
        ) : (
          <div className="divide-y divide-parchment-100">
            {bookmarks.map((bm) => (
              <div key={bm.id} className="px-5 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-parchment-500 mb-1">
                      {bm.reference}
                    </p>
                    <p className="text-sm text-parchment-700 leading-relaxed line-clamp-3 italic">
                      &ldquo;{bm.text}&rdquo;
                    </p>
                    {bm.note && (
                      <p className="text-xs text-parchment-500 mt-1.5 bg-parchment-50 rounded px-2 py-1">
                        📝 {bm.note}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-2">
                      <Link
                        href={`/bible/${encodeURIComponent(bm.book_name)}/${bm.chapter}#v${bm.verse}`}
                        className="text-xs text-parchment-500 hover:text-parchment-700 underline underline-offset-2"
                      >
                        Read in context →
                      </Link>
                      <button
                        onClick={() => handleDelete(bm.id)}
                        className="text-xs text-red-400 hover:text-red-600"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
