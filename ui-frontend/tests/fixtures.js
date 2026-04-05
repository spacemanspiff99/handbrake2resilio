/**
 * Shared Playwright test helpers for handbrake2resilio UI tests.
 */

const ADMIN_USER = 'admin';
const ADMIN_PASS = 'admin123';

/**
 * Set up all common API mocks needed for an authenticated session.
 * Call before page.goto() to ensure mocks are in place.
 */
async function setupAuthMocks(page) {
  await page.route('**/api/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        token: 'test-jwt-token',
        user: { id: 1, username: 'admin', role: 'admin' },
      }),
    });
  });
  await page.route('**/api/auth/verify', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        valid: true,
        user: { id: 1, username: 'admin', role: 'admin' },
      }),
    });
  });
}

/**
 * Set up mocks for dashboard data (health, system load, queue, jobs).
 */
async function setupDashboardMocks(page) {
  await page.route('**/health', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        database: 'sqlite',
        handbrake_service: true,
      }),
    });
  });
  await page.route('**/api/system/load', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        cpu_percent: 25,
        memory_percent: 45,
        disk_percent: 60,
        disk_free_gb: 100,
        memory_available_gb: 8,
      }),
    });
  });
  await page.route('**/api/queue', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ running: 0, pending: 0, completed: 5, failed: 0 }),
    });
  });
  // Note: **/api/queue/jobs is intentionally NOT mocked here.
  // Tests that need specific job data (queue.spec.js) should mock it themselves
  // BEFORE calling setupDashboardMocks, since Playwright uses LIFO route ordering.
  await page.route('**/api/tabs', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
}

/**
 * Mock login — bypasses real API for isolated UI tests.
 * Sets up auth mocks then performs the login flow.
 */
async function mockLoginAsAdmin(page) {
  await setupAuthMocks(page);
  await page.goto('/login');
  await page.fill('input[name="username"]', ADMIN_USER);
  await page.fill('input[name="password"]', ADMIN_PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
}

/**
 * Log in as admin against a real running API.
 */
async function loginAsAdmin(page) {
  await page.goto('/login');
  await page.fill('input[name="username"]', ADMIN_USER);
  await page.fill('input[name="password"]', ADMIN_PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
}

/**
 * Wait for API to be reachable (for live stack tests).
 */
async function waitForApiReady(page, apiUrl = 'http://localhost:8080') {
  let attempts = 0;
  while (attempts < 10) {
    try {
      const resp = await page.request.get(`${apiUrl}/health`);
      if (resp.ok()) return true;
    } catch (_) {}
    await page.waitForTimeout(2000);
    attempts++;
  }
  throw new Error('API not ready after 20 seconds');
}

module.exports = {
  loginAsAdmin,
  mockLoginAsAdmin,
  setupAuthMocks,
  setupDashboardMocks,
  waitForApiReady,
  ADMIN_USER,
  ADMIN_PASS,
};
