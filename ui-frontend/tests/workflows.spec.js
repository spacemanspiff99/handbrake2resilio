const { test, expect } = require('@playwright/test');
const { setupAuthMocks, setupDashboardMocks } = require('./fixtures');

// FileBrowser expects: { success: true, data: { items: [...], current_path: '...' } }
const MOCK_FILESYSTEM_RESPONSE = {
  success: true,
  data: {
    current_path: '/mnt',
    items: [
      { name: '..', is_directory: true, path: '/' },
      { name: 'media', is_directory: true, path: '/mnt/media' },
      { name: 'video.mp4', is_directory: false, path: '/mnt/video.mp4', size: 1024 },
    ],
  },
};

test.describe('Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthMocks(page);
    await setupDashboardMocks(page);
    await page.route('**/api/filesystem/browse**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_FILESYSTEM_RESPONSE),
      });
    });
    await page.route('**/api/queue/jobs', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [] }),
      });
    });
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
  });

  test('should open new job modal and browse files', async ({ page }) => {
    // Mock queue POST for job submission
    await page.route('**/api/queue', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Job added' }),
        });
      } else {
        await route.continue();
      }
    });

    // Open New Job modal
    const newJobBtn = page.locator('button', { hasText: /new job/i }).first();
    await expect(newJobBtn).toBeVisible({ timeout: 5000 });
    await newJobBtn.click();

    // Modal should appear
    await expect(page.locator('text=Add New Conversion Job')).toBeVisible({ timeout: 5000 });

    // Click Browse for input file
    const browseButtons = page.locator('button', { hasText: /browse/i });
    await browseButtons.first().click();

    // FileBrowser renders current_path in header and items in list
    await expect(page.locator('text=/mnt').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=media').first()).toBeVisible({ timeout: 5000 });

    // Select the video file
    await page.locator('text=video.mp4').first().click();

    // Input path should be populated
    await expect(
      page.locator('input[placeholder="Select a video file..."]')
    ).toHaveValue('/mnt/video.mp4', { timeout: 5000 });
  });
});
