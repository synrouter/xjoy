"""
Xjoy 用户数据层

管理笔记、书签、阅读进度的 SQLite 持久化。

当前为单用户模式（无认证），所有数据存储在 user_data.db 中。
未来引入认证后再扩展为多用户。

Usage:
    from xjoy.user_data import UserDataStore

    store = UserDataStore("data/user_data.db")

    # Notes
    note = store.create_note("John 3:16", "God's love...", "John", 3, 16)
    notes = store.list_notes()

    # Bookmarks
    bookmark = store.create_bookmark("John 3:16", "John", 3, 16, "For God so loved...")
    bookmarks = store.list_bookmarks()

    # Reading Progress
    store.update_progress("John", 3)
    progress = store.get_progress()
"""

from __future__ import annotations

import sqlite3
import uuid
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Data Types ───────────────────────────────────────────────────────────────

@dataclass
class Note:
    """一条用户笔记"""
    id: str
    reference: str
    book_name: str
    chapter: int
    verse: int
    content: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reference": self.reference,
            "book_name": self.book_name,
            "chapter": self.chapter,
            "verse": self.verse,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Bookmark:
    """一条书签"""
    id: str
    reference: str
    book_name: str
    chapter: int
    verse: int
    text: str
    note: Optional[str]
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reference": self.reference,
            "book_name": self.book_name,
            "chapter": self.chapter,
            "verse": self.verse,
            "text": self.text,
            "note": self.note,
            "created_at": self.created_at,
        }


@dataclass
class ReadingProgress:
    """某卷书的阅读进度"""
    book_name: str
    chapters_read: int
    total_chapters: int
    last_read_at: str

    def to_dict(self) -> dict:
        return {
            "book_name": self.book_name,
            "chapters_read": self.chapters_read,
            "total_chapters": self.total_chapters,
            "last_read_at": self.last_read_at,
        }


# ── SQL Schema ───────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    reference TEXT NOT NULL,
    book_name TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id TEXT PRIMARY KEY,
    reference TEXT NOT NULL,
    book_name TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    text TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reading_progress (
    book_name TEXT NOT NULL,
    chapters_read INTEGER NOT NULL DEFAULT 1,
    total_chapters INTEGER NOT NULL,
    last_read_at TEXT NOT NULL,
    PRIMARY KEY (book_name)
);

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL CHECK(category IN ('ai_chat','reading','overall','feature','bug','other')),
    rating INTEGER CHECK(rating IS NULL OR (rating >= 1 AND rating <= 5)),
    message TEXT NOT NULL,
    contact TEXT,
    created_at TEXT NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_notes_book ON notes(book_name, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookmarks_book ON bookmarks(book_name, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created ON bookmarks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);
"""


# ── Store ────────────────────────────────────────────────────────────────────

class UserDataStore:
    """
    用户数据存储。

    线程安全（SQLite 写操作序列化）。
    所有数据存储在独立的 SQLite 数据库中。
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        """创建新连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Notes ──────────────────────────────────────────────────────────────

    def create_note(
        self,
        reference: str,
        content: str,
        book_name: str,
        chapter: int,
        verse: int,
    ) -> Note:
        """创建新笔记"""
        now = datetime.now(timezone.utc).isoformat()
        note_id = str(uuid.uuid4())
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO notes (id, reference, book_name, chapter, verse, "
                "content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (note_id, reference, book_name, chapter, verse, content, now, now),
            )
            conn.commit()
            return Note(
                id=note_id,
                reference=reference,
                book_name=book_name,
                chapter=chapter,
                verse=verse,
                content=content,
                created_at=now,
                updated_at=now,
            )
        finally:
            conn.close()

    def get_note(self, note_id: str) -> Optional[Note]:
        """获取单条笔记"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if not row:
                return None
            return Note(**dict(row))
        finally:
            conn.close()

    def list_notes(
        self,
        *,
        book_name: Optional[str] = None,
        chapter: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Note]:
        """列出笔记，支持按书卷和章节过滤"""
        conn = self._connect()
        try:
            conditions = []
            params: list = []
            if book_name:
                conditions.append("book_name = ?")
                params.append(book_name)
            if chapter is not None:
                conditions.append("chapter = ?")
                params.append(chapter)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = (
                f"SELECT * FROM notes {where} "
                f"ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            )
            params.extend([limit, offset])
            rows = conn.execute(sql, params).fetchall()
            return [Note(**dict(r)) for r in rows]
        finally:
            conn.close()

    def update_note(self, note_id: str, content: str) -> Optional[Note]:
        """更新笔记内容"""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
                (content, now, note_id),
            )
            conn.commit()
            if conn.total_changes == 0:
                return None
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            return Note(**dict(row)) if row else None
        finally:
            conn.close()

    def delete_note(self, note_id: str) -> bool:
        """删除笔记，返回是否成功"""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def get_notes_count(self) -> int:
        """获取笔记总数"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM notes").fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def get_notes_for_verse(
        self, book_name: str, chapter: int, verse: int
    ) -> list[Note]:
        """获取某节经文的所有笔记"""
        return self.list_notes(book_name=book_name, chapter=chapter)

    # ── Bookmarks ─────────────────────────────────────────────────────────

    def create_bookmark(
        self,
        reference: str,
        book_name: str,
        chapter: int,
        verse: int,
        text: str,
        note: Optional[str] = None,
    ) -> Bookmark:
        """创建书签"""
        now = datetime.now(timezone.utc).isoformat()
        bookmark_id = str(uuid.uuid4())

        # 检查是否已存在同一节经文的书签
        conn = self._connect()
        try:
            existing = conn.execute(
                "SELECT id FROM bookmarks WHERE book_name = ? AND chapter = ? AND verse = ?",
                (book_name, chapter, verse),
            ).fetchone()
            if existing:
                # 更新已有书签
                conn.execute(
                    "UPDATE bookmarks SET reference = ?, text = ?, note = ?, "
                    "created_at = ? WHERE id = ?",
                    (reference, text, note, now, existing[0]),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT * FROM bookmarks WHERE id = ?", (existing[0],)
                ).fetchone()
                return Bookmark(**dict(row))

            conn.execute(
                "INSERT INTO bookmarks (id, reference, book_name, chapter, verse, "
                "text, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (bookmark_id, reference, book_name, chapter, verse, text, note, now),
            )
            conn.commit()
            return Bookmark(
                id=bookmark_id,
                reference=reference,
                book_name=book_name,
                chapter=chapter,
                verse=verse,
                text=text,
                note=note,
                created_at=now,
            )
        finally:
            conn.close()

    def list_bookmarks(
        self,
        *,
        book_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Bookmark]:
        """列出书签"""
        conn = self._connect()
        try:
            if book_name:
                rows = conn.execute(
                    "SELECT * FROM bookmarks WHERE book_name = ? "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (book_name, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM bookmarks ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            return [Bookmark(**dict(r)) for r in rows]
        finally:
            conn.close()

    def get_bookmark(self, bookmark_id: str) -> Optional[Bookmark]:
        """获取单条书签"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
            ).fetchone()
            if not row:
                return None
            return Bookmark(**dict(row))
        finally:
            conn.close()

    def delete_bookmark(self, bookmark_id: str) -> bool:
        """删除书签（也可按引用删除）"""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def is_bookmarked(
        self, book_name: str, chapter: int, verse: int
    ) -> Optional[str]:
        """检查某节经文是否已收藏，返回书签 ID 或 None"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id FROM bookmarks WHERE book_name = ? AND chapter = ? AND verse = ?",
                (book_name, chapter, verse),
            ).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_bookmarks_count(self) -> int:
        """获取书签总数"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    # ── Reading Progress ──────────────────────────────────────────────────

    def update_progress(
        self, book_name: str, chapter: int, total_chapters: int = 0
    ) -> ReadingProgress:
        """更新某卷书的阅读进度（记录已读到的章节）。

        total_chapters 由调用方从 Bible 数据中获取后传入。
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            existing = conn.execute(
                "SELECT chapters_read, total_chapters FROM reading_progress WHERE book_name = ?",
                (book_name,),
            ).fetchone()

            if existing:
                new_chapters = max(existing[0], chapter)
                new_total = max(existing[1], total_chapters)
                conn.execute(
                    "UPDATE reading_progress SET chapters_read = ?, "
                    "total_chapters = ?, last_read_at = ? WHERE book_name = ?",
                    (new_chapters, new_total, now, book_name),
                )
            else:
                conn.execute(
                    "INSERT INTO reading_progress "
                    "(book_name, chapters_read, total_chapters, last_read_at) "
                    "VALUES (?, ?, ?, ?)",
                    (book_name, chapter, total_chapters, now),
                )
            conn.commit()

            return ReadingProgress(
                book_name=book_name,
                chapters_read=chapter if not existing else max(existing[0], chapter),
                total_chapters=total_chapters if not existing else max(existing[1], total_chapters),
                last_read_at=now,
            )
        finally:
            conn.close()

    def get_progress(
        self, book_name: Optional[str] = None
    ) -> list[ReadingProgress]:
        """获取阅读进度（可按书卷过滤）"""
        conn = self._connect()
        try:
            if book_name:
                rows = conn.execute(
                    "SELECT * FROM reading_progress WHERE book_name = ?",
                    (book_name,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM reading_progress ORDER BY last_read_at DESC"
                ).fetchall()
            return [ReadingProgress(**dict(r)) for r in rows]
        finally:
            conn.close()

    def get_chapters_read(self, book_name: str) -> int:
        """获取某卷书已读章节数"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT chapters_read FROM reading_progress WHERE book_name = ?",
                (book_name,),
            ).fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    # ── Feedback ─────────────────────────────────────────────────────────

    def create_feedback(
        self,
        category: str,
        message: str,
        rating: Optional[int] = None,
        contact: Optional[str] = None,
    ) -> Feedback:
        """提交用户反馈"""
        now = datetime.now(timezone.utc).isoformat()
        feedback_id = str(uuid.uuid4())
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO feedback (id, category, rating, message, contact, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (feedback_id, category, rating, message, contact, now),
            )
            conn.commit()
            return Feedback(
                id=feedback_id,
                category=category,
                rating=rating,
                message=message,
                contact=contact,
                created_at=now,
            )
        finally:
            conn.close()

    def list_feedback(
        self,
        *,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Feedback]:
        """列出反馈，支持按类别过滤"""
        conn = self._connect()
        try:
            if category:
                rows = conn.execute(
                    "SELECT * FROM feedback WHERE category = ? "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (category, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            return [Feedback(**dict(r)) for r in rows]
        finally:
            conn.close()

    def get_feedback_count(self, category: Optional[str] = None) -> int:
        """获取反馈数量"""
        conn = self._connect()
        try:
            if category:
                row = conn.execute(
                    "SELECT COUNT(*) FROM feedback WHERE category = ?", (category,)
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    # ── Statistics ────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """获取用户数据统计"""
        conn = self._connect()
        try:
            notes_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            bookmarks_count = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
            books_started = conn.execute(
                "SELECT COUNT(*) FROM reading_progress"
            ).fetchone()[0]
            total_chapters_read = conn.execute(
                "SELECT COALESCE(SUM(chapters_read), 0) FROM reading_progress"
            ).fetchone()[0]
            return {
                "notes": notes_count,
                "bookmarks": bookmarks_count,
                "books_started": books_started,
                "total_chapters_read": total_chapters_read,
            }
        finally:
            conn.close()

@dataclass
class Feedback:
    """一条用户反馈"""
    id: str
    category: str          # 'ai_chat' | 'reading' | 'overall' | 'feature' | 'bug'
    rating: Optional[int]  # 1-5 评分（部分类别无评分）
    message: str           # 反馈正文
    contact: Optional[str] # 可选联系方式
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "rating": self.rating,
            "message": self.message,
            "contact": self.contact,
            "created_at": self.created_at,
        }
