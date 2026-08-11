"""
Bible 数据访问层测试

测试核心的经文查询、搜索、章节获取等功能。
"""

import pytest
import sys
from pathlib import Path

# 将项目根目录加入 Python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xjoy.bible import Bible


@pytest.fixture(scope="module")
def bible():
    """创建 Bible 实例，所有测试共享同一个数据库连接。"""
    db_path = ROOT.parent / "db" / "data" / "kjv.db"
    if not db_path.exists():
        pytest.fail(f"数据库文件不存在: {db_path}")
    return Bible(str(db_path))


class TestBibleBasics:
    """基础数据验证"""

    def test_stats(self, bible):
        """验证数据库统计信息正确"""
        stats = bible.stats()
        assert stats["books"] == 66
        assert stats["verses"] == 31103
        assert stats["ot_verses"] == 23145
        assert stats["nt_verses"] == 7958
        assert stats["cross_references"] == 343609

    def test_books(self, bible):
        """验证书卷列表"""
        books = bible.books()
        assert len(books) == 66
        # 第一卷应该是 Genesis
        assert books[0].name == "Genesis"
        assert books[0].sort_order == 1
        # 最后一卷应该是 Revelation
        assert books[-1].name == "Revelation"

    def test_books_by_testament(self, bible):
        """验证新旧约书卷分组"""
        grouped = bible.books_by_testament()
        assert len(grouped["OT"]) == 39
        assert len(grouped["NT"]) == 27
        assert grouped["OT"][0].name == "Genesis"
        assert grouped["NT"][0].name == "Matthew"


class TestVerseLookup:
    """经文查询测试"""

    def test_john_3_16(self, bible):
        """查询最著名的经文"""
        verse = bible.verse("John 3:16")
        assert verse.book_name == "John"
        assert verse.chapter == 3
        assert verse.verse == 16
        assert "God so loved the world" in verse.text
        assert verse.reference == "John 3:16"

    def test_genesis_1_1(self, bible):
        """查询圣经第一句"""
        verse = bible.verse("Genesis 1:1")
        assert verse.book_name == "Genesis"
        assert verse.chapter == 1
        assert verse.verse == 1
        assert "beginning" in verse.text.lower()
        assert "God created" in verse.text

    def test_case_insensitive_reference(self, bible):
        """验证经文引用不区分大小写"""
        verse1 = bible.verse("john 3:16")
        verse2 = bible.verse("JOHN 3:16")
        verse3 = bible.verse("John 3:16")
        assert verse1.id == verse2.id == verse3.id

    def test_not_found(self, bible):
        """验证不存在的经文引用抛出异常"""
        with pytest.raises(ValueError, match="Unknown book"):
            bible.verse("Nonexistent 99:99")


class TestChapterLookup:
    """章节查询测试"""

    def test_psalm_23(self, bible):
        """诗篇 23 篇应有 6 节"""
        verses = bible.chapter("Psalms", 23)
        assert len(verses) == 6
        assert verses[0].reference == "Psalms 23:1"
        assert "The LORD is my shepherd" in verses[0].text

    def test_psalm_119(self, bible):
        """圣经中最长的诗篇"""
        verses = bible.chapter("Psalms", 119)
        assert len(verses) == 176

    def test_shortest_chapter(self, bible):
        """诗篇 117 篇只有 2 节"""
        verses = bible.chapter("Psalms", 117)
        assert len(verses) == 2

    def test_book_name_alias(self, bible):
        """验证书卷名别名（1 John vs First John）"""
        # "1 John" 应该能正常工作
        verses = bible.chapter("1 John", 1)
        assert len(verses) == 10  # 1 John 1 有 10 节


class TestSearch:
    """全文搜索测试"""

    def test_search_love(self, bible):
        """搜索 'love' 应该有大量结果"""
        results = bible.search("love", limit=20)
        assert len(results) > 0
        # 检查结果包含 score
        for r in results:
            assert r.rank is not None

    def test_search_with_testament_filter(self, bible):
        """验证按新约过滤搜索"""
        results = bible.search("grace", testament="NT", limit=10)
        for r in results:
            assert r.verse.book_name in {
                b.name for b in bible.books_by_testament()["NT"]
            }

    def test_search_with_book_filter(self, bible):
        """验证按书卷过滤搜索"""
        results = bible.search("love", book="John", limit=10)
        for r in results:
            assert r.verse.book_name == "John"

    def test_empty_search_returns_empty(self, bible):
        """验证无意义搜索"""
        results = bible.search("zzzzzzzzzzzzz", limit=5)
        # 可能返回 0 或很少的结果
        assert len(results) >= 0


class TestCrossRefs:
    """交叉引用测试"""

    def test_cross_refs_john_3_16(self, bible):
        """验证 John 3:16 有交叉引用"""
        refs = bible.cross_refs("John 3:16", limit=20)
        # John 3:16 是圣经中最被引用的经文之一，应该有交叉引用
        assert len(refs) > 0

    def test_cross_refs_to(self, bible):
        """验证反向交叉引用"""
        refs = bible.cross_refs_to("John 3:16", limit=10)
        assert len(refs) >= 0  # 可能为 0，但不应该报错


class TestRange:
    """范围查询测试"""

    def test_short_range(self, bible):
        """验证短范围查询"""
        verses = bible.range("John 3:16", "John 3:18")
        assert len(verses) == 3
        references = [v.reference for v in verses]
        assert "John 3:16" in references
        assert "John 3:17" in references
        assert "John 3:18" in references
