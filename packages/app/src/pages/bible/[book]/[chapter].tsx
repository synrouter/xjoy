/**
 * 章节阅读器
 *
 * 展示整章经文，支持前后章节导航、字号调节、书签和笔记。
 * 进入页面时自动记录阅读进度。
 */

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import type { Verse, Book } from '@xjoy/shared';
import {
  fetchChapter,
  fetchBooks,
  createBookmark,
  deleteBookmark,
  checkBookmark,
  updateProgress,
  createNote,
} from '@/lib/api';
import { BOOKS } from '@/lib/bible-data';
import PageHeader from '@/components/ui/PageHeader';

export default function ChapterReaderPage() {
  const router = useRouter();
  const { book: bookName, chapter: chapterStr } = router.query;
  const [verses, setVerses] = useState<Verse[]>([]);
  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fontSize, setFontSize] = useState<'sm' | 'md' | 'lg'>('md');

  // 书签状态：{ [verse]: bookmark_id | null }
  const [bookmarks, setBookmarks] = useState<Record<number, string | null>>({});
  const [bookmarkLoading, setBookmarkLoading] = useState<Record<number, boolean>>({});

  // 笔记编辑器状态
  const [noteEditor, setNoteEditor] = useState<{
    verse: number;
    content: string;
  } | null>(null);
  const [noteSaving, setNoteSaving] = useState(false);

  const chapter = chapterStr
    ? parseInt(Array.isArray(chapterStr) ? chapterStr[0] : chapterStr, 10)
    : 0;
  const name = bookName
    ? decodeURIComponent(Array.isArray(bookName) ? bookName[0] : bookName)
    : '';

  useEffect(() => {
    if (!name || !chapter) return;

    setLoading(true);
    setError(null);

    Promise.all([fetchChapter(name, chapter), fetchBooks()])
      .then(([verseList, allBooks]) => {
        if (verseList.length === 0) {
          setError('此章节无经文');
          return;
        }
        setVerses(verseList);
        // 切换章节时重置笔记编辑器状态
        setNoteEditor(null);
        const found = allBooks.find(
          (b) => b.name.toLowerCase() === name.toLowerCase()
        );
        setBook(found || null);

        // 记录阅读进度
        updateProgress(name, chapter).catch(() => {});

        // 批量检查所有经文的书签状态
        return Promise.all(
          verseList.map((v) =>
            checkBookmark(name, chapter, v.verse)
              .then((r) => ({ verse: v.verse, id: r.bookmark_id }))
              .catch(() => ({ verse: v.verse, id: null }))
          )
        ).then((results) => {
          const map: Record<number, string | null> = {};
          results.forEach((r) => {
            map[r.verse] = r.id;
          });
          setBookmarks(map);
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [name, chapter]);

  const toggleBookmark = useCallback(
    async (verse: Verse) => {
      const verseNum = verse.verse;
      if (bookmarkLoading[verseNum]) return;

      setBookmarkLoading((prev) => ({ ...prev, [verseNum]: true }));
      try {
        const existingId = bookmarks[verseNum];
        if (existingId) {
          // 取消书签
          await deleteBookmark(existingId);
          setBookmarks((prev) => ({ ...prev, [verseNum]: null }));
        } else {
          // 添加书签
          const result = await createBookmark({
            reference: verse.reference,
            book_name: name,
            chapter,
            verse: verseNum,
            text: verse.text,
          });
          setBookmarks((prev) => ({ ...prev, [verseNum]: result.id }));
        }
      } catch {
        // 静默失败，不影响阅读
      } finally {
        setBookmarkLoading((prev) => ({ ...prev, [verseNum]: false }));
      }
    },
    [bookmarks, bookmarkLoading, name, chapter]
  );

  const handleSaveNote = useCallback(
    async (verse: Verse) => {
      if (!noteEditor || noteSaving) return;
      const content = noteEditor.content.trim();
      if (!content) {
        setNoteEditor(null);
        return;
      }
      setNoteSaving(true);
      try {
        await createNote({
          reference: verse.reference,
          content,
          book_name: name,
          chapter,
          verse: verse.verse,
        });
        setNoteEditor(null);
      } catch {
        // 静默失败
      } finally {
        setNoteSaving(false);
      }
    },
    [noteEditor, noteSaving, name, chapter]
  );

  const fontSizeClass = {
    sm: 'text-sm leading-relaxed',
    md: 'text-[15px] leading-relaxed',
    lg: 'text-lg leading-relaxed',
  }[fontSize];

  const hasPrev = book ? chapter > 1 : false;
  const hasNext = book ? chapter < book.chapters : false;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-parchment-400 text-sm">加载经文中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full px-5">
        <div className="text-center">
          <p className="text-red-500 text-sm mb-3">{error}</p>
          <button
            onClick={() => router.back()}
            className="text-parchment-500 text-sm underline"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title={book?.name || name}
        subtitle={`Chapter ${chapter}${book?.chapters ? ` / ${book.chapters}` : ''}`}
        bordered
        actions={
          <div className="flex items-center gap-1 bg-parchment-50 border border-parchment-200 rounded-xl p-0.5">
            {(['sm', 'md', 'lg'] as const).map((size) => (
              <button
                key={size}
                onClick={() => setFontSize(size)}
                className={`px-2 py-1 text-xs rounded-lg transition-colors ${
                  fontSize === size
                    ? 'bg-white text-parchment-700 shadow-sm font-medium'
                    : 'text-parchment-400'
                }`}
              >
                {size === 'sm' ? '小' : size === 'md' ? '中' : '大'}
              </button>
            ))}
          </div>
        }
      />

      {/* 经文正文 */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className={fontSizeClass}>
          {verses.map((verse) => {
            const isBookmarked = !!bookmarks[verse.verse];
            const isBMKLoading = !!bookmarkLoading[verse.verse];
            const isEditingNote = noteEditor?.verse === verse.verse;

            return (
              <div
                key={verse.id}
                id={`v${verse.verse}`}
              >
                <div className="group flex mb-1.5">
                  {/* 节号 + 书签按钮 */}
                  <button
                    onClick={() => toggleBookmark(verse)}
                    disabled={isBMKLoading}
                    className={`shrink-0 w-7 text-right mr-1.5 select-none transition-colors ${
                      isBookmarked
                        ? 'text-amber-500'
                        : 'text-parchment-400 group-hover:text-amber-400'
                    }`}
                    title={isBookmarked ? '取消书签' : '添加书签'}
                  >
                    <sup className="text-[10px] font-medium">
                      {isBookmarked ? '🔖' : verse.verse}
                    </sup>
                  </button>

                  {/* 笔记按钮 — hover 时显示 */}
                  <button
                    onClick={() =>
                      setNoteEditor(
                        isEditingNote
                          ? null
                          : { verse: verse.verse, content: '' }
                      )
                    }
                    className={`shrink-0 mr-1.5 select-none transition-all ${
                      isEditingNote
                        ? 'opacity-100 text-accent-500'
                        : 'opacity-0 group-hover:opacity-100 text-parchment-300 hover:text-accent-400'
                    }`}
                    title="添加笔记"
                  >
                    <sup className="text-[10px]">📝</sup>
                  </button>

                  <span
                    className={`text-parchment-800 flex-1 ${
                      isBookmarked ? 'bg-amber-50 -mx-1 px-1 rounded' : ''
                    }`}
                  >
                    {verse.text}
                  </span>
                </div>

                {/* 内联笔记编辑器 */}
                {isEditingNote && (
                  <div className="ml-[3.75rem] mb-2 mr-1 bg-accent-50 border border-accent-200 rounded-lg p-3">
                    <textarea
                      value={noteEditor!.content}
                      onChange={(e) =>
                        setNoteEditor({
                          verse: verse.verse,
                          content: e.target.value,
                        })
                      }
                      placeholder={`在 ${verse.reference} 上写下你的心得...`}
                      className="w-full bg-white border border-accent-200 rounded-lg p-2.5 text-sm text-parchment-700 placeholder-parchment-300 focus:outline-none focus:border-accent-400 focus:ring-2 focus:ring-accent-500/10 resize-none"
                      rows={3}
                      autoFocus
                    />
                    <div className="flex items-center justify-end gap-2 mt-2">
                      <button
                        onClick={() => setNoteEditor(null)}
                        className="text-xs text-parchment-400 hover:text-parchment-600 px-2 py-1"
                      >
                        取消
                      </button>
                      <button
                        onClick={() => handleSaveNote(verse)}
                        disabled={noteSaving || !noteEditor!.content.trim()}
                        className="text-xs bg-accent-500 text-white px-3 py-1.5 rounded-lg hover:bg-accent-600 disabled:opacity-40 transition-colors font-medium"
                      >
                        {noteSaving ? '保存中...' : '保存笔记'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 底部导航栏 */}
      <footer className="shrink-0 border-t border-parchment-200 bg-white px-5 py-3">
        <div className="flex items-center justify-between">
          {hasPrev ? (
            <Link
              href={`/bible/${encodeURIComponent(name)}/${chapter - 1}`}
              className="flex items-center gap-1 text-sm text-parchment-600 hover:text-parchment-800 transition-colors px-3 py-2 rounded-lg hover:bg-parchment-50"
            >
              ← Chapter {chapter - 1}
            </Link>
          ) : (
            <div />
          )}

          <Link
            href={`/bible/${encodeURIComponent(name)}`}
            className="text-xs text-parchment-400 hover:text-parchment-600 px-2 py-1"
          >
            All Chapters
          </Link>

          {hasNext ? (
            <Link
              href={`/bible/${encodeURIComponent(name)}/${chapter + 1}`}
              className="flex items-center gap-1 text-sm text-parchment-600 hover:text-parchment-800 transition-colors px-3 py-2 rounded-lg hover:bg-parchment-50"
            >
              Chapter {chapter + 1} →
            </Link>
          ) : (
            <div />
          )}
        </div>
      </footer>
    </div>
  );
}

// ── 静态导出：getStaticPaths + getStaticProps ──────────────────────────────

export async function getStaticPaths() {
  const paths: { params: { book: string; chapter: string } }[] = [];
  for (const book of BOOKS) {
    for (let ch = 1; ch <= book.chapters; ch++) {
      paths.push({
        params: { book: book.name, chapter: String(ch) },
      });
    }
  }
  return { paths, fallback: false };
}

export async function getStaticProps({
  params,
}: {
  params: { book: string; chapter: string };
}) {
  return { props: {} };
}
