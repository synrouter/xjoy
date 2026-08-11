/**
 * 搜索页面
 *
 * KJV 全文搜索，支持关键字查找经文。
 */

import { useState } from 'react';
import Link from 'next/link';
import type { SearchResult } from '@xjoy/shared';
import { searchBible } from '@/lib/api';
import PageHeader from '@/components/ui/PageHeader';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    setSearched(true);
    try {
      const res = await searchBible(q, { limit: 30 });
      setResults(res);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Search" />

      {/* 搜索栏 */}
      <div className="shrink-0 px-5 pb-3">
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search the Bible..."
            className="flex-1 bg-parchment-50 border border-parchment-200 rounded-xl px-4 py-2.5 text-sm text-parchment-800 placeholder:text-parchment-400 focus:outline-none focus:border-parchment-500 focus:ring-2 focus:ring-parchment-500/10"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2.5 bg-parchment-700 text-white text-sm font-medium rounded-xl hover:bg-parchment-800 disabled:opacity-40 transition-colors shrink-0"
          >
            {loading ? '...' : '搜索'}
          </button>
        </form>
      </div>

      {/* 搜索结果 */}
      <div className="flex-1 overflow-y-auto px-5 pb-6">
        {!searched && (
          <div className="flex flex-col items-center justify-center h-40 text-parchment-400">
            <span className="text-4xl mb-3">🔍</span>
            <p className="text-sm">输入关键字搜索 KJV 经文</p>
          </div>
        )}

        {searched && !loading && results.length === 0 && (
          <div className="flex flex-col items-center justify-center h-40 text-parchment-400">
            <p className="text-sm">未找到与 &ldquo;{query}&rdquo; 相关的经文</p>
          </div>
        )}

        {results.map((r, i) => (
          <Link
            key={i}
            href={`/bible/${encodeURIComponent(r.verse.book_name)}/${r.verse.chapter}#v${r.verse.verse}`}
            className="block bg-white border border-parchment-200 rounded-xl px-4 py-3 mb-2 hover:border-parchment-400 hover:shadow-sm transition-all"
          >
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-xs font-semibold text-parchment-600">
                {r.verse.reference}
              </span>
            </div>
            <p
              className="text-sm text-parchment-700 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: r.snippet.replace(
                  /\*\*(.*?)\*\*/g,
                  '<mark class="bg-yellow-100 text-parchment-900 rounded px-0.5">$1</mark>'
                ),
              }}
            />
          </Link>
        ))}
      </div>
    </div>
  );
}
