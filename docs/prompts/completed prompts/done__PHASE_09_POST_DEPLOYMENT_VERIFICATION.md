# PHASE_09: Post-Deployment Verification and E2E Testing

## 📝 Context & Rules
This prompt follows the project rules defined in `.cursor/rules/rules.mdc`.
**Objective**: Verify the success of the Phase 08 deployment and ensure all core functionality is working on the live dev server (`192.168.10.18`).

## 👥 Personas
1. **Backend Engineer**: Verify API health, database stability, and auth logic.
2. **QA Engineer**: Execute browser-based smoke tests and E2E workflows.
3. **Project Manager**: Finalize documentation and Git operations.

---

### 🟢 Step 1: Backend & API Verification (Backend Engineer)
*Wait for the build initiated in Phase 08 to complete (verified: build finished at 20:09 UTC).*

1. **Verify Service Health**:
   ```bash
   curl http://192.168.10.18:8080/health
   ```
   Check that `database` is "healthy" and `api_gateway` version is "2.0.0".

2. **Verify Database Initialization**:
   Check logs for any `sqlite3` errors after the `executescript` fix:
   ```bash
   ssh akun@192.168.10.18 "docker logs handbrake2resilio_api-gateway | grep -i error"
   ```

3. **Manual Auth Check**:
   Register and login via `curl` to ensure the auth service is writing to the database correctly.

---

### 🔵 Step 2: Browser-Based E2E Testing (QA Engineer)
*Per rule 9 in `rules.mdc`, we must use a browser simulation tool to verify the frontend.*

1. **Create Smoke Test**: Create `ui-frontend/tests/smoke.spec.js` that performs a real (non-mocked) login on `http://192.168.10.18:3000`.
2. **Execute Tests**:
   ```bash
   npx playwright test tests/smoke.spec.js --config=playwright.config.js
   ```
3. **Verify Core Features**:
   - Upward navigation (`..`) in File Browser.
   - Visibility of `/mnt/tv` and `/mnt/movies`.
   - Folder creation in the creation modal.
   - Tab settings editing and persistence.

---

### 🟠 Step 3: Finalization & Handoff (Project Manager)

1. **Rename Phases**:
   - `PHASE_08_DEPLOYMENT_FIX.md` -> `done__PHASE_08_DEPLOYMENT_FIX.md`
   - `PHASE_09_POST_DEPLOYMENT_VERIFICATION.md` -> `done__PHASE_09_POST_DEPLOYMENT_VERIFICATION.md`

2. **Git Operations**:
   - `git add .`
   - `git commit -m "Phase 09 complete: Deployment verified with live E2E smoke tests"`
   - `git push origin main`

## 🛑 STOP
This completes the stabilization phase. The system is now ready for production feature development.
Next: `PHASE_10_ENHANCEMENTS.md` (if requested).
