import { test, expect } from '@playwright/test';

/**
 * Today 页面 E2E 测试
 *
 * 验证首页能正常加载、展示每日经文和快捷入口。
 */

test.describe('Today Page', () => {
  test.beforeEach(async ({ page }) => {
    // 跳过引导流程
    await page.addInitScript(() => {
      localStorage.setItem('xjoy_onboarding_completed', 'true');
    });
  });

  test('should load the Today page and show daily verse', async ({ page }) => {
    await page.goto('/');

    // 检查页面标题
    await expect(page.locator('h1')).toContainText('Today');

    // 检查每日经文卡片
    const verseCard = page.locator('text=Verse of the Day').first();
    await expect(verseCard).toBeVisible({ timeout: 10000 });

    // 等待经文加载完成（不应显示"加载中"）
    await expect(page.locator('text=加载中...')).not.toBeVisible({ timeout: 10000 });
  });

  test('should show quick action cards', async ({ page }) => {
    await page.goto('/');

    // 检查快捷入口
    await expect(page.locator('text=Read Bible')).toBeVisible();
    await expect(page.locator('text=AI Chat')).toBeVisible();
    await expect(page.locator('text=Search')).toBeVisible();
    await expect(page.locator('text=Psalm 23')).toBeVisible();
  });

  test('should navigate to Bible page from quick action', async ({ page }) => {
    await page.goto('/');

    // 点击 "Read Bible" 快捷入口
    await page.locator('text=Read Bible').click();

    // 应导航到 /bible
    await expect(page).toHaveURL(/\/bible/);
    await expect(page.locator('h1')).toContainText('Bible');
  });

  test('should navigate to Chat page from quick action', async ({ page }) => {
    await page.goto('/');

    // 点击 "AI Chat" 快捷入口
    await page.locator('text=AI Chat').click();

    // 应导航到 /chat
    await expect(page).toHaveURL(/\/chat/);
    await expect(page.locator('h1')).toContainText('AI Study Helper');
  });
});
