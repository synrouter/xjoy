/**
 * 反馈页面 — 收集用户对 Xjoy 的使用反馈
 *
 * 覆盖 5 个维度：AI 聊天准确度、阅读体验、整体印象、功能建议、Bug 报告
 */

import { useState } from 'react';
import { useRouter } from 'next/router';
import PageHeader from '@/components/ui/PageHeader';
import { submitFeedback } from '@/lib/api';

// 反馈类别定义
const CATEGORIES = [
  {
    key: 'ai_chat',
    label: 'AI 聊天准确度',
    icon: '🤖',
    prompt: 'AI 回答是否准确引用经文？解释是否合乎上下文？',
    hasRating: true,
  },
  {
    key: 'reading',
    label: '阅读体验',
    icon: '📖',
    prompt: '阅读经文的体验如何？字号、导航、布局是否舒适？',
    hasRating: true,
  },
  {
    key: 'overall',
    label: '整体印象',
    icon: '💡',
    prompt: '你对 Xjoy 的整体感受是什么？会推荐给朋友吗？',
    hasRating: true,
  },
  {
    key: 'feature',
    label: '功能建议',
    icon: '✨',
    prompt: '你希望我们加入什么功能？请具体描述你的需求。',
    hasRating: false,
  },
  {
    key: 'bug',
    label: 'Bug 报告',
    icon: '🐛',
    prompt: '遇到了什么问题？请描述操作步骤和预期结果。',
    hasRating: false,
  },
  {
    key: 'other',
    label: '其他',
    icon: '💬',
    prompt: '还有什么想告诉我们的吗？',
    hasRating: false,
  },
];

// 星级评分组件
function StarRating({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex gap-1.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onChange(star)}
          className={`text-2xl transition-all active:scale-110 ${
            star <= value
              ? 'text-amber-400 scale-105'
              : 'text-parchment-300 hover:text-amber-300'
          }`}
          aria-label={`${star} 星`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

export default function FeedbackPage() {
  const router = useRouter();
  const [category, setCategory] = useState('');
  const [rating, setRating] = useState(0);
  const [message, setMessage] = useState('');
  const [contact, setContact] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const activeCategory = CATEGORIES.find((c) => c.key === category);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!category || !message.trim()) return;

    setSubmitting(true);
    setError('');
    try {
      await submitFeedback({
        category,
        rating: activeCategory?.hasRating ? rating : undefined,
        message: message.trim(),
        contact: contact.trim() || undefined,
      });
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败，请重试');
    } finally {
      setSubmitting(false);
    }
  };

  // 提交成功页
  if (submitted) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader title="Feedback" />
        <div className="flex-1 flex flex-col items-center justify-center px-5 pb-20">
          <div className="text-5xl mb-5">🙏</div>
          <h2 className="text-lg font-semibold text-parchment-700 mb-2">
            感谢你的反馈！
          </h2>
          <p className="text-sm text-parchment-500 text-center mb-6">
            你的意见帮助我们让 Xjoy 变得更好。<br />
            每一份反馈都会被认真对待。
          </p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2.5 bg-parchment-700 text-white rounded-xl text-sm font-medium
                       hover:bg-parchment-800 active:scale-95 transition-all"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Feedback" subtitle="帮助我们让 Xjoy 变得更好" />

      <form
        onSubmit={handleSubmit}
        className="flex-1 overflow-y-auto px-5 pb-6 space-y-5"
      >
        {/* 选择类别 */}
        <div>
          <label className="block text-sm font-medium text-parchment-700 mb-2">
            反馈类别
          </label>
          <div className="grid grid-cols-2 gap-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.key}
                type="button"
                onClick={() => {
                  setCategory(cat.key);
                  setRating(0);
                }}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border text-left text-sm
                  transition-all active:scale-95 ${
                    category === cat.key
                      ? 'border-parchment-500 bg-parchment-100 text-parchment-800 shadow-sm'
                      : 'border-parchment-200 bg-white text-parchment-600 hover:border-parchment-300'
                  }`}
              >
                <span className="text-lg">{cat.icon}</span>
                <span className="truncate">{cat.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 评分（仅部分类别） */}
        {activeCategory?.hasRating && (
          <div>
            <label className="block text-sm font-medium text-parchment-700 mb-2">
              评分
            </label>
            <StarRating value={rating} onChange={setRating} />
          </div>
        )}

        {/* 反馈正文 */}
        <div>
          <label className="block text-sm font-medium text-parchment-700 mb-2">
            {activeCategory?.prompt || '请描述你的想法'}
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
            maxLength={5000}
            required
            placeholder="在这里写下你的反馈..."
            className="w-full px-4 py-3 border border-parchment-200 rounded-xl text-sm
                       text-parchment-800 placeholder-parchment-400
                       focus:outline-none focus:ring-2 focus:ring-parchment-500/10 focus:border-parchment-500
                       resize-none bg-white"
          />
          <p className="text-[10px] text-parchment-400 text-right mt-1">
            {message.length}/5000
          </p>
        </div>

        {/* 联系方式（可选） */}
        <div>
          <label className="block text-sm font-medium text-parchment-700 mb-2">
            联系方式 <span className="text-parchment-400 font-normal">（选填）</span>
          </label>
          <input
            type="text"
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            maxLength={200}
            placeholder="Email 或手机号，方便我们后续跟进"
            className="w-full px-4 py-3 border border-parchment-200 rounded-xl text-sm
                       text-parchment-800 placeholder-parchment-400
                       focus:outline-none focus:ring-2 focus:ring-parchment-500/10 focus:border-parchment-500
                       bg-white"
          />
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* 提交按钮 */}
        <button
          type="submit"
          disabled={!category || !message.trim() || submitting}
          className="w-full py-3 rounded-xl text-sm font-semibold text-white
                     transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed
                     bg-parchment-700 hover:bg-parchment-800"
        >
          {submitting ? '提交中...' : '提交反馈'}
        </button>

        <p className="text-center text-[10px] text-parchment-400 pt-1">
          每一份反馈都会被认真对待，感谢你参与 Xjoy 的成长 🙏
        </p>
      </form>
    </div>
  );
}
