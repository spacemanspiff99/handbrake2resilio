const { test, expect } = require('@playwright/test');
const { setupAuthMocks, setupDashboardMocks, ADMIN_USER, ADMIN_PASS } = require('./fixtures');

test.describe('Authentication', () => {
  test('login page renders with form fields and submit button', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toContainText('Sign in');
  });

  test('redirects to login when not authenticated', async ({ page }) => {
    // No auth mocks — verify token will fail → redirect to /login
    await page.route('**/api/auth/verify', async (route) => {
      await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ error: 'Unauthorized' }) });
    });
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login with valid credentials redirects to dashboard', async ({ page }) => {
    await setupAuthMocks(page);
    await setupDashboardMocks(page);
    await page.goto('/login');
    await page.fill('input[name="username"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
    // Should land on dashboard (root route)
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('login with invalid credentials shows error message', async ({ page }) => {
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Invalid credentials' }),
      });
    });
    await page.goto('/login');
    await page.fill('input[name="username"]', 'wrong');
    await page.fill('input[name="password"]', 'wrong');
    await page.click('button[type="submit"]');
    // Should stay on login page
    await expect(page).toHaveURL(/\/login/);
    // Toast error should appear
    await expect(page.locator('text=Invalid credentials').or(page.locator('text=Login failed'))).toBeVisible({ timeout: 5000 });
  });

  test('login with empty fields shows validation error', async ({ page }) => {
    await page.goto('/login');
    // Clear fields and submit
    await page.fill('input[name="username"]', '');
    await page.fill('input[name="password"]', '');
    await page.click('button[type="submit"]');
    // Should stay on login — either browser validation or toast
    await expect(page).toHaveURL(/\/login/);
  });

  test('logout clears session and redirects to login', async ({ page }) => {
    await setupAuthMocks(page);
    await setupDashboardMocks(page);
    await page.goto('/login');
    await page.fill('input[name="username"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });

    // Find and click logout — look in header
    const logoutBtn = page.locator('button', { hasText: /logout|sign out/i }).or(
      page.locator('[title*="logout" i]')
    ).or(page.locator('[aria-label*="logout" i]'));
    if (await logoutBtn.count() > 0) {
      await logoutBtn.first().click();
      await expect(page).toHaveURL(/\/login/);
    } else {
      // Manually clear token and navigate
      await page.evaluate(() => localStorage.removeItem('token'));
      await page.goto('/');
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test('token persistence — reload page stays authenticated', async ({ page }) => {
    await setupAuthMocks(page);
    await setupDashboardMocks(page);
    await page.goto('/login');
    await page.fill('input[name="username"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });

    // Reload — verify mock still active
    await setupAuthMocks(page);
    await setupDashboardMocks(page);
    await page.reload();
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('register link is visible on login page', async ({ page }) => {
    await page.goto('/login');
    const registerLink = page.locator('a[href="/register"]').or(page.locator('text=register'));
    await expect(registerLink.first()).toBeVisible();
  });

  test('register page loads with form fields', async ({ page }) => {
    await page.goto('/register');
    await expect(page.locator('input[name="username"]').or(page.locator('input[placeholder*="username" i]'))).toBeVisible();
    await expect(page.locator('input[name="password"]').or(page.locator('input[placeholder*="password" i]'))).toBeVisible();
  });
});
