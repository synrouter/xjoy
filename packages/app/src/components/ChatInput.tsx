'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';

const SUGGESTIONS = [
  { label: 'John 3:16', query: 'What does John 3:16 say?' },
  { label: '关于爱的教导', query: 'What did Jesus teach about love?' },
  { label: '信心与行为', query: 'Compare faith and works according to James' },
  { label: '十诫', query: 'Show me the Ten Commandments' },
  { label: '神的保护', query: 'What does Psalms say about God\'s protection?' },
];

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
    // 重置 textarea 高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 自动调整 textarea 高度
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  return (
    <div className="border-t border-parchment-200 bg-white px-4 py-3">
      {/* 建议词 */}
      <div className="flex flex-wrap gap-2 mb-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            onClick={() => onSend(s.query)}
            disabled={disabled}
            className="px-3.5 py-1.5 text-xs bg-parchment-50 border border-parchment-200 
                       rounded-full text-parchment-500 hover:bg-parchment-200 hover:text-parchment-700
                       hover:border-parchment-300 transition-colors disabled:opacity-50"
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* 输入区 */}
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="输入您的问题，如：What did Jesus teach about forgiveness?"
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none bg-parchment-50 border border-parchment-200 
                     rounded-xl px-4 py-3 text-[15px] leading-relaxed
                     placeholder:text-parchment-400 focus:outline-none 
                     focus:border-parchment-500 focus:ring-2 focus:ring-parchment-500/10
                     disabled:opacity-50 transition-all"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="px-5 py-3 bg-parchment-700 text-white rounded-xl font-medium
                     text-[15px] hover:bg-parchment-800 disabled:opacity-40 
                     disabled:cursor-not-allowed transition-colors shrink-0"
        >
          发送
        </button>
      </div>

      <p className="text-[11px] text-parchment-400 mt-2 text-center">
        Xjoy 基于 KJV 经文回答，每一条陈述都有准确的经文引用。
      </p>
    </div>
  );
}
