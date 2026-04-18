# Phase 7: Final Integration & Polish

## Context
Connect all the loose ends. The Dashboard and Queue views need to reflect real data and actions.

## Requirements
1.  **Update `Dashboard.js`**:
    -   Ensure `systemAPI` calls return real data from `handbrake-service`.
    -   Display Active Jobs count, System Resources (CPU/RAM) from the API.
2.  **Update `QueueView.js`**:
    -   Ensure "Cancel", "Retry", "Clear Completed" buttons call the `queueAPI`.
    -   Ensure the list auto-refreshes (React Query `refetchInterval` is already there, check it works).
3.  **Error Handling**:
    -   In `api.js` interceptors: If 401 is received, trigger a logout (clear token, redirect).
4.  **Cleanup**:
    -   Remove any "mock" data or console logs used for debugging.

## Verification
-   Full walkthrough of the application.
-   Login -> Dashboard (Check stats) -> Add Tab -> Submit Job -> Watch Queue (Progress updates) -> Job Complete.

## Next Phase
STOP. This is the final phase.
