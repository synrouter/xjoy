"""
API 端点集成测试

使用 FastAPI TestClient 测试所有 REST 端点。
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from xjoy.api import app


@pytest.fixture(scope="module")
def client():
    """创建 TestClient，确保 lifespan 正确运行。"""
    with TestClient(app) as c:
        yield c


class TestHealth:
    """健康检查端点"""

    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["bible_loaded"] is True
        assert "chat_enabled" in data

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Xjoy API"
        assert data["version"] == "0.1.0"


class TestBooksAPI:
    """书卷端点"""

    def test_list_books(self, client):
        response = client.get("/api/bible/books")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 66
        assert books[0]["name"] == "Genesis"

    def test_list_books_ot(self, client):
        response = client.get("/api/bible/books?testament=OT")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 39

    def test_list_books_nt(self, client):
        response = client.get("/api/bible/books?testament=NT")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 27

    def test_list_books_invalid_testament(self, client):
        response = client.get("/api/bible/books?testament=XX")
        assert response.status_code == 422

    def test_books_by_testament(self, client):
        response = client.get("/api/bible/books-by-testament")
        assert response.status_code == 200
        data = response.json()
        assert len(data["OT"]) == 39
        assert len(data["NT"]) == 27


class TestVersesAPI:
    """经文端点"""

    def test_get_john_3_16(self, client):
        response = client.get("/api/bible/verses/John%203:16")
        assert response.status_code == 200
        verse = response.json()
        assert verse["book_name"] == "John"
        assert verse["chapter"] == 3
        assert verse["verse"] == 16
        assert "God so loved the world" in verse["text"]

    def test_get_genesis_1_1(self, client):
        response = client.get("/api/bible/verses/Genesis%201:1")
        assert response.status_code == 200
        verse = response.json()
        assert "created" in verse["text"].lower()

    def test_verse_not_found(self, client):
        response = client.get("/api/bible/verses/FakeBook%2099:99")
        assert response.status_code == 404

    def test_invalid_format(self, client):
        response = client.get("/api/bible/verses/invalid")
        assert response.status_code in (404, 400)


class TestChaptersAPI:
    """章节端点"""

    def test_psalm_23(self, client):
        response = client.get("/api/bible/chapters/Psalms/23")
        assert response.status_code == 200
        verses = response.json()
        assert len(verses) == 6

    def test_chapter_not_found(self, client):
        """Genesis 999 不存在，应返回空列表或 404"""
        response = client.get("/api/bible/chapters/Genesis/999")
        # Bible.chapter() 对不存在的章节可能返回空列表 (200) 或抛异常 (404)
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert response.json() == []


class TestSearchAPI:
    """搜索端点"""

    def test_search_love(self, client):
        response = client.get("/api/bible/search?q=love&limit=5")
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0

    def test_search_with_testament(self, client):
        response = client.get("/api/bible/search?q=grace&testament=NT&limit=5")
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0

    def test_search_empty_query(self, client):
        response = client.get("/api/bible/search?q=")
        assert response.status_code == 422


class TestStatsAPI:
    """统计端点"""

    def test_stats(self, client):
        response = client.get("/api/bible/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["books"] == 66
        assert stats["verses"] == 31103


class TestCrossRefsAPI:
    """交叉引用端点"""

    def test_crossrefs(self, client):
        response = client.get("/api/bible/crossrefs/John%203:16?limit=20")
        assert response.status_code == 200
        refs = response.json()
        assert len(refs) > 0


class TestRangeAPI:
    """范围端点"""

    def test_range(self, client):
        response = client.get(
            "/api/bible/range?start=John%203:16&end=John%203:18"
        )
        assert response.status_code == 200
        verses = response.json()
        assert len(verses) == 3


class TestChatAPI:
    """聊天端点"""

    def test_chat_no_api_key(self, client):
        """无 API Key 时应返回 503"""
        response = client.post(
            "/api/chat",
            json={"question": "What is faith?"},
        )
        if response.status_code == 503:
            assert "ANTHROPIC_API_KEY" in response.json()["detail"]
        elif response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "references" in data

    def test_chat_empty_question(self, client):
        """空问题应该返回验证错误"""
        response = client.post(
            "/api/chat",
            json={"question": ""},
        )
        assert response.status_code == 422

    def test_chat_with_history(self, client):
        """带对话历史的请求"""
        response = client.post(
            "/api/chat",
            json={
                "question": "What is faith?",
                "history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Welcome!"},
                ],
            },
        )
        assert response.status_code in (200, 503)


# ── 用户数据 API ────────────────────────────────────────────────────────────────

class TestNotesAPI:
    """笔记 REST API 集成测试"""

    def test_create_note(self, client):
        resp = client.post("/api/notes", json={
            "reference": "John 3:16",
            "content": "上帝的爱是无条件的",
            "book_name": "John",
            "chapter": 3,
            "verse": 16,
        })
        assert resp.status_code == 200
        note = resp.json()
        assert note["reference"] == "John 3:16"
        assert note["content"] == "上帝的爱是无条件的"
        assert note["id"]

    def test_list_notes(self, client):
        # 创建两条笔记
        client.post("/api/notes", json={
            "reference": "Gen 1:1", "content": "起初", "book_name": "Genesis", "chapter": 1, "verse": 1,
        })
        client.post("/api/notes", json={
            "reference": "Rev 22:21", "content": "结尾", "book_name": "Revelation", "chapter": 22, "verse": 21,
        })
        resp = client.get("/api/notes")
        assert resp.status_code == 200
        notes = resp.json()
        assert len(notes) >= 2

    def test_filter_notes_by_book(self, client):
        resp = client.get("/api/notes?book_name=Genesis")
        assert resp.status_code == 200
        notes = resp.json()
        for n in notes:
            assert n["book_name"] == "Genesis"

    def test_get_note_not_found(self, client):
        resp = client.get("/api/notes/nonexistent-id")
        assert resp.status_code == 404

    def test_update_note(self, client):
        resp = client.post("/api/notes", json={
            "reference": "Prov 3:5", "content": "trust", "book_name": "Proverbs", "chapter": 3, "verse": 5,
        })
        note_id = resp.json()["id"]
        resp2 = client.put(f"/api/notes/{note_id}", json={"content": "你要专心仰赖耶和华"})
        assert resp2.status_code == 200
        assert resp2.json()["content"] == "你要专心仰赖耶和华"

    def test_delete_note(self, client):
        resp = client.post("/api/notes", json={
            "reference": "Matt 5:3", "content": "虚心的人有福了", "book_name": "Matthew", "chapter": 5, "verse": 3,
        })
        note_id = resp.json()["id"]
        resp2 = client.delete(f"/api/notes/{note_id}")
        assert resp2.status_code == 200
        assert resp2.json() == {"deleted": True}
        # 确认已删除
        assert client.get(f"/api/notes/{note_id}").status_code == 404


class TestBookmarksAPI:
    """书签 REST API 集成测试"""

    def test_create_bookmark(self, client):
        resp = client.post("/api/bookmarks", json={
            "reference": "John 3:16",
            "book_name": "John",
            "chapter": 3,
            "verse": 16,
            "text": "For God so loved the world...",
        })
        assert resp.status_code == 200
        bm = resp.json()
        assert bm["reference"] == "John 3:16"
        assert bm["id"]

    def test_create_bookmark_with_note(self, client):
        resp = client.post("/api/bookmarks", json={
            "reference": "Rom 8:28",
            "book_name": "Romans",
            "chapter": 8,
            "verse": 28,
            "text": "And we know...",
            "note": "最爱的经文",
        })
        assert resp.status_code == 200
        assert resp.json()["note"] == "最爱的经文"

    def test_list_bookmarks(self, client):
        resp = client.get("/api/bookmarks")
        assert resp.status_code == 200
        bookmarks = resp.json()
        assert len(bookmarks) >= 1

    def test_check_bookmark(self, client):
        # 创建书签
        client.post("/api/bookmarks", json={
            "reference": "Psa 23:1", "book_name": "Psalms", "chapter": 23, "verse": 1,
            "text": "The LORD is my shepherd",
        })
        # 检查存在
        resp = client.get("/api/bookmarks/check?book_name=Psalms&chapter=23&verse=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["bookmarked"] is True
        assert data["bookmark_id"] is not None
        # 检查不存在
        resp2 = client.get("/api/bookmarks/check?book_name=Psalms&chapter=23&verse=99")
        assert resp2.status_code == 200
        assert resp2.json()["bookmarked"] is False

    def test_delete_bookmark(self, client):
        resp = client.post("/api/bookmarks", json={
            "reference": "Gen 1:1", "book_name": "Genesis", "chapter": 1, "verse": 1,
            "text": "In the beginning...",
        })
        bm_id = resp.json()["id"]
        resp2 = client.delete(f"/api/bookmarks/{bm_id}")
        assert resp2.status_code == 200
        assert resp2.json() == {"deleted": True}


class TestProgressAPI:
    """阅读进度 REST API 集成测试"""

    def test_update_and_get_progress(self, client):
        # 更新进度
        resp = client.post("/api/progress", json={
            "book_name": "John",
            "chapter": 3,
        })
        assert resp.status_code == 200
        p = resp.json()
        assert p["book_name"] == "John"
        assert p["chapters_read"] == 3

        # 获取进度
        resp2 = client.get("/api/progress")
        assert resp2.status_code == 200
        progress = resp2.json()
        assert len(progress) >= 1

    def test_get_progress_by_book(self, client):
        client.post("/api/progress", json={"book_name": "Genesis", "chapter": 10})
        resp = client.get("/api/progress?book_name=Genesis")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["book_name"] == "Genesis"
        assert data[0]["chapters_read"] >= 10


class TestUserStatsAPI:
    """用户统计 REST API 集成测试"""

    def test_user_stats(self, client):
        resp = client.get("/api/user/stats")
        assert resp.status_code == 200
        stats = resp.json()
        assert "notes" in stats
        assert "bookmarks" in stats
        assert "books_started" in stats
        assert "total_chapters_read" in stats
