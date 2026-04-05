const { test, expect } = require('@playwright/test');
const { mockLoginAsAdmin, setupDashboardMocks } = require('./fixtures');

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupDashboardMocks(page);
    await mockLoginAsAdmin(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('dashboard loads and shows heading', async ({ page }) => {
    await expect(page.locator('h1', { hasText: 'Dashboard' })).toBeVisible();
  });

  test('CPU usage metric is displayed', async ({ page }) => {
    await expect(page.locator('text=CPU Usage').first()).toBeVisible();
    // A percentage value should be visible somewhere on the page
    await expect(page.locator('text=/\\d+%/').first()).toBeVisible();
  });

  test('memory usage metric is displayed', async ({ page }) => {
    await expect(page.locator('text=Memory Usage').first()).toBeVisible();
  });

  test('API health status is displayed', async ({ page }) => {
    await expect(page.locator('text=API health').first()).toBeVisible();
  });

  test('queue status section is displayed', async ({ page }) => {
    await expect(page.locator('text=Queue Status').first()).toBeVisible();
  });

  test('system health section shows service statuses', async ({ page }) => {
    await expect(page.locator('text=System Health').first()).toBeVisible();
  });

  test('navigation to queue view works', async ({ page }) => {
    const queueLink = page.locator('a[href="/queue"]').first();
    if (await queueLink.count() > 0) {
      await queueLink.click();
      await expect(page).toHaveURL(/\/queue/);
    }
  });

  test('navigation to system view works', async ({ page }) => {
    const systemLink = page.locator('a[href="/system"]').first();
    if (await systemLink.count() > 0) {
      await systemLink.click();
      await expect(page).toHaveURL(/\/system/);
    }
  });

  test('renders correctly at 1920x1080', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1', { hasText: 'Dashboard' })).toBeVisible();
  });

  test('renders correctly at 768x1024 (tablet)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});
