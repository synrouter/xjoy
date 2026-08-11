/**
 * Xjoy 本地用户数据存储（localStorage fallback）
 *
 * 在无后端（GitHub Pages 静态部署）时，使用 localStorage 存储用户数据。
 * 支持的存储类型：笔记 (notes)、书签 (bookmarks)、阅读进度 (progress)。
 *
 * 所有操作模仿后端 API 的返回格式，确保前端代码无需修改。
 */

import type { Note, Bookmark, ReadingProgress, Feedback } from '@xjoy/shared';

// ── 存储键 ──────────────────────────────────────────────────────────────────

const KEYS = {
  notes: 'xjoy_notes',
  bookmarks: 'xjoy_bookmarks',
  progress: 'xjoy_progress',
  feedback: 'xjoy_feedback',
} as const;

// ── 工具函数 ────────────────────────────────────────────────────────────────

function generateId(): string {
  return `local_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function readStore<T>(key: string): T[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeStore<T>(key: string, data: T[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.error(`localStorage 写入失败 (${key}):`, e);
  }
}

// ── 笔记 (Notes) ────────────────────────────────────────────────────────────

export function getLocalNotes(params?: {
  book_name?: string;
  chapter?: number;
  limit?: number;
  offset?: number;
}): Note[] {
  let notes = readStore<Note>(KEYS.notes);

  if (params?.book_name) {
    notes = notes.filter((n) => n.book_name === params.book_name);
  }
  if (params?.chapter) {
    notes = notes.filter((n) => n.chapter === params.chapter);
  }

  // 按创建时间倒序
  notes.sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const offset = params?.offset ?? 0;
  const limit = params?.limit ?? notes.length;
  return notes.slice(offset, offset + limit);
}

export function createLocalNote(data: {
  reference: string;
  content: string;
  book_name: string;
  chapter: number;
  verse: number;
}): Note {
  const notes = readStore<Note>(KEYS.notes);
  const now = new Date().toISOString();
  const note: Note = {
    id: generateId(),
    reference: data.reference,
    book_name: data.book_name,
    chapter: data.chapter,
    verse: data.verse,
    content: data.content,
    created_at: now,
    updated_at: now,
  };
  notes.push(note);
  writeStore(KEYS.notes, notes);
  return note;
}

export function updateLocalNote(id: string, content: string): Note {
  const notes = readStore<Note>(KEYS.notes);
  const idx = notes.findIndex((n) => n.id === id);
  if (idx === -1) throw new Error(`笔记未找到: ${id}`);
  notes[idx] = {
    ...notes[idx],
    content,
    updated_at: new Date().toISOString(),
  };
  writeStore(KEYS.notes, notes);
  return notes[idx];
}

export function deleteLocalNote(id: string): void {
  const notes = readStore<Note>(KEYS.notes);
  writeStore(
    KEYS.notes,
    notes.filter((n) => n.id !== id)
  );
}

// ── 书签 (Bookmarks) ────────────────────────────────────────────────────────

export function getLocalBookmarks(params?: {
  book_name?: string;
  limit?: number;
  offset?: number;
}): Bookmark[] {
  let bookmarks = readStore<Bookmark>(KEYS.bookmarks);

  if (params?.book_name) {
    bookmarks = bookmarks.filter((b) => b.book_name === params.book_name);
  }

  bookmarks.sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const offset = params?.offset ?? 0;
  const limit = params?.limit ?? bookmarks.length;
  return bookmarks.slice(offset, offset + limit);
}

export function createLocalBookmark(data: {
  reference: string;
  book_name: string;
  chapter: number;
  verse: number;
  text: string;
  note?: string;
}): Bookmark {
  const bookmarks = readStore<Bookmark>(KEYS.bookmarks);
  const bookmark: Bookmark = {
    id: generateId(),
    reference: data.reference,
    book_name: data.book_name,
    chapter: data.chapter,
    verse: data.verse,
    text: data.text,
    note: data.note,
    created_at: new Date().toISOString(),
  };
  bookmarks.push(bookmark);
  writeStore(KEYS.bookmarks, bookmarks);
  return bookmark;
}

export function deleteLocalBookmark(id: string): void {
  const bookmarks = readStore<Bookmark>(KEYS.bookmarks);
  writeStore(
    KEYS.bookmarks,
    bookmarks.filter((b) => b.id !== id)
  );
}

export function checkLocalBookmark(
  book_name: string,
  chapter: number,
  verse: number
): { bookmarked: boolean; bookmark_id: string | null } {
  const bookmarks = readStore<Bookmark>(KEYS.bookmarks);
  const found = bookmarks.find(
    (b) => b.book_name === book_name && b.chapter === chapter && b.verse === verse
  );
  return {
    bookmarked: !!found,
    bookmark_id: found?.id ?? null,
  };
}

// ── 阅读进度 (Reading Progress) ─────────────────────────────────────────────

export function getLocalProgress(book_name?: string): ReadingProgress[] {
  let progress = readStore<ReadingProgress>(KEYS.progress);

  if (book_name) {
    progress = progress.filter((p) => p.book_name === book_name);
  }

  return progress;
}

export function updateLocalProgress(
  book_name: string,
  chapter: number
): ReadingProgress {
  const progress = readStore<ReadingProgress>(KEYS.progress);
  const idx = progress.findIndex((p) => p.book_name === book_name);

  const now = new Date().toISOString();
  if (idx >= 0) {
    progress[idx] = {
      ...progress[idx],
      chapters_read: Math.max(progress[idx].chapters_read, chapter),
      last_read_at: now,
    };
  } else {
    progress.push({
      book_name,
      chapters_read: chapter,
      total_chapters: 0, // 由调用者设置或忽略
      last_read_at: now,
    });
  }

  writeStore(KEYS.progress, progress);
  return progress.find((p) => p.book_name === book_name)!;
}

// ── 用户统计 ────────────────────────────────────────────────────────────────

export function getLocalUserStats(): {
  notes: number;
  bookmarks: number;
  books_started: number;
  total_chapters_read: number;
} {
  const notes = readStore<Note>(KEYS.notes);
  const bookmarks = readStore<Bookmark>(KEYS.bookmarks);
  const progress = readStore<ReadingProgress>(KEYS.progress);

  return {
    notes: notes.length,
    bookmarks: bookmarks.length,
    books_started: progress.length,
    total_chapters_read: progress.reduce(
      (sum, p) => sum + p.chapters_read,
      0
    ),
  };
}

// ── 反馈 ────────────────────────────────────────────────────────────────────

export function saveLocalFeedback(data: {
  category: string;
  rating?: number;
  message: string;
  contact?: string;
}): Feedback {
  const feedbackList = readStore<Feedback>(KEYS.feedback);
  const feedback: Feedback = {
    id: generateId(),
    category: data.category as Feedback['category'],
    rating: data.rating,
    message: data.message,
    contact: data.contact,
    created_at: new Date().toISOString(),
  };
  feedbackList.push(feedback);
  writeStore(KEYS.feedback, feedbackList);
  return feedback;
}
