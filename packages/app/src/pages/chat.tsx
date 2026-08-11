/**
 * AI 对话页面
 *
 * 提供基于 KJV 圣经的 AI 聊天交互。
 * 从原 index.tsx 迁移而来。
 */

import { useState, useRef, useEffect } from 'react';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import TypingIndicator from '@/components/TypingIndicator';
import PageHeader from '@/components/ui/PageHeader';
import { sendChatMessage } from '@/lib/api';
import type { ChatReference } from '@xjoy/shared';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  references?: ChatReference[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `欢迎来到 Xjoy！我是您的 AI 圣经助手，基于英王钦定本 (KJV) 圣经。

您可以问我任何关于圣经的问题，例如：
• 某段经文的含义
• 某个主题在圣经中如何讲述
• 特定经文的交叉引用

我会确保所有回答都基于圣经原文，并给出准确的经文引用。`,
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (question: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const history = messages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await sendChatMessage(question, history);

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        references: response.references,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'error',
        content:
          err instanceof Error ? err.message : '发送消息时出现未知错误',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="💬 AI Study Helper"
        subtitle="Powered by AI, grounded in KJV"
        bordered
      />

      {/* 聊天区域 */}
      <main className="flex-1 overflow-y-auto chat-scroll px-4 py-4">
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            role={msg.role}
            content={msg.content}
            references={msg.references}
          />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={chatEndRef} />
      </main>

      {/* 输入区域 */}
      <div className="shrink-0">
        <ChatInput onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  );
}
