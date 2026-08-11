'use client';

import { useState, useCallback } from 'react';

interface Slide {
  icon: string;
  title: string;
  subtitle: string;
  description: string;
}

const SLIDES: Slide[] = [
  {
    icon: '📖',
    title: '欢迎来到 Xjoy',
    subtitle: 'Your AI-Powered KJV Bible',
    description:
      'Xjoy 是一款基于英王钦定本圣经的智能应用。\n在这里，你可以读经、提问、做笔记，\n用全新的方式亲近神的话语。',
  },
  {
    icon: '📅',
    title: '每日经文',
    subtitle: 'Start Each Day with Scripture',
    description:
      '打开 Today 标签，每天获取一节精选经文。\n让神的话语成为你一天的力量和引导。\n点击经文即可进入上下文阅读。',
  },
  {
    icon: '📖',
    title: '阅读圣经',
    subtitle: 'Read the Holy Bible',
    description:
      '在 Bible 标签中浏览全部 66 卷书。\n点击书卷 → 选择章节 → 开始阅读。\n支持字号调节、书签标记和笔记记录。',
  },
  {
    icon: '💬',
    title: 'AI 研经助手',
    subtitle: 'Ask, Learn & Understand',
    description:
      '对经文有疑问？使用 AI Chat 提问。\n助手会基于 KJV 原文回答，\n每次回答都附带准确的经文引用。',
  },
  {
    icon: '🎓',
    title: '学习工具',
    subtitle: 'Track Your Journey',
    description:
      '在 Study 标签中管理你的笔记和书签。\nMe 标签会追踪你的阅读进度，\n记录你与神话语同行的每一步。',
  },
  {
    icon: '🙏',
    title: '开始你的旅程',
    subtitle: 'Thy word is a lamp unto my feet',
    description:
      '你的话是我脚前的灯，是我路上的光。\n— 诗篇 119:105\n\n愿你通过 Xjoy 更深地认识神的话语。',
  },
];

interface Props {
  onComplete: () => void;
}

export default function Onboarding({ onComplete }: Props) {
  const [current, setCurrent] = useState(0);
  const [exiting, setExiting] = useState(false);

  const slide = SLIDES[current];
  const isLast = current === SLIDES.length - 1;

  const handleNext = useCallback(() => {
    if (isLast) {
      setExiting(true);
      setTimeout(onComplete, 300);
    } else {
      setCurrent((prev) => prev + 1);
    }
  }, [isLast, onComplete]);

  const handleSkip = useCallback(() => {
    setExiting(true);
    setTimeout(onComplete, 300);
  }, [onComplete]);

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-parchment-50 px-6 transition-opacity duration-300 ${
        exiting ? 'opacity-0' : 'opacity-100'
      }`}
    >
      {/* 进度指示器 */}
      <div className="absolute top-8 left-6 right-6 flex items-center justify-between">
        <button
          onClick={handleSkip}
          className="text-sm text-parchment-400 hover:text-parchment-600 transition-colors"
        >
          跳过
        </button>
        <div className="flex gap-1.5">
          {SLIDES.map((_, i) => (
            <span
              key={i}
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                i === current
                  ? 'bg-parchment-600 w-5'
                  : 'bg-parchment-300'
              }`}
            />
          ))}
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex flex-col items-center text-center max-w-xs">
        {/* 图标 */}
        <div className="text-6xl mb-6 animate-bounce-in">
          {slide.icon}
        </div>

        {/* 标题 */}
        <h1 className="text-2xl font-semibold text-parchment-800 mb-2">
          {slide.title}
        </h1>

        {/* 副标题 */}
        <p className="text-sm font-medium text-parchment-500 mb-5">
          {slide.subtitle}
        </p>

        {/* 描述 */}
        <p className="text-sm text-parchment-600 leading-relaxed whitespace-pre-line">
          {slide.description}
        </p>
      </div>

      {/* 底部按钮 */}
      <div className="absolute bottom-12 left-6 right-6">
        <button
          onClick={handleNext}
          className="w-full py-3.5 bg-parchment-700 text-white rounded-2xl text-base font-semibold
                     hover:bg-parchment-800 active:scale-[0.98] transition-all shadow-lg shadow-parchment-700/20"
        >
          {isLast ? '开始使用' : '继续'}
        </button>
      </div>

      {/* 动画 */}
      <style jsx>{`
        @keyframes bounceIn {
          0% { transform: scale(0.3); opacity: 0; }
          50% { transform: scale(1.08); }
          70% { transform: scale(0.95); }
          100% { transform: scale(1); opacity: 1; }
        }
        .animate-bounce-in {
          animation: bounceIn 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}
