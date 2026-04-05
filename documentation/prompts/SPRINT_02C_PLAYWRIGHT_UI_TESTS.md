# SPRINT_02C — Comprehensive Playwright UI Tests (WEA-126)

💣

## Rules Reference
`.cursor/rules/rules.mdc` — always use browser simulation tool (Playwright), never assume frontend works.

## Model Recommendation
**Claude 4.6 Sonnet** (browser testing requires strong reasoning + MCP browser tool access)

## Personas (in sequence)
1. **QA Engineer** — design test coverage, identify edge cases
2. **Frontend Engineer** — understand component structure, selectors, routing

---

## Context

### Stack
- Frontend: React 18 (CRA), Tailwind, React Query, React Router
- Running at: `http://localhost:7474` (Docker) or `http://localhost:3000` (dev)
- API: `http://localhost:8080` (api-gateway)
- Auth: JWT stored in localStorage

### Existing test files (to be replaced/expanded)
- `ui-frontend/tests/auth.spec.js` — basic auth stubs (uses mocked API)
- `ui-frontend/tests/smoke.spec.js` — minimal smoke tests
- `ui-frontend/tests/workflows.spec.js` — workflow stubs

### Existing `playwright.config.js`
- baseURL: `http://localhost:3000`
- webServer: `npm start` (starts CRA dev server)
- Chromium only

### Key components
- `ui-frontend/src/components/QueueView.js` — job queue, cancel button
- `ui-frontend/src/components/` — Dashboard, FileBrowser, Tabs, System views
- `ui-frontend/src/context/AuthContext.js` — auth state
- `ui-frontend/src/services/api.js` — all API calls

---

## Tasks

### Task 1 — Update `ui-frontend/playwright.config.js`

```javascript
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: false,  // sequential for stability
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm start',
    url: process.env.BASE_URL || 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
  timeout: 30000,
});
```

### Task 2 — Create `ui-frontend/tests/fixtures.js`

```javascript
/**
 * Shared Playwright test helpers.
 */
const { expect } = require('@playwright/test');

const ADMIN_USER = 'admin';
const ADMIN_PASS = 'admin123';

/**
 * Log in as admin and store token in localStorage.
 * Uses real API if available, falls back to mock.
 */
async function loginAsAdmin(page) {
  await page.goto('/login');
  await page.fill('input[name="username"]', ADMIN_USER);
  await page.fill('input[name="password"]', ADMIN_PASS);
  await page.click('button[type="submit"]');
  // Wait for redirect away from /login
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
}

/**
 * Mock login — bypasses real API for isolated UI tests.
 */
async function mockLoginAsAdmin(page) {
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
  await page.goto('/login');
  await page.fill('input[name="username"]', ADMIN_USER);
  await page.fill('input[name="password"]', ADMIN_PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
}

/**
 * Wait for API to be reachable.
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

module.exports = { loginAsAdmin, mockLoginAsAdmin, waitForApiReady, ADMIN_USER, ADMIN_PASS };
```

### Task 3 — Rewrite `ui-frontend/tests/auth.spec.js`

Full coverage per WEA-126:
1. Login page renders — form fields visible, submit button present
2. Login with valid credentials (mocked) → redirects to dashboard
3. Login with invalid credentials (mocked 401) → shows error, stays on /login
4. Login with empty fields → shows validation error
5. Logout → clears token, redirects to /login
6. Protected route redirect → /dashboard without token → /login
7. Token persistence → login, reload, still authenticated (mocked verify)
8. Register new user (mocked) → create account, login with new credentials

### Task 4 — Create `ui-frontend/tests/dashboard.spec.js`

Full coverage per WEA-126:
1. Dashboard loads → shows system status section
2. System metrics displayed → CPU %, memory %, disk % visible
3. Job statistics displayed → active, completed, failed counts visible
4. Navigation → sidebar links to all sections work
5. Responsive layout → renders at 1920x1080 and 768x1024

Mock API responses for `/health` and `/api/system/load` and `/api/queue`.

### Task 5 — Create `ui-frontend/tests/queue.spec.js`

Full coverage per WEA-126:
1. Queue view loads → shows job list section
2. Queue status displayed → running, pending, completed counts
3. Job details visible → each job shows input path, status
4. Submit new job (mocked) → modal opens, form fills, job appears in list
5. Cancel job (mocked) → click cancel, status changes to cancelled
6. Clear completed (mocked) → click clear, completed jobs removed
7. Pause/resume queue buttons present

### Task 6 — Create `ui-frontend/tests/filebrowser.spec.js`

Full coverage per WEA-126:
1. File browser loads → shows directory listing section
2. Navigate directories (mocked) → click folder, breadcrumb updates
3. Go up directory → click `..`, navigates to parent
4. Video files displayed → .mp4, .mkv files shown with metadata
5. Non-existent path (mocked 404) → shows error message
6. Permission denied (mocked 403) → shows appropriate error

### Task 7 — Create `ui-frontend/tests/tabs.spec.js`

Full coverage per WEA-126:
1. Tabs list loads → shows existing tabs or empty state
2. Create tab (mocked) → fill name/source/destination, save
3. Edit tab (mocked) → modify settings, save changes
4. Delete tab (mocked) → confirm deletion, tab removed
5. Tab navigation → switching tabs shows correct content

### Task 8 — Create `ui-frontend/tests/system.spec.js`

Full coverage per WEA-126:
1. System view loads → shows resource usage
2. CPU/Memory/Disk metrics → values are numbers, 0-100% range
3. HandBrake service status → shows connected/disconnected
4. Error handling → graceful display when backend unreachable (mocked 503)

---

## Implementation Notes

### Selector Strategy
- Prefer `data-testid` attributes when available
- Fall back to semantic selectors: `role`, `label`, `placeholder`
- Avoid brittle CSS class selectors (Tailwind classes change)
- Add `data-testid` attributes to key elements if missing:
  - `data-testid="login-username"`, `data-testid="login-password"`, `data-testid="login-submit"`
  - `data-testid="cancel-job-btn"`, `data-testid="queue-list"`, `data-testid="job-status"`

### Mocking Strategy
All tests MUST work without a running backend (use `page.route()` mocks).
Tests that optionally test against live backend should use:
```javascript
const USE_LIVE_API = process.env.USE_LIVE_API === 'true';
```

### Test Independence
- Each test must call `mockLoginAsAdmin(page)` or set up auth independently
- No shared state between tests
- Use `test.beforeEach` for common setup only

---

## Acceptance Criteria

- [ ] All 6 test files exist with tests listed above
- [ ] `npx playwright test --project=chromium` passes all tests (mocked backend)
- [ ] Tests run headless in under 120 seconds total
- [ ] Screenshots captured on failure (configured in playwright.config.js)
- [ ] No hardcoded URLs — all use `process.env.BASE_URL || 'http://localhost:3000'`
- [ ] Tests are independent (no ordering dependencies)
- [ ] `npx playwright test --reporter=html` generates readable report
- [ ] Cancel button visible for both `running` and `pending` jobs in queue tests

---

## Verification

```bash
cd /Users/eli/github/handbrake2resilio/ui-frontend

# Install Playwright browsers if needed
npx playwright install chromium

# Run all Playwright tests (mocked)
npx playwright test --project=chromium

# Run with HTML report
npx playwright test --reporter=html

# Run specific test file
npx playwright test tests/auth.spec.js --project=chromium

# Run against live stack (if running)
BASE_URL=http://localhost:7474 USE_LIVE_API=true npx playwright test --project=chromium
```

---

## Git Operations

```bash
git add ui-frontend/tests/ ui-frontend/playwright.config.js
git commit -m "test(WEA-126): add comprehensive Playwright UI test suite for all views"
git push origin main
```

---

## STOP

Next prompt: `SPRINT_02D_E2E_INTEGRATION.md` (WEA-127, WEA-144)
