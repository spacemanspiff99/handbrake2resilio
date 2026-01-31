# Phase 2: Tabs (Watch Configuration) Backend

## Context
The "Tabs" feature defines where the system looks for content ("Source Path") and where it sends it ("Destination Path"). We need to support this in the database and API.

## Requirements
1.  **Database Schema Update**:
    -   Update `api-gateway/auth.py` (or create `api-gateway/db.py` if better separation is desired) to include a `tabs` table.
    -   **Schema**:
        -   `id` (INTEGER PRIMARY KEY)
        -   `name` (TEXT NOT NULL)
        -   `source_path` (TEXT NOT NULL) - **CRITICAL: New field**
        -   `destination_path` (TEXT NOT NULL)
        -   `source_type` (TEXT DEFAULT 'tv')
        -   `profile` (TEXT DEFAULT 'standard')
        -   `user_id` (INTEGER, Foreign Key to users)
        -   `created_at` (TIMESTAMP)
2.  **API Endpoints (`api-gateway/api_gateway.py`)**:
    -   Implement CRUD for tabs:
        -   `POST /api/tabs`: Validate `source_path` and `destination_path` are not empty.
        -   `GET /api/tabs`: Return list of tabs (optionally filter by user).
        -   `PUT /api/tabs/<id>`: Update tab details.
        -   `DELETE /api/tabs/<id>`: Remove tab.
3.  **Validation**:
    -   Ensure `source_path` and `destination_path` look like valid paths (basic string validation).

## Verification
-   Use `curl` or Postman to test endpoints (requires Auth token from Phase 1).
-   `POST /api/tabs` with `{"name": "Test", "source_path": "/data/source", "destination_path": "/data/dest"}`.
-   `GET /api/tabs` should return the created tab.

## Next Phase
STOP. The next phase is `PHASE_03_TABS_FRONTEND.md`.
