# S22: Lifecycle & DB Integration

**Goal:** VisionService orchestration, lifecycle _init_camera() with lazy imports, and detection results written to SQLite via existing queue pattern.
**Demo:** Full camera stack starts in lifecycle; detection events and wear history written to camera.db; camera.enabled=false creates no camera objects.

## Must-Haves


## Tasks


## Files Likely Touched

- `src/services/camera/vision_service.py`
- `src/core/lifecycle.py`
