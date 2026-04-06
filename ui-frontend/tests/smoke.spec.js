const { test, expect } = require('@playwright/test');

/**
 * Smoke tests against a live running stack.
 * These tests are SKIPPED unless USE_LIVE_API=true is set.
 * Run with: USE_LIVE_API=true BASE_URL=http://localhost:7474 npx playwright test tests/smoke.spec.js
 */
const USE_LIVE_API = process.env.USE_LIVE_API === 'true';
const targetURL = process.env.BASE_URL || 'http://localhost:3000';

test.describe('Smoke Test - Production Verification', () => {
  test.beforeEach(async ({}) => {
    if (!USE_LIVE_API) {
      test.skip(true, 'Skipped: set USE_LIVE_API=true to run live stack smoke tests');
    }
  });

  test('should perform a real login on dev server', async ({ page }) => {
    await page.goto(targetURL);
    await page.waitForURL('**/login');
    await expect(page).toHaveURL(`${targetURL}/login`);

    await page.fill('input[name="username"]', 'testuser_phase09');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await page.waitForURL(`${targetURL}/`, { timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByText('HandBrake2Resilio UI')).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Job' })).toBeVisible();
  });

  test('should verify file browser is accessible', async ({ page }) => {
    await page.goto(targetURL);
    await page.waitForURL('**/login');
    await page.fill('input[name="username"]', 'testuser_phase09');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(`${targetURL}/`);

    await page.click('button:has-text("New Job")');
    await expect(page.getByText('Add New Conversion Job')).toBeVisible();
    await page.click('button:has-text("Browse") >> nth=0');
    await expect(page.getByText('mnt')).toBeVisible({ timeout: 10000 });
  });
});
