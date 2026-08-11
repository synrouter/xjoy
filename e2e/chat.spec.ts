import { test, expect } from '@playwright/test';

/**
 * AI 聊天流程 E2E 测试
 *
 * 验证聊天页面能正常加载、显示欢迎消息、发送问题和接收回复。
 */

test.describe('AI Chat Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('xjoy_onboarding_completed', 'true');
    });
  });

  test('should load chat page with welcome message', async ({ page }) => {
    await page.goto('/chat');

    // 检查页面标题
    await expect(page.locator('h1')).toContainText('AI Study Helper');

    // 应有欢迎消息
    await expect(page.locator('text=欢迎来到 Xjoy')).toBeVisible({ timeout: 5000 });
  });

  test('should show suggestion chips', async ({ page }) => {
    await page.goto('/chat');

    // 应显示建议问题
    await expect(page.locator('text=John 3:16')).toBeVisible();
    await expect(page.locator('text=关于爱的教导')).toBeVisible();
    await expect(page.locator('text=十诫')).toBeVisible();
  });

  test('should have textarea for user input', async ({ page }) => {
    await page.goto('/chat');

    // 应有输入框
    const textarea = page.locator('textarea[placeholder*="输入您的问题"]');
    await expect(textarea).toBeVisible();

    // 应有发送按钮
    const sendButton = page.locator('text=发送');
    await expect(sendButton).toBeVisible();
  });

  test('should send message and show user message in chat', async ({ page }) => {
    await page.goto('/chat');

    // 输入问题
    const textarea = page.locator('textarea');
    await textarea.fill('What is faith?');

    // 发送
    await page.locator('text=发送').click();

    // 应显示用户消息
    await expect(page.locator('text=What is faith?').last()).toBeVisible({ timeout: 5000 });
  });

  test('should show footer disclaimer', async ({ page }) => {
    await page.goto('/chat');

    // 应有免责声明
    await expect(page.locator('text=Xjoy 基于 KJV 经文回答')).toBeVisible();
  });
});
