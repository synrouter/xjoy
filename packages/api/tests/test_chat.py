"""
Chat 服务测试

测试 RAG 检索管道、关键词提取和上下文构建。
"""
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xjoy.bible import Bible
from xjoy.chat import ChatService


@pytest.fixture(scope="module")
def chat():
    """创建 ChatService 实例（无 API Key）"""
    db_path = ROOT.parent / "db" / "data" / "kjv.db"
    bible = Bible(str(db_path))
    return ChatService(bible)


class TestKeywordExtraction:
    """关键词提取测试"""

    def test_extract_keywords(self, chat):
        """验证从问题中提取关键词"""
        keywords = chat._extract_keywords(
            "What did Jesus teach about faith and love?"
        )
        # 应该有有效关键词
        assert len(keywords) > 0
        # 停用词应该被过滤
        assert "what" not in keywords
        assert "did" not in keywords
        assert "and" not in keywords
        assert "the" not in keywords
        assert "about" not in keywords

    def test_extract_keywords_single_word(self, chat):
        """单关键词测试"""
        keywords = chat._extract_keywords("faith")
        assert "faith" in keywords

    def test_extract_keywords_order_by_length(self, chat):
        """验证关键词按长度降序排列"""
        keywords = chat._extract_keywords(
            "forgiveness love faith"
        )
        # forgiveness (12) > love (4) > faith (5) → 不对，forgiveness (12) > faith (5) > love (4)
        if len(keywords) >= 2:
            assert len(keywords[0]) >= len(keywords[1])


class TestRetrieval:
    """RAG 检索测试"""

    def test_retrieve_returns_results(self, chat):
        """验证检索返回结果"""
        results = chat._retrieve("What did Jesus say about faith?")
        assert len(results) > 0
        # 每个结果应有经文和排名
        for r in results:
            assert r.verse.text
            assert r.verse.reference

    def test_retrieve_with_testament_filter(self, chat):
        """验证按约过滤检索"""
        results_nt = chat._retrieve("love", testament="NT")
        for r in results_nt:
            assert r.verse.book_id >= 40  # NT starts after Malachi (book 39)

    def test_retrieve_returns_diverse_verses(self, chat):
        """验证检索到的经文不全是同一条"""
        results = chat._retrieve("grace mercy peace", testament="NT")
        if len(results) > 1:
            verse_ids = {r.verse.id for r in results}
            assert len(verse_ids) > 1


class TestContextBuilding:
    """上下文构建测试"""

    def test_build_context(self, chat):
        """验证将检索结果构建为上下文文本"""
        results = chat._retrieve("faith", testament="NT")
        context = chat._build_context(results)
        # 应该包含经文引用
        assert "[" in context
        assert "]" in context
        # 不应超过最大长度
        assert len(context) <= chat.MAX_CONTEXT_CHARS

    def test_build_context_empty(self, chat):
        """空结果返回提示"""
        context = chat._build_context([])
        assert context == "（未找到相关经文）"


class TestAskWithoutAPIKey:
    """无 API Key 时的行为测试"""

    def test_ask_returns_guidance(self, chat):
        """验证无 API Key 时返回引导信息"""
        import asyncio
        response = asyncio.run(chat.ask("What is faith?"))
        assert "⚠️ 未配置 ANTHROPIC_API_KEY" in response.answer
        # 即使没有 API Key，也应该有引用
        assert len(response.references) > 0
