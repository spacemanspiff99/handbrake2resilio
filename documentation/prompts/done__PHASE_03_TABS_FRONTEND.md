# Phase 3: Tabs (Watch Configuration) Frontend

## Context
With the backend ready, we need to update the UI to allow users to configure Tabs, specifically capturing the `source_path`.

## Requirements
1.  **Update `ui-frontend/src/services/api.js`**:
    -   Ensure `tabsAPI` methods (`getTabs`, `createTab`, `updateTab`, `deleteTab`) match the backend endpoints implemented in Phase 2.
2.  **Update `ui-frontend/src/components/Sidebar.js`**:
    -   Update the "Add Tab" form.
    -   Add input field for `Source Path`.
    -   Add input field for `Destination Path` (already exists, ensure it maps correctly).
    -   Ensure `source_type` is selectable (TV/Movies).
3.  **Display Tabs**:
    -   Ensure the Sidebar list displays the new `source_path` info in the expanded view.

## Verification
-   Login to the UI.
-   Click "+" in Sidebar to add a tab.
-   Enter Name "Test Show", Source "/mnt/tv_source", Dest "/mnt/tv_dest".
-   Click Create.
-   Verify the tab appears in the list.
-   Expand the tab and verify paths are correct.

## Next Phase
STOP. The next phase is `PHASE_04_FILE_BROWSER_BACKEND.md`.
