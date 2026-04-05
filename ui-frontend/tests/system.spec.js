const { test, expect } = require('@playwright/test');
const { mockLoginAsAdmin, setupDashboardMocks } = require('./fixtures');

test.describe('System View', () => {
  test.beforeEach(async ({ page }) => {
    await setupDashboardMocks(page);
    await mockLoginAsAdmin(page);
    await page.goto('/system');
    await page.waitForLoadState('networkidle');
  });

  test('system view loads without crashing', async ({ page }) => {
    await expect(page.locator('text=React Error Boundary')).not.toBeVisible();
    await expect(page.locator('body')).toBeVisible();
  });

  test('system monitoring heading is displayed', async ({ page }) => {
    // SystemView shows "System Monitoring" heading
    await expect(page.locator('h1', { hasText: 'System Monitoring' })).toBeVisible();
  });

  test('gateway status card is displayed', async ({ page }) => {
    await expect(page.locator('text=Gateway status').first()).toBeVisible();
  });

  test('gateway shows healthy status from mock', async ({ page }) => {
    // Mock returns status: 'healthy'
    await expect(page.locator('text=healthy').first()).toBeVisible();
  });

  test('dependencies section is displayed', async ({ page }) => {
    await expect(page.locator('text=Dependencies').first()).toBeVisible();
  });

  test('database dependency is shown', async ({ page }) => {
    await expect(page.locator('text=Database').first()).toBeVisible();
  });

  test('graceful display when backend is unreachable', async ({ page }) => {
    await page.route('**/health', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'unhealthy' }),
      });
    });
    await page.reload();
    await page.waitForLoadState('networkidle');
    // Should not crash
    await expect(page.locator('text=React Error Boundary')).not.toBeVisible();
    await expect(page.locator('body')).toBeVisible();
  });
});
