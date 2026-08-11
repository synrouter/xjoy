'use client';

import React from 'react';

interface Props {
  title: string;
  subtitle?: string;
  /** 是否显示底部分隔线，默认 false */
  bordered?: boolean;
  /** 右侧操作区域 */
  actions?: React.ReactNode;
}

/**
 * 统一的页面标题组件
 *
 * 所有页面使用此组件确保标题样式一致。
 * 子页面（如笔记列表、书签列表）使用 bordered 变体。
 */
export default function PageHeader({ title, subtitle, bordered = false, actions }: Props) {
  return (
    <header
      className={`shrink-0 px-5 pt-6 pb-3 ${
        bordered ? 'border-b border-parchment-200 bg-white' : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-parchment-800">{title}</h1>
          {subtitle && (
            <p className="text-xs text-parchment-400 mt-0.5">{subtitle}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
}
