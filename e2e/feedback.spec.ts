import { test, expect } from '@playwright/test';

/**
 * 反馈流程 E2E 测试
 *
 * 验证反馈页面能正常加载、选择类别、评分、提交反馈。
 */

test.describe('Feedback Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('xjoy_onboarding_completed', 'true');
    });
  });

  test('should load feedback page', async ({ page }) => {
    await page.goto('/feedback');

    // 检查页面标题
    await expect(page.locator('h1')).toContainText('Feedback');

    // 应显示所有 6 个类别按钮
    await expect(page.locator('text=AI 聊天准确度')).toBeVisible();
    await expect(page.locator('text=阅读体验')).toBeVisible();
    await expect(page.locator('text=整体印象')).toBeVisible();
    await expect(page.locator('text=功能建议')).toBeVisible();
    await expect(page.locator('text=Bug 报告')).toBeVisible();
    await expect(page.locator('text=其他')).toBeVisible();
  });

  test('should show floating feedback button on other pages', async ({ page }) => {
    await page.goto('/');

    // 浮动反馈按钮应存在
    const feedbackButton = page.locator('a[title="发送反馈"]');
    await expect(feedbackButton).toBeVisible();

    // 点击应导航到 /feedback
    await feedbackButton.click();
    await expect(page).toHaveURL(/\/feedback/);
  });

  test('should select category and show rating stars', async ({ page }) => {
    await page.goto('/feedback');

    // 点击 "AI 聊天准确度"（有评分功能）
    await page.locator('text=AI 聊天准确度').click();

    // 应显示星级评分
    const stars = page.locator('[aria-label="5 星"]');
    await expect(stars).toBeVisible();

    // 点击 5 星评分
    await stars.click();
  });

  test('should require category and message to submit', async ({ page }) => {
    await page.goto('/feedback');

    // 提交按钮应处于禁用状态（未选类别、未填内容）
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeDisabled();

    // 选择类别
    await page.locator('text=其他').click();

    // 填写反馈内容
    await page.locator('textarea[placeholder*="在这里写下你的反馈"]').fill('测试反馈内容');

    // 现在提交按钮应可用
    await expect(submitButton).toBeEnabled();
  });
});
