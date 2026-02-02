import { test, expect } from '@playwright/test';

test.describe('Smoke Test - Production Verification', () => {
  const targetURL = 'http://192.168.10.18:3000';

  test('should perform a real login on dev server', async ({ page }) => {
    // Navigate to root, which should redirect to /login
    await page.goto(targetURL);
    
    // Wait for redirect to login page (this happens in client-side React)
    await page.waitForURL('**/login');
    await expect(page).toHaveURL(`${targetURL}/login`);

    // Fill in the real credentials created in Step 1
    await page.fill('input[name="username"]', 'testuser_phase09');
    await page.fill('input[name="password"]', 'password123');
    
    // Click login
    await page.click('button[type="submit"]');

    // Should redirect to dashboard (root)
    // Wait for navigation and check URL
    await page.waitForURL(`${targetURL}/`, { timeout: 10000 });
    
    // Verify we see some dashboard content
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByText('HandBrake2Resilio UI')).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Job' })).toBeVisible();
  });

  test('should verify file browser is accessible', async ({ page }) => {
    // Login first
    await page.goto(targetURL);
    await page.waitForURL('**/login');
    await page.fill('input[name="username"]', 'testuser_phase09');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(`${targetURL}/`);

    // Open "New Job" modal
    await page.click('button:has-text("New Job")');
    
    // Check if Modal is visible
    await expect(page.getByText('Add New Conversion Job')).toBeVisible();

    // Click Browse for input file
    await page.click('button:has-text("Browse") >> nth=0');
    
    // Look for /mnt/tv or /mnt/movies which should be there
    // These might take a second to load via the API
    await expect(page.getByText('mnt')).toBeVisible({ timeout: 10000 });
  });
});
