import { test, expect } from '@playwright/test';

/**
 * Onboarding 引导流程 E2E 测试
 *
 * 验证首次访问时显示引导流程、轮播、跳过和完成。
 */

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 清除 localStorage 以模拟首次访问
    await page.goto('/');
    await page.evaluate(() => localStorage.removeItem('xjoy_onboarding_completed'));
  });

  test('should show onboarding on first visit', async ({ page }) => {
    await page.goto('/');

    // 应显示引导页面
    await expect(page.locator('text=欢迎来到 Xjoy')).toBeVisible({ timeout: 5000 });

    // 应有"跳过"按钮
    await expect(page.locator('text=跳过')).toBeVisible();
  });

  test('should navigate through all slides', async ({ page }) => {
    await page.goto('/');

    // 第一页：欢迎
    await expect(page.locator('text=欢迎来到 Xjoy')).toBeVisible();
    await page.locator('text=继续').click();

    // 第二页：每日经文
    await expect(page.locator('text=每日经文')).toBeVisible();
    await page.locator('text=继续').click();

    // 第三页：阅读圣经
    await expect(page.locator('text=阅读圣经')).toBeVisible();
    await page.locator('text=继续').click();

    // 第四页：AI 研经助手
    await expect(page.locator('text=AI 研经助手')).toBeVisible();
    await page.locator('text=继续').click();

    // 第五页：学习工具
    await expect(page.locator('text=学习工具')).toBeVisible();
    await page.locator('text=继续').click();

    // 第六页：开始旅程 → 按钮文字变为"开始使用"
    await expect(page.locator('text=开始你的旅程')).toBeVisible();
    const startButton = page.locator('text=开始使用');
    await expect(startButton).toBeVisible();
  });

  test('should skip onboarding', async ({ page }) => {
    await page.goto('/');

    // 点击"跳过"
    await page.locator('text=跳过').click();

    // 等待引导层消失
    await expect(page.locator('text=欢迎来到 Xjoy')).not.toBeVisible({ timeout: 5000 });

    // 应显示主应用（Today 页面）
    await expect(page.locator('h1').first()).toContainText('Today', { timeout: 5000 });
  });

  test('should complete onboarding and show main app', async ({ page }) => {
    await page.goto('/');

    // 快速跳过所有页面
    for (let i = 0; i < 5; i++) {
      await page.locator('text=继续').click();
    }

    // 最后一页，点击"开始使用"
    await page.locator('text=开始使用').click();

    // 等待引导层消失
    await expect(page.locator('text=开始你的旅程')).not.toBeVisible({ timeout: 5000 });

    // 应显示主应用
    await expect(page.locator('h1').first()).toContainText('Today', { timeout: 5000 });
  });

  test('should not show onboarding on subsequent visits', async ({ page }) => {
    // 先完成一次引导
    await page.goto('/');
    await page.locator('text=跳过').click();
    await expect(page.locator('text=欢迎来到 Xjoy')).not.toBeVisible({ timeout: 5000 });

    // 刷新页面，不应再显示引导
    await page.goto('/');
    await expect(page.locator('h1').first()).toContainText('Today', { timeout: 5000 });
    await expect(page.locator('text=欢迎来到 Xjoy')).not.toBeVisible({ timeout: 3000 });
  });
});
