# S21: AI Detection Pipeline

**Goal:** RT-DETR broken/crack detection, LDC wear calculation, and health score computation — all running in dedicated threads with results in CameraResultsStore.
**Demo:** Feed test JPEGs to detection pipeline; broken/crack/wear/health results appear in store and camera.db.

## Must-Haves


## Tasks


## Files Likely Touched

- `src/services/camera/detection_worker.py`
- `src/services/camera/ldc_worker.py`
- `src/services/camera/health_calculator.py`
