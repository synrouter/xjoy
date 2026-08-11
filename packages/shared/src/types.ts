/**
 * Xjoy 共享类型定义
 *
 * 这些类型在前后端共享，确保数据模型一致性。
 */

// ── 圣经 ──────────────────────────────────────────────────────────────────────

/** 一节经文 */
export interface Verse {
  id: number;
  book_id: number;
  book_name: string;
  chapter: number;
  verse: number;
  text: string;
  reference: string;
}

/** 一卷书 */
export interface Book {
  id: number;
  name: string;
  sort_order: number;
  testament: 'OT' | 'NT';
  chapters: number;
}

/** 搜索结果 */
export interface SearchResult {
  verse: Verse;
  snippet: string;
  rank: number;
}

/** 交叉引用 */
export interface CrossRef {
  source_reference: string;
  target_reference: string;
}

// ── AI 聊天 ────────────────────────────────────────────────────────────────────

/** 聊天消息 */
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

/** AI 聊天响应 */
export interface ChatResponse {
  answer: string;
  references: ChatReference[];
  model: string;
  usage: Record<string, unknown>;
}

/** 经文引用 */
export interface ChatReference {
  reference: string;
  text: string;
  book_name: string;
  chapter: number;
  verse: number;
}

// ── 统计 ──────────────────────────────────────────────────────────────────────

export interface Stats {
  books: number;
  verses: number;
  ot_verses: number;
  nt_verses: number;
  cross_references: number;
}

// ── 用户数据 ──────────────────────────────────────────────────────────────────

/** 阅读进度 */
export interface ReadingProgress {
  book_name: string;
  chapters_read: number;
  total_chapters: number;
  last_read_at: string;
}

/** 书签 */
export interface Bookmark {
  id: string;
  reference: string;
  book_name: string;
  chapter: number;
  verse: number;
  text: string;
  note?: string;
  created_at: string;
}

/** 反馈 */
export interface Feedback {
  id: string;
  category: 'ai_chat' | 'reading' | 'overall' | 'feature' | 'bug' | 'other';
  rating?: number;
  message: string;
  contact?: string;
  created_at: string;
}

/** 笔记 */
export interface Note {
  id: string;
  reference: string;
  book_name: string;
  chapter: number;
  verse: number;
  content: string;
  created_at: string;
  updated_at: string;
}
