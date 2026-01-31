# Phase 4: Secure File Browser & Scanner Backend

## Context
Users need to browse files to select input/output paths. We need a secure way to list files on the server. `handbrake-service` has access to the media volumes, so it should handle this.

## Requirements
1.  **Update `handbrake-service/handbrake_service.py`**:
    -   Add `JAIL_ROOT` configuration (default to `/mnt` or a safe directory).
    -   Implement `GET /browse`:
        -   Query param: `path` (optional, defaults to `JAIL_ROOT`).
        -   **SECURITY**: Validate `path` starts with `JAIL_ROOT` and contains no `..` traversal. Return 403 if invalid.
        -   Return: List of `{name, type (file/dir), path}`.
    -   Implement `GET /scan`:
        -   Query param: `path`.
        -   Recursive scan for known video extensions (`.mp4`, `.mkv`, etc.).
        -   Return: List of video files found.
2.  **Update `api-gateway/api_gateway.py`**:
    -   Add `/api/filesystem/browse` and `/api/filesystem/scan` endpoints.
    -   Proxy requests to `handbrake-service`'s new endpoints.
    -   Ensure these are `@require_auth`.

## Verification
-   `curl` with auth token to `/api/filesystem/browse?path=/mnt`.
-   Verify it lists contents.
-   Try `/api/filesystem/browse?path=/etc` -> Should fail (403 or empty).

## Next Phase
STOP. The next phase is `PHASE_05_FILE_BROWSER_FRONTEND.md`.
