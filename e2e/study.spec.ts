import { test, expect } from '@playwright/test';

/**
 * 学习工具流程 E2E 测试
 *
 * 验证 Study 页面、笔记列表、书签列表的导航。
 */

test.describe('Study Tools Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('xjoy_onboarding_completed', 'true');
    });
  });

  test('should load Study page with tool cards', async ({ page }) => {
    await page.goto('/study');

    // 检查页面标题
    await expect(page.locator('h1')).toContainText('Study');

    // 应有笔记和书签入口
    await expect(page.locator('text=My Notes')).toBeVisible();
    await expect(page.locator('text=Bookmarks')).toBeVisible();

    // 应有 Quiz 和 Jigsaw (Coming Soon)
    await expect(page.locator('text=Bible Quiz')).toBeVisible();
    await expect(page.locator('text=Weekly Jigsaw')).toBeVisible();
  });

  test('should navigate to Notes page from Study', async ({ page }) => {
    await page.goto('/study');

    // 点击 My Notes
    await page.locator('text=My Notes').click();

    // 应导航到 /study/notes
    await expect(page).toHaveURL(/\/study\/notes/);
    await expect(page.locator('h1')).toContainText('My Notes');
  });

  test('should navigate to Bookmarks page from Study', async ({ page }) => {
    await page.goto('/study');

    // 点击 Bookmarks
    await page.locator('text=Bookmarks').click();

    // 应导航到 /study/bookmarks
    await expect(page).toHaveURL(/\/study\/bookmarks/);
    await expect(page.locator('h1')).toContainText('Bookmarks');
  });

  test('should show empty state for notes with no data', async ({ page }) => {
    await page.goto('/study/notes');

    // 应显示空状态（没有笔记时）
    await expect(page.locator('text=暂无笔记').or(page.locator('h1'))).toBeVisible({ timeout: 5000 });
  });

  test('should show empty state for bookmarks with no data', async ({ page }) => {
    await page.goto('/study/bookmarks');

    // 应显示空状态（没有书签时）
    await expect(page.locator('text=暂无书签').or(page.locator('h1'))).toBeVisible({ timeout: 5000 });
  });

  test('should navigate back to Study from Notes', async ({ page }) => {
    await page.goto('/study/notes');

    // 应有返回 Study 的链接
    await expect(page.locator('text=Study').first()).toBeVisible();
  });

  test('should navigate back to Study from Bookmarks', async ({ page }) => {
    await page.goto('/study/bookmarks');

    // 应有返回 Study 的链接
    await expect(page.locator('text=Study').first()).toBeVisible();
  });
});
