"""
Xjoy RAG 聊天模块

基于 Claude API 的 RAG（检索增强生成）圣经问答。
核心原则：文本忠实性 — AI 不得捏造或错误引用经文。

检索策略（两阶段）：
1. FTS5 关键词检索 — 快速匹配用户查询中的关键词
2. Claude 上下文组装 — 将相关经文注入 system prompt，严格约束引用范围

Usage:
    from xjoy.chat import ChatService
    chat = ChatService(bible, api_key="...")
    response = await chat.ask("What did Jesus say about faith?")
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Optional

from xjoy.bible import Bible, SearchResult


# ── 系统提示词 ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """你是 Xjoy，一位基于圣经文本的助手。你只依据所提供的 KJV 经文来回答问题。

## 核心规则（不可违反）

1. **只引用提供的经文。** 你只能引用下方「参考经文」中列出的经节。不得引用或暗示任何未提供的经文。
2. **每条陈述必须有经文依据。** 当你做出任何关于圣经内容的陈述时，必须同时给出具体的经文章节引用。
3. **不可捏造。** 如果参考经文中没有足够的信息来回答用户的问题，请明确告诉用户：「根据我目前检索到的经文，我无法完全回答这个问题。建议您查阅相关经卷以获得更全面的理解。」然后基于已有经文提供部分相关信息。
4. **保持谦卑。** 你不是牧师、神学家或属灵权威。你是一个帮助用户理解圣经文本的工具。对于需要深度解释或应用的问题，建议用户咨询牧师或查阅可靠的解经资料。
5. **尊重文本。** 使用 KJV（英王钦定本）的措辞和表达。经文引用必须精确，包括书名、章节和经文编号。

## 回答格式

- 以经文引用开始，例如：「根据 John 3:16...」
- 在引用经文时，使用引号标记经文原文
- 结束时可以提出一个反思问题，帮助用户深入思考经文含义
- 如果用户的问题与圣经无关，礼貌地引导他们回到圣经话题

## 参考经文

{context}

---

现在，请根据以上经文回答用户的问题。记住：只引用上面列出的经文。"""


USER_MESSAGE_TEMPLATE = """用户问题：{question}

请根据参考经文回答。如果经文不足以完全回答，请诚实说明。"""


# ── 数据结构 ───────────────────────────────────────────────────────────────────

@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # 'user' | 'assistant'
    content: str


@dataclass
class ChatResponse:
    """聊天响应"""
    answer: str
    references: list[dict] = field(default_factory=list)
    model: str = ""
    usage: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "references": self.references,
            "model": self.model,
            "usage": self.usage,
        }


# ── 聊天服务 ───────────────────────────────────────────────────────────────────

class ChatService:
    """
    RAG 聊天服务。

    使用 Claude API 进行基于经文的问答，通过 FTS5 检索相关经文作为上下文。
    """

    # Claude 模型
    DEFAULT_MODEL = "claude-sonnet-5-20251001"

    # 检索参数
    DEFAULT_RETRIEVAL_LIMIT = 15  # 检索经文数量
    MAX_CONTEXT_CHARS = 8000      # 上下文最大字符数

    def __init__(
        self,
        bible: Bible,
        *,
        api_key: str | None = None,
        model: str | None = None,
        retrieval_limit: int | None = None,
    ):
        self.bible = bible
        self.api_key = (
            api_key
            or os.environ.get("ANTHROPIC_API_KEY", "")
            or os.environ.get("CLAUDE_API_KEY", "")
        )
        # 注意：不使用 ANTHROPIC_MODEL 环境变量（Paperclip 运行时会设置它）
        self.model = model or self.DEFAULT_MODEL
        self.retrieval_limit = retrieval_limit or self.DEFAULT_RETRIEVAL_LIMIT

    async def ask(
        self,
        question: str,
        *,
        conversation_history: list[ChatMessage] | None = None,
        testament: str | None = None,
    ) -> ChatResponse:
        """
        回答用户关于圣经的问题。

        Args:
            question: 用户的问题
            conversation_history: 之前的对话历史
            testament: 限定检索范围 ('OT' 或 'NT')

        Returns:
            ChatResponse: 包含回答和引用经文
        """
        # 第一阶段：检索相关经文
        search_results = self._retrieve(question, testament=testament)

        # 第二阶段：组装上下文
        context = self._build_context(search_results)

        # 第三阶段：调用 Claude
        answer = await self._call_claude(question, context, conversation_history)

        # 提取引用
        references = [
            {
                "reference": r.verse.reference,
                "text": r.verse.text,
                "book_name": r.verse.book_name,
                "chapter": r.verse.chapter,
                "verse": r.verse.verse,
            }
            for r in search_results[:10]
        ]

        return ChatResponse(
            answer=answer,
            references=references,
            model=self.model,
        )

    def _retrieve(
        self,
        question: str,
        *,
        testament: str | None = None,
    ) -> list[SearchResult]:
        """
        检索与问题相关的经文。

        策略：
        1. FTS5 全文搜索
        2. 如果 FTS5 结果不足，使用 LIKE 关键词搜索补充
        """
        # FTS5 搜索
        results = self.bible.search(
            question,
            limit=self.retrieval_limit,
            testament=testament,
        )

        # 如果结果太少，尝试用提取的关键词补充
        if len(results) < 5:
            keywords = self._extract_keywords(question)
            seen_ids = {r.verse.id for r in results}

            for kw in keywords[:3]:
                kw_results = self.bible.keyword_search(kw, limit=10)
                for verse in kw_results:
                    if verse.id not in seen_ids:
                        results.append(SearchResult(
                            verse=verse,
                            snippet=verse.text[:60],
                            rank=999.0,
                        ))
                        seen_ids.add(verse.id)

                if len(results) >= self.retrieval_limit:
                    break

        return results[:self.retrieval_limit]

    def _build_context(self, results: list[SearchResult]) -> str:
        """将检索结果组装为 Claude 的上下文文本。"""
        lines = []
        total_chars = 0

        for r in results:
            ref = r.verse.reference
            text = r.verse.text
            line = f"[{ref}] {text}"
            total_chars += len(line) + 1

            if total_chars > self.MAX_CONTEXT_CHARS:
                break

            lines.append(line)

        if not lines:
            return "（未找到相关经文）"

        return "\n".join(lines)

    async def _call_claude(
        self,
        question: str,
        context: str,
        history: list[ChatMessage] | None = None,
    ) -> str:
        """
        调用 Claude API 生成回答。

        使用 Anthropic SDK 直接调用，支持 conversation history。
        """
        if not self.api_key:
            return (
                "⚠️ 未配置 ANTHROPIC_API_KEY 环境变量。\n\n"
                "聊天功能需要 Claude API 密钥。请设置环境变量后重启服务。\n\n"
                "在此期间，您可以使用以下 API 端点直接查询经文：\n"
                "- GET /api/bible/verses/John 3:16\n"
                "- GET /api/bible/search?q=love\n"
            )

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            system_prompt = SYSTEM_PROMPT.format(context=context)
            user_message = USER_MESSAGE_TEMPLATE.format(question=question)

            messages = []
            if history:
                for msg in history[-6:]:  # 保留最近 3 轮对话
                    messages.append({
                        "role": msg.role,
                        "content": msg.content,
                    })

            messages.append({"role": "user", "content": user_message})

            response = await client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,  # 低温度以保证文本准确性
                system=system_prompt,
                messages=messages,
            )

            # 提取文本内容
            content_blocks = response.content
            text_parts = []
            for block in content_blocks:
                if block.type == "text":
                    text_parts.append(block.text)

            return "".join(text_parts)

        except ImportError:
            return (
                "⚠️ anthropic Python SDK 未安装。\n\n"
                "请运行：pip install anthropic\n"
                "然后设置 ANTHROPIC_API_KEY 环境变量。"
            )
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return (
                    "⚠️ Claude API 认证失败。请检查 ANTHROPIC_API_KEY 是否正确设置。\n\n"
                    "您可以在 https://console.anthropic.com 获取 API 密钥。"
                )
            return f"⚠️ 调用 Claude API 时出错：{error_msg}\n\n请稍后重试。"

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """
        从用户问题中提取关键词用于 FTS5 搜索。

        简单的实现：根据空格分词，过滤短词和停用词。
        """
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "shall", "to",
            "of", "in", "for", "on", "with", "at", "by", "from", "as",
            "into", "through", "during", "before", "after", "above",
            "below", "between", "and", "but", "or", "nor", "not", "so",
            "if", "then", "than", "that", "this", "these", "those",
            "what", "which", "who", "whom", "whose", "when", "where",
            "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "some", "any", "no", "very", "just", "about",
            "over", "under", "again", "further", "once", "here", "there",
        }

        import re
        words = re.findall(r'[a-zA-Z]+', text.lower())
        keywords = []
        for w in words:
            if len(w) > 2 and w not in stopwords:
                keywords.append(w)

        # 返回最长的关键词优先（通常更有意义）
        keywords.sort(key=len, reverse=True)
        return keywords[:10]
