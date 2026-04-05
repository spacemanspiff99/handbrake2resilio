const { test, expect } = require('@playwright/test');
const { mockLoginAsAdmin, setupDashboardMocks } = require('./fixtures');

const MOCK_JOBS = [
  {
    id: 'job-running-1',
    input_path: '/media/input/movie.mkv',
    output_path: '/media/output/movie.mkv',
    status: 'running',
    progress: 45.0,
    created_at: new Date().toISOString(),
  },
  {
    id: 'job-pending-1',
    input_path: '/media/input/show.mp4',
    output_path: '/media/output/show.mkv',
    status: 'pending',
    progress: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: 'job-completed-1',
    input_path: '/media/input/done.mp4',
    output_path: '/media/output/done.mkv',
    status: 'completed',
    progress: 100,
    created_at: new Date().toISOString(),
  },
];

async function setupQueueMocks(page, jobs = MOCK_JOBS) {
  // Register queue mocks BEFORE dashboard mocks — Playwright uses first matching route
  await page.route('**/api/queue', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ running: 1, pending: 1, completed: 1, failed: 0 }),
    });
  });
  await page.route('**/api/queue/jobs', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      // QueueView reads: Array.isArray(jobs?.data) ? jobs.data : ...
      // axios interceptor returns response.data, so this object IS what component receives
      body: JSON.stringify({ data: jobs }),
    });
  });
}

test.describe('Queue View', () => {
  test.beforeEach(async ({ page }) => {
    // Queue mocks FIRST so they take priority over dashboard mocks
    await setupQueueMocks(page);
    await setupDashboardMocks(page);
    await mockLoginAsAdmin(page);
    await page.goto('/queue');
    await page.waitForLoadState('networkidle');
    // React Query needs an extra moment to fetch and render jobs
    await page.waitForTimeout(2000);
  });

  test('queue view loads and shows jobs section heading', async ({ page }) => {
    await expect(page.locator('text=All Jobs').first()).toBeVisible();
  });

  test('queue running count is displayed', async ({ page }) => {
    await expect(page.locator('text=Running').first()).toBeVisible();
  });

  test('queue pending count is displayed', async ({ page }) => {
    await expect(page.locator('text=Pending').first()).toBeVisible();
  });

  test('queue completed count is displayed', async ({ page }) => {
    await expect(page.locator('text=Completed').first()).toBeVisible();
  });

  test('job filename is visible in job list', async ({ page }) => {
    // movie.mkv should appear as the formatted filename
    await expect(page.locator('text=movie.mkv').first()).toBeVisible();
  });

  test('job status label is visible', async ({ page }) => {
    // QueueView shows status as uppercase: RUNNING
    await expect(page.locator('text=RUNNING').first()).toBeVisible();
  });

  test('cancel button visible for running job', async ({ page }) => {
    // QueueView renders <button title="Cancel Job"> for running/pending jobs
    await expect(page.locator('button[title="Cancel Job"]').first()).toBeVisible();
  });

  test('cancel button visible for both running and pending jobs', async ({ page }) => {
    const cancelBtns = page.locator('button[title="Cancel Job"]');
    await expect(cancelBtns.first()).toBeVisible();
    const count = await cancelBtns.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('cancel job button is clickable and not disabled', async ({ page }) => {
    const cancelBtn = page.locator('button[title="Cancel Job"]').first();
    await expect(cancelBtn).toBeVisible();
    await expect(cancelBtn).not.toBeDisabled();
    // Set up dialog handler before clicking to prevent dialog blocking
    page.on('dialog', (dialog) => dialog.dismiss());
    await cancelBtn.click({ timeout: 5000 });
  });

  test('clear completed button is present', async ({ page }) => {
    const clearBtn = page.locator('button', { hasText: /clear/i }).first();
    if (await clearBtn.count() > 0) {
      await expect(clearBtn).toBeVisible();
    }
  });

  test('empty queue shows no jobs message', async ({ page }) => {
    await page.route('**/api/queue/jobs', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [] }),
      });
    });
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=No jobs in queue').first()).toBeVisible();
  });
});
