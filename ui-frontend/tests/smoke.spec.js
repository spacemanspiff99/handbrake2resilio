const { test, expect } = require('@playwright/test');
const { ADMIN_USER, ADMIN_PASS } = require('./fixtures');

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

    await page.fill('input[name="username"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PASS);
    await page.click('button[type="submit"]');

    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should have Tailwind CSS loaded (not unstyled)', async ({ page }) => {
    await page.goto(targetURL);
    await page.waitForURL('**/login');
    const ruleCount = await page.evaluate(() => {
      const sheets = Array.from(document.styleSheets);
      return sheets.reduce((sum, s) => {
        try { return sum + s.cssRules.length; } catch { return sum; }
      }, 0);
    });
    expect(ruleCount).toBeGreaterThan(50);
  });

  test('should verify file browser is accessible', async ({ page }) => {
    await page.goto(targetURL);
    await page.waitForURL('**/login');
    await page.fill('input[name="username"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });

    await page.click('button:has-text("New Job")');
    await expect(page.getByText('Add New Conversion Job')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Browse") >> nth=0');
    await expect(page.locator('text=media').or(page.locator('text=mnt')).or(page.locator('text=tmp'))).toBeVisible({ timeout: 10000 });
  });
});
