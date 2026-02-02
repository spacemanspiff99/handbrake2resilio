import { test, expect } from '@playwright/test';

test.describe('Workflows', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.route('**/api/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          token: 'fake-token',
          user: { id: 1, username: 'admin', role: 'admin' }
        })
      });
    });
    
    await page.route('**/api/auth/verify', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          valid: true,
          user: { id: 1, username: 'admin', role: 'admin' }
        })
      });
    });

    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');
  });

  test('should open new job modal and browse files', async ({ page }) => {
    // Mock filesystem browse
    await page.route('**/api/filesystem/browse?path=*', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                path: '/mnt',
                items: [
                    { name: 'media', type: 'directory', path: '/mnt/media' },
                    { name: 'video.mp4', type: 'file', path: '/mnt/video.mp4', size: 1024 }
                ]
            })
        });
    });

    // Mock queue add
    await page.route('**/api/queue', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Job added' })
        });
    });

    // Open Modal
    await page.click('text=New Job');
    
    // Click Browse for Input
    const browseButtons = await page.locator('button:has-text("Browse")');
    await browseButtons.first().click();
    
    // Check if file browser appears
    await expect(page.getByText('/mnt')).toBeVisible();
    await expect(page.getByText('media')).toBeVisible();
    
    // Select file
    await page.click('text=video.mp4');
    
    // Check if input is populated
    await expect(page.locator('input[placeholder="Select a video file..."]')).toHaveValue('/mnt/video.mp4');
    
    // Select output (simplified for test)
    await browseButtons.nth(1).click();
    await page.click('text=Select This Folder');
    
    // Submit
    await page.click('button:has-text("Start Job")');
    
    // Toast should appear
    await expect(page.getByText('Job added to queue')).toBeVisible();
  });
});