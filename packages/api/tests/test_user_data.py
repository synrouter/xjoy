"""
UserDataStore 单元测试

测试笔记、书签、阅读进度的 CRUD 操作。
"""

import os
import tempfile
import pytest
from xjoy.user_data import UserDataStore


@pytest.fixture
def store():
    """创建临时数据库的 UserDataStore 实例"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    s = UserDataStore(path)
    yield s
    os.unlink(path)


class TestNotes:
    """笔记 CRUD 测试"""

    def test_create_note(self, store):
        note = store.create_note(
            reference="John 3:16",
            content="上帝的爱是无条件的",
            book_name="John",
            chapter=3,
            verse=16,
        )
        assert note.reference == "John 3:16"
        assert note.content == "上帝的爱是无条件的"
        assert note.book_name == "John"
        assert note.chapter == 3
        assert note.verse == 16
        assert note.id  # 自动生成 UUID

    def test_get_note(self, store):
        created = store.create_note(
            reference="Psalm 23:1", content="耶和华是我的牧者",
            book_name="Psalms", chapter=23, verse=1,
        )
        fetched = store.get_note(created.id)
        assert fetched is not None
        assert fetched.content == created.content
        assert fetched.reference == created.reference

    def test_get_note_not_found(self, store):
        assert store.get_note("nonexistent-id") is None

    def test_list_notes(self, store):
        store.create_note("Gen 1:1", "起初神创造天地", "Genesis", 1, 1)
        store.create_note("John 1:1", "太初有道", "John", 1, 1)
        store.create_note("John 3:16", "神爱世人", "John", 3, 16)

        all_notes = store.list_notes()
        assert len(all_notes) == 3

        john_notes = store.list_notes(book_name="John")
        assert len(john_notes) == 2

        gen_notes = store.list_notes(book_name="Genesis", chapter=1)
        assert len(gen_notes) == 1

    def test_update_note(self, store):
        created = store.create_note("Prov 3:5", "trust", "Proverbs", 3, 5)
        updated = store.update_note(created.id, "你要专心仰赖耶和华")
        assert updated is not None
        assert updated.content == "你要专心仰赖耶和华"
        assert updated.updated_at > created.updated_at

    def test_update_note_not_found(self, store):
        assert store.update_note("nonexistent", "content") is None

    def test_delete_note(self, store):
        created = store.create_note("Matt 5:3", "虚心的人有福了", "Matthew", 5, 3)
        assert store.delete_note(created.id) is True
        assert store.get_note(created.id) is None

    def test_delete_note_not_found(self, store):
        assert store.delete_note("nonexistent") is False

    def test_notes_count(self, store):
        assert store.get_notes_count() == 0
        store.create_note("Gen 1:1", "In the beginning", "Genesis", 1, 1)
        store.create_note("Rev 22:21", "The grace", "Revelation", 22, 21)
        assert store.get_notes_count() == 2

    def test_list_notes_pagination(self, store):
        for i in range(10):
            store.create_note(
                f"Psalm {i+1}:1", f"Note {i}", "Psalms", i + 1, 1
            )
        first_page = store.list_notes(limit=5, offset=0)
        assert len(first_page) == 5
        second_page = store.list_notes(limit=5, offset=5)
        assert len(second_page) == 5


class TestBookmarks:
    """书签 CRUD 测试"""

    def test_create_bookmark(self, store):
        bm = store.create_bookmark(
            reference="John 3:16",
            book_name="John",
            chapter=3,
            verse=16,
            text="For God so loved the world...",
        )
        assert bm.reference == "John 3:16"
        assert bm.book_name == "John"
        assert bm.text.startswith("For God")
        assert bm.id

    def test_create_bookmark_with_note(self, store):
        bm = store.create_bookmark(
            reference="Rom 8:28",
            book_name="Romans",
            chapter=8,
            verse=28,
            text="And we know that all things work together...",
            note="最爱的经文之一",
        )
        assert bm.note == "最爱的经文之一"

    def test_duplicate_bookmark_updates(self, store):
        """同一节经文书签应更新而非重复创建"""
        bm1 = store.create_bookmark(
            "John 3:16", "John", 3, 16, "For God so loved..."
        )
        bm2 = store.create_bookmark(
            "John 3:16", "John", 3, 16, "Updated text", note="new note"
        )
        # 应更新已有记录
        assert bm2.id == bm1.id  # 相同 ID
        assert bm2.text == "Updated text"
        assert bm2.note == "new note"

        # 不创建重复记录
        all_bm = store.list_bookmarks(book_name="John")
        assert len(all_bm) == 1

    def test_list_bookmarks(self, store):
        store.create_bookmark("Gen 1:1", "Genesis", 1, 1, "In the beginning...")
        store.create_bookmark("Rev 22:21", "Revelation", 22, 21, "The grace...")

        all_bm = store.list_bookmarks()
        assert len(all_bm) == 2

        gen_bm = store.list_bookmarks(book_name="Genesis")
        assert len(gen_bm) == 1

    def test_delete_bookmark(self, store):
        bm = store.create_bookmark("John 3:16", "John", 3, 16, "text")
        assert store.delete_bookmark(bm.id) is True
        assert store.delete_bookmark(bm.id) is False  # 已删除

    def test_is_bookmarked(self, store):
        assert store.is_bookmarked("John", 3, 16) is None
        bm = store.create_bookmark("John 3:16", "John", 3, 16, "text")
        assert store.is_bookmarked("John", 3, 16) == bm.id

    def test_bookmarks_count(self, store):
        assert store.get_bookmarks_count() == 0
        store.create_bookmark("Gen 1:1", "Genesis", 1, 1, "text")
        store.create_bookmark("Exo 20:1", "Exodus", 20, 1, "text")
        assert store.get_bookmarks_count() == 2


class TestReadingProgress:
    """阅读进度测试"""

    def test_update_progress_new_book(self, store):
        p = store.update_progress("John", 3, total_chapters=21)
        assert p.book_name == "John"
        assert p.chapters_read == 3
        assert p.total_chapters == 21

    def test_update_progress_incremental(self, store):
        store.update_progress("Psalms", 23, total_chapters=150)
        p = store.update_progress("Psalms", 50, total_chapters=150)
        assert p.chapters_read == 50  # 取最大值

    def test_update_progress_no_regression(self, store):
        """阅读进度不应倒退"""
        store.update_progress("Genesis", 10, total_chapters=50)
        p = store.update_progress("Genesis", 5, total_chapters=50)
        assert p.chapters_read == 10  # 保持最大值

    def test_get_progress(self, store):
        store.update_progress("Genesis", 10, total_chapters=50)
        store.update_progress("Exodus", 5, total_chapters=40)

        all_p = store.get_progress()
        assert len(all_p) == 2

        gen_p = store.get_progress(book_name="Genesis")
        assert len(gen_p) == 1
        assert gen_p[0].book_name == "Genesis"
        assert gen_p[0].chapters_read == 10

    def test_get_chapters_read(self, store):
        assert store.get_chapters_read("John") == 0
        store.update_progress("John", 5, total_chapters=21)
        assert store.get_chapters_read("John") == 5

    def test_progress_sorted_by_last_read(self, store):
        """进度应按最近阅读时间排序"""
        store.update_progress("Genesis", 1, total_chapters=50)
        store.update_progress("Revelation", 22, total_chapters=22)
        progress = store.get_progress()
        # 最近更新的排在前面
        assert progress[0].book_name == "Revelation"


class TestStats:
    """统计测试"""

    def test_empty_stats(self, store):
        s = store.stats()
        assert s["notes"] == 0
        assert s["bookmarks"] == 0
        assert s["books_started"] == 0
        assert s["total_chapters_read"] == 0

    def test_full_stats(self, store):
        store.create_note("Gen 1:1", "note1", "Genesis", 1, 1)
        store.create_note("Exo 1:1", "note2", "Exodus", 1, 1)
        store.create_bookmark("John 3:16", "John", 3, 16, "text")
        store.update_progress("Genesis", 10, total_chapters=50)
        store.update_progress("Exodus", 5, total_chapters=40)

        s = store.stats()
        assert s["notes"] == 2
        assert s["bookmarks"] == 1
        assert s["books_started"] == 2
        assert s["total_chapters_read"] == 15  # 10 + 5
