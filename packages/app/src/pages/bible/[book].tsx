/**
 * 章节列表页面
 *
 * 展示所选书卷的所有章节，每个章节以数字按钮呈现。
 * 点击进入该章节的经文选读。
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import type { Book } from '@xjoy/shared';
import { fetchBooks } from '@/lib/api';
import { BOOKS } from '@/lib/bible-data';
import PageHeader from '@/components/ui/PageHeader';

export default function BookChaptersPage() {
  const router = useRouter();
  const { book: bookName } = router.query;
  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!bookName) return;
    const name = Array.isArray(bookName) ? bookName[0] : bookName;
    fetchBooks()
      .then((allBooks) => {
        const found = allBooks.find(
          (b) => b.name.toLowerCase() === decodeURIComponent(name).toLowerCase()
        );
        if (found) {
          setBook(found);
        } else {
          setError(`未找到书卷: ${name}`);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [bookName]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-parchment-400 text-sm">加载中...</p>
      </div>
    );
  }

  if (error || !book) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-500 text-sm">{error || '未找到书卷'}</p>
      </div>
    );
  }

  const chapters = Array.from({ length: book.chapters }, (_, i) => i + 1);

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title={book.name}
        subtitle={`${book.testament === 'OT' ? '旧约' : '新约'} · ${book.chapters} 章`}
      />

      {/* 章节网格 */}
      <div className="flex-1 overflow-y-auto px-5 pb-6">
        <div className="grid grid-cols-5 gap-3">
          {chapters.map((ch) => (
            <Link
              key={ch}
              href={`/bible/${encodeURIComponent(book.name)}/${ch}`}
              className="flex items-center justify-center bg-white border border-parchment-200 rounded-xl aspect-square text-parchment-700 font-medium hover:border-parchment-400 hover:shadow-sm transition-all active:scale-95"
            >
              {ch}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── 静态导出：getStaticPaths + getStaticProps ──────────────────────────────

export async function getStaticPaths() {
  const paths = BOOKS.map((b) => ({
    params: { book: b.name },
  }));
  return { paths, fallback: false };
}

export async function getStaticProps({ params }: { params: { book: string } }) {
  return { props: {} };
}
