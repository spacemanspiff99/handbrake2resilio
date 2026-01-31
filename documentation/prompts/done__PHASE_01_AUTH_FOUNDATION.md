# Phase 1: Authentication Foundation

## Context
The backend (`api-gateway/auth.py`) has a robust authentication system (JWT, bcrypt, SQLite), but the frontend (`ui-frontend`) lacks the user interface to interact with it. We need to implement the frontend authentication layer.

## Requirements
1.  **Update `ui-frontend/src/services/api.js`**:
    -   Add an `authAPI` object with methods:
        -   `login(username, password)` -> `POST /api/auth/login`
        -   `register(username, password, email)` -> `POST /api/auth/register`
        -   `verifyToken()` -> `GET /api/auth/verify` (You may need to add this endpoint to backend if missing, or use a workaround like `getSystemStatus` to check validity).
        -   `logout()` (Client-side only, clear token).
2.  **Create Auth Context**:
    -   Create `ui-frontend/src/context/AuthContext.js`.
    -   Implement `AuthProvider` component.
    -   Manage state: `user`, `token`, `isAuthenticated`, `isLoading`.
    -   Provide `login`, `logout`, `register` functions that use `authAPI` and update state.
    -   Persist token in `localStorage`.
    -   On mount, check if token exists and verify it.
3.  **Create Login Component**:
    -   `ui-frontend/src/components/Login.js`.
    -   Form with Username and Password.
    -   Handle submit -> `auth.login`.
    -   Handle errors (toast notification).
    -   Redirect to dashboard on success.
4.  **Create Register Component**:
    -   `ui-frontend/src/components/Register.js`.
    -   Form with Username, Password, Email.
    -   Handle submit -> `auth.register`.
    -   Redirect to login or dashboard on success.
5.  **Update App.js**:
    -   Add routes for `/login` and `/register`.
    -   Create a `ProtectedRoute` component that checks `isAuthenticated`.
    -   Wrap protected routes (`/`, `/queue`, `/system`) with `ProtectedRoute`.

## Verification
-   Start the stack (`docker-compose up`).
-   Visit `http://localhost:3000`. Should redirect to `/login`.
-   Register a new user "admin" / "admin123".
-   Login with the new user. Should redirect to Dashboard.
-   Refresh page. Should stay logged in.
-   Logout. Should redirect to Login.

## Next Phase
STOP. The next phase is `PHASE_02_TABS_BACKEND.md`.
