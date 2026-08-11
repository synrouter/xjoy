'use client';

import type { ChatReference } from '@xjoy/shared';

interface Props {
  role: 'user' | 'assistant' | 'error';
  content: string;
  references?: ChatReference[];
}

export default function ChatMessage({ role, content, references }: Props) {
  if (role === 'user') {
    return (
      <div className="message-enter flex justify-end mb-5">
        <div className="max-w-[85%] bg-parchment-200 text-parchment-900 rounded-2xl rounded-br-md px-5 py-3.5 text-[15px] leading-relaxed whitespace-pre-wrap">
          {content}
        </div>
      </div>
    );
  }

  if (role === 'error') {
    return (
      <div className="message-enter mb-5">
        <div className="max-w-full bg-red-50 border border-red-200 text-red-800 rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="message-enter mb-5">
      <div className="max-w-full bg-white border border-parchment-200 rounded-2xl rounded-bl-md px-5 py-3.5 text-[15px] leading-relaxed whitespace-pre-wrap shadow-sm">
        {content}
      </div>

      {references && references.length > 0 && (
        <div className="mt-3 bg-parchment-100 border border-parchment-200 rounded-xl px-4 py-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-parchment-500 mb-2">
            📖 参考经文
          </h4>
          <div className="space-y-1.5">
            {references.map((ref, i) => (
              <div
                key={i}
                className="text-[13px] leading-relaxed border-b border-parchment-200/50 last:border-b-0 pb-1.5 last:pb-0"
              >
                <span className="font-semibold text-parchment-700">
                  {ref.reference}
                </span>
                <span className="text-parchment-600"> — {ref.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
