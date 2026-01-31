# Phase 6: E2E Testing Setup (Playwright)

## Context
We need to verify the frontend flows automatically.

## Requirements
1.  **Initialize Playwright**:
    -   Run `npm init playwright@latest` in `ui-frontend` (or manually set up if easier).
    -   Configure `playwright.config.js` to point to `http://localhost:3000`.
2.  **Create Auth Test (`ui-frontend/tests/auth.spec.js`)**:
    -   Test 1: Navigate to `/`. Assert redirect to `/login`.
    -   Test 2: Fill login form with valid creds. Assert redirect to Dashboard.
    -   Test 3: Logout. Assert redirect to Login.
3.  **Create Workflow Test (`ui-frontend/tests/workflows.spec.js`)**:
    -   Mock the backend responses if necessary, or run against the real running stack (preferred if docker is up).
    -   Test: Navigate to New Job -> Click Browse -> Select File (mock if needed) -> Submit.

## Verification
-   Run `npx playwright test`.
-   Ensure tests pass.

## Next Phase
STOP. The next phase is `PHASE_07_FINAL_INTEGRATION.md`.
