"""
Xjoy FastAPI Server

Serves the Bible API and AI Chat endpoints.
Entry point: python -m xjoy.api  or  uvicorn xjoy.api:app
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .bible import Bible
from .chat import ChatService, ChatMessage
from .user_data import UserDataStore


# ── App Lifecycle ──────────────────────────────────────────────────────────────

bible: Optional[Bible] = None
chat_service: Optional[ChatService] = None
user_store: Optional[UserDataStore] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bible, chat_service, user_store
    db_path = os.environ.get(
        "KJV_DB_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "db" / "data" / "kjv.db"),
    )
    bible = Bible(db_path)
    stats = bible.stats()
    print(f"📖 Xjoy API 服务启动")
    print(f"   数据库: {db_path}")
    print(f"   经文: {stats['verses']:,} 节 | 书卷: {stats['books']} 卷")
    print(f"   交叉引用: {stats['cross_references']:,} 条")

    # 初始化用户数据存储
    user_db_path = os.environ.get(
        "USER_DB_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "db" / "data" / "user_data.db"),
    )
    user_store = UserDataStore(user_db_path)
    user_stats = user_store.stats()
    print(f"📝 用户数据: {user_db_path}")
    print(f"   笔记: {user_stats['notes']} | 书签: {user_stats['bookmarks']}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-20251001")
        chat_service = ChatService(bible, api_key=api_key, model=model)
        print(f"   Claude API: 已配置 ✅ (model: {model})")
    else:
        print(f"   Claude API: 未配置 ⚠️ (聊天功能不可用)")

    yield
    print("📖 Xjoy API 服务关闭")


app = FastAPI(
    title="Xjoy API",
    description="AI-powered KJV Bible",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "bible_loaded": bible is not None,
        "chat_enabled": chat_service is not None,
    }


# ── Bible: Books ───────────────────────────────────────────────────────────────

@app.get("/api/bible/books")
async def list_books(testament: Optional[str] = Query(None, pattern="^(OT|NT)$")):
    """List all books, optionally filtered by testament. Returns array."""
    assert bible is not None
    if testament:
        grouped = bible.books_by_testament()
        return [b.to_dict() for b in grouped[testament]]
    return [b.to_dict() for b in bible.books()]


# ── Bible: Verses ──────────────────────────────────────────────────────────────

@app.get("/api/bible/verses/{ref:path}")
async def get_verse(ref: str):
    """Look up a single verse by reference. e.g. /api/bible/verses/John 3:16"""
    assert bible is not None
    try:
        verse = bible.verse(ref)
        return verse.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Bible: Chapters ────────────────────────────────────────────────────────────

@app.get("/api/bible/chapters/{book_name}/{chapter}")
async def get_chapter(book_name: str, chapter: int):
    """Get all verses in a chapter. Returns array of verses."""
    assert bible is not None
    try:
        verses = bible.chapter(book_name, chapter)
        return [v.to_dict() for v in verses]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Bible: Search ──────────────────────────────────────────────────────────────

@app.get("/api/bible/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    testament: Optional[str] = Query(None, pattern="^(OT|NT)$"),
    book: Optional[str] = Query(None),
):
    """Full-text search across the Bible. Returns array of results."""
    assert bible is not None
    try:
        results = bible.search(q, limit=limit, testament=testament, book=book)
        return [r.to_dict() for r in results]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Bible: Stats ───────────────────────────────────────────────────────────────

@app.get("/api/bible/stats")
async def get_stats():
    """Get database statistics."""
    assert bible is not None
    return bible.stats()


# ── Bible: Books by Testament ────────────────────────────────────────────────────

@app.get("/api/bible/books-by-testament")
async def books_by_testament():
    """Get books grouped by testament. Returns { OT: [...], NT: [...] }."""
    assert bible is not None
    grouped = bible.books_by_testament()
    return {
        "OT": [b.to_dict() for b in grouped["OT"]],
        "NT": [b.to_dict() for b in grouped["NT"]],
    }


# ── Bible: Cross-References ────────────────────────────────────────────────────

@app.get("/api/bible/crossrefs/{ref:path}")
async def get_crossrefs(
    ref: str,
    limit: int = Query(50, ge=1, le=200),
    direction: str = Query("from", pattern="^(from|to)$"),
):
    """Get cross-references for a verse. Returns array."""
    assert bible is not None
    try:
        if direction == "to":
            refs = bible.cross_refs_to(ref, limit=limit)
        else:
            refs = bible.cross_refs(ref, limit=limit)
        return [r.to_dict() for r in refs]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Bible: Range ───────────────────────────────────────────────────────────────

@app.get("/api/bible/range")
async def get_range(
    start: str = Query(..., description="Start reference, e.g. 'John 3:16'"),
    end: str = Query(..., description="End reference, e.g. 'John 3:18'"),
):
    """Get verses in a range."""
    assert bible is not None
    try:
        verses = bible.range(start, end)
        return [v.to_dict() for v in verses]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Chat ───────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: list[dict] = Field(default_factory=list)
    testament: Optional[str] = Field(default=None, pattern="^(OT|NT)$")


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """AI-powered Bible chat with RAG."""
    if chat_service is None:
        raise HTTPException(
            status_code=503,
            detail="Chat is not available. Set ANTHROPIC_API_KEY to enable.",
        )

    history = [ChatMessage(role=m["role"], content=m["content"]) for m in req.history]

    try:
        response = await chat_service.ask(
            req.question,
            conversation_history=history,
            testament=req.testament,
        )
        return response.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ── Notes ──────────────────────────────────────────────────────────────────────

class NoteCreateRequest(BaseModel):
    reference: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=10000)
    book_name: str = Field(..., min_length=1, max_length=50)
    chapter: int = Field(..., ge=1, le=150)
    verse: int = Field(..., ge=1, le=176)


class NoteUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


@app.get("/api/notes")
async def list_notes(
    book_name: Optional[str] = Query(None),
    chapter: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """列出笔记，支持按书卷和章节过滤"""
    assert user_store is not None
    notes = user_store.list_notes(
        book_name=book_name, chapter=chapter, limit=limit, offset=offset
    )
    return [n.to_dict() for n in notes]


@app.post("/api/notes")
async def create_note(req: NoteCreateRequest):
    """创建新笔记"""
    assert user_store is not None
    note = user_store.create_note(
        reference=req.reference,
        content=req.content,
        book_name=req.book_name,
        chapter=req.chapter,
        verse=req.verse,
    )
    return note.to_dict()


@app.get("/api/notes/{note_id}")
async def get_note(note_id: str):
    """获取单条笔记"""
    assert user_store is not None
    note = user_store.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记未找到")
    return note.to_dict()


@app.put("/api/notes/{note_id}")
async def update_note(note_id: str, req: NoteUpdateRequest):
    """更新笔记内容"""
    assert user_store is not None
    note = user_store.update_note(note_id, req.content)
    if not note:
        raise HTTPException(status_code=404, detail="笔记未找到")
    return note.to_dict()


@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: str):
    """删除笔记"""
    assert user_store is not None
    ok = user_store.delete_note(note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="笔记未找到")
    return {"deleted": True}


# ── Bookmarks ─────────────────────────────────────────────────────────────────

class BookmarkCreateRequest(BaseModel):
    reference: str = Field(..., min_length=1, max_length=100)
    book_name: str = Field(..., min_length=1, max_length=50)
    chapter: int = Field(..., ge=1, le=150)
    verse: int = Field(..., ge=1, le=176)
    text: str = Field(..., min_length=1, max_length=2000)
    note: Optional[str] = Field(default=None, max_length=500)


@app.get("/api/bookmarks")
async def list_bookmarks(
    book_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """列出书签"""
    assert user_store is not None
    bookmarks = user_store.list_bookmarks(
        book_name=book_name, limit=limit, offset=offset
    )
    return [b.to_dict() for b in bookmarks]


@app.post("/api/bookmarks")
async def create_bookmark(req: BookmarkCreateRequest):
    """创建或更新书签（同一经文重复收藏会更新而非报错）"""
    assert user_store is not None
    bookmark = user_store.create_bookmark(
        reference=req.reference,
        book_name=req.book_name,
        chapter=req.chapter,
        verse=req.verse,
        text=req.text,
        note=req.note,
    )
    return bookmark.to_dict()


@app.delete("/api/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str):
    """删除书签"""
    assert user_store is not None
    ok = user_store.delete_bookmark(bookmark_id)
    if not ok:
        raise HTTPException(status_code=404, detail="书签未找到")
    return {"deleted": True}


@app.get("/api/bookmarks/check")
async def check_bookmark(
    book_name: str = Query(...),
    chapter: int = Query(...),
    verse: int = Query(...),
):
    """检查某节经文是否已收藏"""
    assert user_store is not None
    bookmark_id = user_store.is_bookmarked(book_name, chapter, verse)
    return {"bookmarked": bookmark_id is not None, "bookmark_id": bookmark_id}


# ── Reading Progress ──────────────────────────────────────────────────────────

class ProgressUpdateRequest(BaseModel):
    book_name: str = Field(..., min_length=1, max_length=50)
    chapter: int = Field(..., ge=1, le=150)


@app.get("/api/progress")
async def get_progress(book_name: Optional[str] = Query(None)):
    """获取阅读进度"""
    assert user_store is not None
    progress_list = user_store.get_progress(book_name=book_name)
    return [p.to_dict() for p in progress_list]


@app.post("/api/progress")
async def update_progress(req: ProgressUpdateRequest):
    """记录阅读进度（自动取已读章节的最大值）"""
    assert user_store is not None
    assert bible is not None
    # 从 Bible 数据中获取该书总章节数
    try:
        book = bible.book(req.book_name)
        total_chapters = book.chapters
    except ValueError:
        total_chapters = 0
    progress = user_store.update_progress(req.book_name, req.chapter, total_chapters)
    return progress.to_dict()


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackSubmitRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=20, pattern="^(ai_chat|reading|overall|feature|bug|other)$")
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    message: str = Field(..., min_length=1, max_length=5000)
    contact: Optional[str] = Field(default=None, max_length=200)


@app.post("/api/feedback")
async def submit_feedback(req: FeedbackSubmitRequest):
    """提交用户反馈"""
    assert user_store is not None
    feedback = user_store.create_feedback(
        category=req.category,
        rating=req.rating,
        message=req.message,
        contact=req.contact,
    )
    return feedback.to_dict()


@app.get("/api/feedback")
async def list_feedback(
    category: Optional[str] = Query(None, pattern="^(ai_chat|reading|overall|feature|bug|other)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """列出反馈"""
    assert user_store is not None
    items = user_store.list_feedback(category=category, limit=limit, offset=offset)
    return [f.to_dict() for f in items]


# ── User Stats ────────────────────────────────────────────────────────────────

@app.get("/api/user/stats")
async def get_user_stats():
    """获取用户数据统计"""
    assert user_store is not None
    return user_store.stats()


# ── Root ───────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return JSONResponse({
        "name": "Xjoy API",
        "description": "AI-Powered KJV Bible — REST API and RAG Chat",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    })


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("xjoy.api:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
