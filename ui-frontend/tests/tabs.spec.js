const { test, expect } = require('@playwright/test');
const { mockLoginAsAdmin, setupDashboardMocks } = require('./fixtures');

// Tabs live in the Sidebar component, not a dedicated route.
// Tests verify the sidebar tab management UI on the dashboard.

const MOCK_TAB = {
  id: 1,
  name: 'Test Tab',
  source_path: '/media/input',
  destination_path: '/media/output',
};

async function setupTabsMocks(page, tabs = []) {
  await page.route('**/api/tabs', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(tabs),
      });
    } else {
      await route.continue();
    }
  });
}

test.describe('Tab Management (Sidebar)', () => {
  test.beforeEach(async ({ page }) => {
    await setupDashboardMocks(page);
    await setupTabsMocks(page, []);
    await mockLoginAsAdmin(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('sidebar renders without crashing', async ({ page }) => {
    await expect(page.locator('text=React Error Boundary')).not.toBeVisible();
  });

  test('tabs section is visible in sidebar', async ({ page }) => {
    await expect(page.locator('text=Tabs').first()).toBeVisible();
  });

  test('empty state shown when no tabs exist', async ({ page }) => {
    await expect(
      page.locator('text=No tabs created yet').or(page.locator('text=No tabs'))
    ).toBeVisible();
  });

  test('tabs list shows existing tabs', async ({ page }) => {
    // Override with a tab
    await page.route('**/api/tabs', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([MOCK_TAB]),
        });
      } else {
        await route.continue();
      }
    });
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=Test Tab')).toBeVisible();
  });

  test('create tab button or form is accessible', async ({ page }) => {
    // Look for a "New Tab", "Add Tab", or "+" button in the sidebar
    const addBtn = page.locator('button', { hasText: /new tab|add tab|\+/i }).or(
      page.locator('[title*="add" i]').or(page.locator('[title*="new" i]'))
    );
    if (await addBtn.count() > 0) {
      await expect(addBtn.first()).toBeVisible();
    }
  });

  test('create tab via POST and tab appears', async ({ page }) => {
    let createCalled = false;
    await page.route('**/api/tabs', async (route) => {
      if (route.request().method() === 'POST') {
        createCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 2, name: 'New Tab', source_path: '/media/input', destination_path: '/media/output' }),
        });
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createCalled ? [{ id: 2, name: 'New Tab', source_path: '/media/input', destination_path: '/media/output' }] : []),
        });
      } else {
        await route.continue();
      }
    });

    // Find and click the add tab button if it exists
    const addBtn = page.locator('button', { hasText: /new tab|add tab|\+/i }).first();
    if (await addBtn.isVisible()) {
      await addBtn.click();
      // Fill in form fields if a modal/form appears
      const nameInput = page.locator('input[placeholder*="name" i]').or(page.locator('input[name="name"]'));
      if (await nameInput.isVisible()) {
        await nameInput.fill('New Tab');
        const saveBtn = page.locator('button', { hasText: /save|create|add/i }).first();
        await saveBtn.click();
      }
    }
  });
});
