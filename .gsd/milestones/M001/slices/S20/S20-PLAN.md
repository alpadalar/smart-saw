# S20: Camera Capture

**Goal:** OpenCV frame capture thread and JPEG encoder running in background threads without blocking the asyncio event loop.
**Demo:** CameraService starts, frames appear in CameraResultsStore within 2 seconds, JPEG files written to recordings directory.

## Must-Haves


## Tasks


## Files Likely Touched

- `src/services/camera/camera_service.py`
- `src/services/camera/results_store.py`
