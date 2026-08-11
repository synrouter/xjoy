import { test, expect } from '@playwright/test';

/**
 * 标签导航 E2E 测试
 *
 * 验证底部 Tab 导航栏正常工作。
 */

test.describe('Tab Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('xjoy_onboarding_completed', 'true');
    });
  });

  test('should have four bottom tabs', async ({ page }) => {
    await page.goto('/');

    // 检查四个标签（限定在 nav 内，避免与页面标题冲突）
    const nav = page.locator('nav');
    await expect(nav.locator('text=Today')).toBeVisible();
    await expect(nav.locator('text=Bible')).toBeVisible();
    await expect(nav.locator('text=Study')).toBeVisible();
    await expect(nav.locator('text=Me')).toBeVisible();
  });

  test('should navigate to Bible tab', async ({ page }) => {
    await page.goto('/');

    // 点击 Bible 标签
    await page.locator('nav').locator('text=Bible').click();

    // 应导航到 /bible
    await expect(page).toHaveURL(/\/bible/);
    await expect(page.locator('h1')).toContainText('Bible');
  });

  test('should navigate to Study tab', async ({ page }) => {
    await page.goto('/');

    // 点击 Study 标签
    await page.locator('nav').locator('text=Study').click();

    // 应导航到 /study
    await expect(page).toHaveURL(/\/study/);
    await expect(page.locator('h1')).toContainText('Study');
  });

  test('should navigate to Me tab', async ({ page }) => {
    await page.goto('/');

    // 点击 Me 标签
    await page.locator('nav').locator('text=Me').click();

    // 应导航到 /me
    await expect(page).toHaveURL(/\/me/);
    await expect(page.locator('h1')).toContainText('Me');
  });

  test('should highlight active tab', async ({ page }) => {
    await page.goto('/bible');

    // Bible 标签应高亮（有下划线指示器）
    const bibleButton = page.locator('nav').locator('text=Bible').locator('..');
    // 检查激活状态通过父按钮上的颜色类
    await expect(bibleButton).toHaveClass(/text-parchment-700/);
  });
});
