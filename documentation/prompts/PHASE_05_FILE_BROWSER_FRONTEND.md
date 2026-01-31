# Phase 5: File Browser Frontend & New Job UI

## Context
We need a reusable UI component for file browsing and a way to manually submit jobs.

## Requirements
1.  **Create `ui-frontend/src/components/common/FileBrowser.js`**:
    -   Props: `onSelect` (callback), `mode` (file/directory), `startPath`.
    -   Use `api.filesystem.browse` to fetch data.
    -   Render list of folders/files.
    -   Click folder -> Navigate down.
    -   Click "Up" -> Navigate up (restricted to allowed root).
    -   Select item -> Call `onSelect`.
2.  **Update `ui-frontend/src/components/Sidebar.js`**:
    -   Replace text inputs for "Source Path" and "Destination Path" with a "Browse" button that opens a Modal containing `FileBrowser`.
3.  **Create `ui-frontend/src/components/NewJobModal.js`**:
    -   Modal with fields:
        -   Input File (Browse button -> FileBrowser).
        -   Output Directory (Browse button -> FileBrowser) OR Select from Tabs.
        -   Quality Profile.
    -   Submit -> `queueAPI.addToQueue`.
    -   Add a "New Job" button to the Dashboard or Header to open this modal.

## Verification
-   Open UI.
-   Create a Tab -> Use Browse to pick `/mnt/tv/series_1`.
-   Open New Job Modal -> Use Browse to pick a video file. Submit.
-   Verify job appears in Queue.

## Next Phase
STOP. The next phase is `PHASE_06_TESTING_SETUP.md`.
