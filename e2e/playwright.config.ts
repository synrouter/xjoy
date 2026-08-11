import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 核心用户流程测试：
 * - 打开 App → Today 页面 → 查看每日经文
 * - Bible 标签 → 选择书卷 → 阅读章节 → 书签/笔记
 * - AI Chat → 发送问题 → 查看回复
 * - Study → 管理笔记和书签
 * - Me → 查看统计和进度
 */

export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 7'] },
    },
  ],

  webServer: [
    {
      command: 'cd ../packages/api && ./venv/bin/python -m uvicorn xjoy.api:app --host 0.0.0.0 --port 8000',
      url: 'http://localhost:8000/api/health',
      reuseExistingServer: !process.env.CI,
      timeout: 15000,
    },
    {
      command: 'cd ../packages/app && npx next dev -p 3000',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
  ],
});
