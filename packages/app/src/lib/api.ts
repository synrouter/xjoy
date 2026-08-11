/**
 * Xjoy API 客户端
 *
 * 与 Python FastAPI 后端通信的 TypeScript 客户端。
 * 在无后端（GitHub Pages 静态部署）时自动降级到本地数据。
 *
 * 模式检测：
 * - 设置了有效的 NEXT_PUBLIC_API_URL → 远程 API 模式
 * - 未设置或使用默认值 → 静态模式（本地数据 + localStorage）
 */

import type {
  Verse,
  Book,
  SearchResult,
  ChatResponse,
  Stats,
  Note,
  Bookmark,
  ReadingProgress,
  Feedback,
} from '@xjoy/shared';

// ── 模式检测 ─────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

/** 是否为静态模式（无后端） */
const STATIC_MODE =
  !API_BASE ||
  API_BASE === '/api' ||
  API_BASE.includes('placeholder') ||
  API_BASE.includes('railway.app'); // Railway 部署尚未就绪时视为静态模式

// ── 懒加载静态模块（仅在静态模式下导入）─────────────────────────────────────

async function getBibleData() {
  const mod = await import('./bible-data');
  return {
    getBooks: mod.getBooks,
    getVerse: mod.getVerse,
    getChapter: mod.getChapter,
    searchBibleLocal: mod.searchBibleLocal,
    getStats: mod.getStats,
    getCrossRefs: mod.getCrossRefs,
  };
}

async function getUserDataLocal() {
  const mod = await import('./user-data-local');
  return {
    getLocalNotes: mod.getLocalNotes,
    createLocalNote: mod.createLocalNote,
    updateLocalNote: mod.updateLocalNote,
    deleteLocalNote: mod.deleteLocalNote,
    getLocalBookmarks: mod.getLocalBookmarks,
    createLocalBookmark: mod.createLocalBookmark,
    deleteLocalBookmark: mod.deleteLocalBookmark,
    checkLocalBookmark: mod.checkLocalBookmark,
    getLocalProgress: mod.getLocalProgress,
    updateLocalProgress: mod.updateLocalProgress,
    getLocalUserStats: mod.getLocalUserStats,
    saveLocalFeedback: mod.saveLocalFeedback,
  };
}

// ── API 函数 ─────────────────────────────────────────────────────────────────

export async function fetchBooks(): Promise<Book[]> {
  if (STATIC_MODE) {
    const { getBooks } = await getBibleData();
    return getBooks();
  }
  const res = await fetch(`${API_BASE}/bible/books`);
  if (!res.ok) throw new Error(`获取书卷列表失败: ${res.status}`);
  return res.json();
}

export async function fetchVerse(reference: string): Promise<Verse> {
  if (STATIC_MODE) {
    const { getVerse } = await getBibleData();
    return getVerse(reference);
  }
  const res = await fetch(
    `${API_BASE}/bible/verses/${encodeURIComponent(reference)}`
  );
  if (!res.ok) throw new Error(`经文未找到: ${reference}`);
  return res.json();
}

export async function fetchChapter(
  book: string,
  chapter: number
): Promise<Verse[]> {
  if (STATIC_MODE) {
    const { getChapter } = await getBibleData();
    return getChapter(book, chapter);
  }
  const res = await fetch(
    `${API_BASE}/bible/chapters/${encodeURIComponent(book)}/${chapter}`
  );
  if (!res.ok) throw new Error(`章节未找到: ${book} ${chapter}`);
  return res.json();
}

export async function searchBible(
  query: string,
  options?: { limit?: number; testament?: string; book?: string }
): Promise<SearchResult[]> {
  if (STATIC_MODE) {
    const { searchBibleLocal } = await getBibleData();
    return searchBibleLocal(query, options);
  }
  const params = new URLSearchParams({ q: query });
  if (options?.limit) params.set('limit', String(options.limit));
  if (options?.testament) params.set('testament', options.testament);
  if (options?.book) params.set('book', options.book);

  const res = await fetch(`${API_BASE}/bible/search?${params}`);
  if (!res.ok) throw new Error(`搜索失败: ${res.status}`);
  return res.json();
}

export async function sendChatMessage(
  question: string,
  history?: { role: string; content: string }[]
): Promise<ChatResponse> {
  if (STATIC_MODE) {
    // 静态模式下 AI 聊天不可用 — 返回提示消息
    return {
      answer:
        'AI 对话功能需要后端服务支持，当前为静态部署模式。\n\n' +
        '您仍然可以浏览和搜索经文、查看笔记和书签、追踪阅读进度。\n\n' +
        '完整功能将在后端服务部署后恢复。',
      references: [],
      model: 'static-mode',
      usage: {},
    };
  }
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history: history || [] }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      (err as { detail?: string }).detail || `聊天请求失败: ${res.status}`
    );
  }
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  if (STATIC_MODE) {
    const { getStats } = await getBibleData();
    return getStats();
  }
  const res = await fetch(`${API_BASE}/bible/stats`);
  if (!res.ok) throw new Error(`获取统计失败: ${res.status}`);
  return res.json();
}

export async function fetchCrossRefs(
  reference: string,
  limit?: number
): Promise<{ target_reference: string }[]> {
  if (STATIC_MODE) {
    const { getCrossRefs } = await getBibleData();
    return getCrossRefs(reference, limit);
  }
  const params = limit ? `?limit=${limit}` : '';
  const res = await fetch(
    `${API_BASE}/bible/crossrefs/${encodeURIComponent(reference)}${params}`
  );
  if (!res.ok) throw new Error(`交叉引用未找到: ${reference}`);
  return res.json();
}

// 重新导出类型
export type { Verse, Book, SearchResult, ChatResponse, Stats, Note, Bookmark, ReadingProgress, Feedback };

// ── 用户数据 API ─────────────────────────────────────────────────────────────

// Notes
export async function fetchNotes(params?: {
  book_name?: string;
  chapter?: number;
  limit?: number;
  offset?: number;
}): Promise<Note[]> {
  if (STATIC_MODE) {
    const { getLocalNotes } = await getUserDataLocal();
    return getLocalNotes(params);
  }
  const searchParams = new URLSearchParams();
  if (params?.book_name) searchParams.set('book_name', params.book_name);
  if (params?.chapter) searchParams.set('chapter', String(params.chapter));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  const qs = searchParams.toString();
  const res = await fetch(`${API_BASE}/notes${qs ? `?${qs}` : ''}`);
  if (!res.ok) throw new Error(`获取笔记失败: ${res.status}`);
  return res.json();
}

export async function createNote(data: {
  reference: string;
  content: string;
  book_name: string;
  chapter: number;
  verse: number;
}): Promise<Note> {
  if (STATIC_MODE) {
    const { createLocalNote } = await getUserDataLocal();
    return createLocalNote(data);
  }
  const res = await fetch(`${API_BASE}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`创建笔记失败: ${res.status}`);
  return res.json();
}

export async function updateNote(id: string, content: string): Promise<Note> {
  if (STATIC_MODE) {
    const { updateLocalNote } = await getUserDataLocal();
    return updateLocalNote(id, content);
  }
  const res = await fetch(`${API_BASE}/notes/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(`更新笔记失败: ${res.status}`);
  return res.json();
}

export async function deleteNote(id: string): Promise<void> {
  if (STATIC_MODE) {
    const { deleteLocalNote } = await getUserDataLocal();
    return deleteLocalNote(id);
  }
  const res = await fetch(`${API_BASE}/notes/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`删除笔记失败: ${res.status}`);
}

// Bookmarks
export async function fetchBookmarks(params?: {
  book_name?: string;
  limit?: number;
  offset?: number;
}): Promise<Bookmark[]> {
  if (STATIC_MODE) {
    const { getLocalBookmarks } = await getUserDataLocal();
    return getLocalBookmarks(params);
  }
  const searchParams = new URLSearchParams();
  if (params?.book_name) searchParams.set('book_name', params.book_name);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  const qs = searchParams.toString();
  const res = await fetch(`${API_BASE}/bookmarks${qs ? `?${qs}` : ''}`);
  if (!res.ok) throw new Error(`获取书签失败: ${res.status}`);
  return res.json();
}

export async function createBookmark(data: {
  reference: string;
  book_name: string;
  chapter: number;
  verse: number;
  text: string;
  note?: string;
}): Promise<Bookmark> {
  if (STATIC_MODE) {
    const { createLocalBookmark } = await getUserDataLocal();
    return createLocalBookmark(data);
  }
  const res = await fetch(`${API_BASE}/bookmarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`创建书签失败: ${res.status}`);
  return res.json();
}

export async function deleteBookmark(id: string): Promise<void> {
  if (STATIC_MODE) {
    const { deleteLocalBookmark } = await getUserDataLocal();
    return deleteLocalBookmark(id);
  }
  const res = await fetch(`${API_BASE}/bookmarks/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`删除书签失败: ${res.status}`);
}

export async function checkBookmark(
  book_name: string,
  chapter: number,
  verse: number
): Promise<{ bookmarked: boolean; bookmark_id: string | null }> {
  if (STATIC_MODE) {
    const { checkLocalBookmark } = await getUserDataLocal();
    return checkLocalBookmark(book_name, chapter, verse);
  }
  const params = new URLSearchParams({
    book_name,
    chapter: String(chapter),
    verse: String(verse),
  });
  const res = await fetch(`${API_BASE}/bookmarks/check?${params}`);
  if (!res.ok) throw new Error(`检查书签失败: ${res.status}`);
  return res.json();
}

// Reading Progress
export async function fetchProgress(
  book_name?: string
): Promise<ReadingProgress[]> {
  if (STATIC_MODE) {
    const { getLocalProgress } = await getUserDataLocal();
    return getLocalProgress(book_name);
  }
  const params = book_name
    ? `?book_name=${encodeURIComponent(book_name)}`
    : '';
  const res = await fetch(`${API_BASE}/progress${params}`);
  if (!res.ok) throw new Error(`获取进度失败: ${res.status}`);
  return res.json();
}

export async function updateProgress(
  book_name: string,
  chapter: number
): Promise<ReadingProgress> {
  if (STATIC_MODE) {
    const { updateLocalProgress } = await getUserDataLocal();
    return updateLocalProgress(book_name, chapter);
  }
  const res = await fetch(`${API_BASE}/progress`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ book_name, chapter }),
  });
  if (!res.ok) throw new Error(`更新进度失败: ${res.status}`);
  return res.json();
}

// User Stats
export async function fetchUserStats(): Promise<{
  notes: number;
  bookmarks: number;
  books_started: number;
  total_chapters_read: number;
}> {
  if (STATIC_MODE) {
    const { getLocalUserStats } = await getUserDataLocal();
    return getLocalUserStats();
  }
  const res = await fetch(`${API_BASE}/user/stats`);
  if (!res.ok) throw new Error(`获取统计失败: ${res.status}`);
  return res.json();
}

// Feedback
export async function submitFeedback(data: {
  category: string;
  rating?: number;
  message: string;
  contact?: string;
}): Promise<Feedback> {
  if (STATIC_MODE) {
    const { saveLocalFeedback } = await getUserDataLocal();
    return saveLocalFeedback(data);
  }
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`提交反馈失败: ${res.status}`);
  return res.json();
}
