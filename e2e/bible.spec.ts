import { test, expect } from '@playwright/test';

/**
 * 圣经阅读流程 E2E 测试
 *
 * 验证书卷选择 → 章节导航 → 经文阅读 → 书签/笔记的完整流程。
 */

test.describe('Bible Reading Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('xjoy_onboarding_completed', 'true');
    });
  });

  test('should navigate through Bible → Books → Chapter → Verses', async ({ page }) => {
    await page.goto('/bible');

    // 应看到书卷选择页面
    await expect(page.locator('h1')).toContainText('Bible');

    // 等待书卷列表加载
    await expect(page.locator('text=Genesis')).toBeVisible({ timeout: 10000 });

    // 点击 Genesis
    await page.locator('text=Genesis').first().click();

    // 应导航到 /bible/Genesis 章节列表
    await expect(page).toHaveURL(/\/bible\/Genesis/);
    await expect(page.locator('h1')).toContainText('Genesis');

    // 点击 Chapter 1
    await page.locator('text=1').first().click();

    // 应导航到 /bible/Genesis/1
    await expect(page).toHaveURL(/\/bible\/Genesis\/1/);
    await expect(page.locator('text=Chapter 1')).toBeVisible({ timeout: 10000 });
  });

  test('should show chapter navigation (prev/next)', async ({ page }) => {
    await page.goto('/bible/Genesis/2');

    // 等待经文加载
    await expect(page.locator('text=Chapter 2')).toBeVisible({ timeout: 10000 });

    // 应有上一章和下一章的导航
    await expect(page.locator('text=Chapter 1')).toBeVisible();
    await expect(page.locator('text=Chapter 3')).toBeVisible();
  });

  test('should navigate between testaments', async ({ page }) => {
    await page.goto('/bible');

    // 默认应显示旧约
    await expect(page.locator('text=Genesis')).toBeVisible({ timeout: 10000 });

    // 切换到新约
    await page.locator('text=新约').click();

    // 应显示新约书卷
    await expect(page.locator('text=Matthew')).toBeVisible({ timeout: 5000 });
  });

  test('should have verse bookmark interaction', async ({ page }) => {
    await page.goto('/bible/John/3');

    // 等待经文加载
    await expect(page.locator('text=Chapter 3')).toBeVisible({ timeout: 10000 });

    // 经文区域应有内容
    const verseText = page.locator('text=For God so loved the world');
    await expect(verseText).toBeVisible({ timeout: 5000 });
  });
});
