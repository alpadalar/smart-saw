---
estimated_steps: 6
estimated_files: 2
---

# T02: Add db_service to workers with DB writes

**Slice:** S22 — Lifecycle & DB Integration
**Milestone:** M001

## Description

DetectionWorker and LDCWorker currently publish results only to CameraResultsStore (in-memory). This task adds an optional `db_service` parameter so workers can also persist results to camera.db via `SQLiteService.write_async()`. DetectionWorker writes to `detection_events` when broken or crack detections occur. LDCWorker writes to `wear_history` each wear cycle.

## Steps

1. **DetectionWorker constructor** (`src/services/camera/detection_worker.py`): Add `db_service=None` parameter after `camera_service`. Store as `self._db_service`. The TYPE_CHECKING import block at top already exists — no need to add SQLiteService type hint (keep it simple, just use `= None`).

2. **DetectionWorker DB writes** — In the main loop inside `run()`, after the `self._results_store.update_batch(...)` call (around line 190), add DB write logic:
   ```python
   # -- persist to camera.db --
   if self._db_service:
       if broken_count > 0:
           self._db_service.write_async(
               "INSERT INTO detection_events "
               "(timestamp, event_type, confidence, count, image_path, "
               "kesim_id, makine_id, serit_id, malzeme_cinsi) "
               "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
               (now, "broken_tooth", broken_confidence, broken_count,
                None, None, None, None, None),
           )
       if crack_count > 0:
           self._db_service.write_async(
               "INSERT INTO detection_events "
               "(timestamp, event_type, confidence, count, image_path, "
               "kesim_id, makine_id, serit_id, malzeme_cinsi) "
               "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
               (now, "crack", crack_confidence, crack_count,
                None, None, None, None, None),
           )
   ```
   The `now` variable already exists (ISO timestamp from `datetime.now().isoformat()`). Traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) are NULL for now — S23/S24 may populate them later.

3. **LDCWorker constructor** (`src/services/camera/ldc_worker.py`): Add `db_service=None` parameter after `camera_service`. Store as `self._db_service`.

4. **LDCWorker DB writes** — In the main loop inside `run()`, after the `self._results_store.update_batch(updates)` call (around line 161), add DB write logic:
   ```python
   # -- persist to camera.db --
   if self._db_service and wear_percentage is not None:
       self._db_service.write_async(
           "INSERT INTO wear_history "
           "(timestamp, wear_percentage, health_score, edge_pixel_count, "
           "image_path, kesim_id, makine_id, serit_id, malzeme_cinsi) "
           "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
           (now, wear_percentage, health_score, None,
            None, None, None, None, None),
       )
   ```
   `now` and `health_score` variables already exist in scope at this point.

5. **Schema cross-check**: The `detection_events` table columns are: `id` (auto), `timestamp`, `event_type`, `confidence`, `count`, `image_path`, `kesim_id`, `makine_id`, `serit_id`, `malzeme_cinsi`. The INSERT must list exactly those 9 non-auto columns. The `wear_history` table columns are: `id` (auto), `timestamp`, `wear_percentage`, `health_score`, `edge_pixel_count`, `image_path`, `kesim_id`, `makine_id`, `serit_id`, `malzeme_cinsi`. The INSERT must list exactly those 9 non-auto columns.

6. Verify syntax: `python -m py_compile src/services/camera/detection_worker.py && python -m py_compile src/services/camera/ldc_worker.py`

## Must-Haves

- [ ] DetectionWorker constructor accepts `db_service=None` keyword argument (backward compatible)
- [ ] LDCWorker constructor accepts `db_service=None` keyword argument (backward compatible)
- [ ] DetectionWorker writes to `detection_events` only when `broken_count > 0` or `crack_count > 0`
- [ ] LDCWorker writes to `wear_history` only when `wear_percentage is not None`
- [ ] INSERT column lists match schema exactly (9 non-auto columns each)
- [ ] No DB writes when `db_service` is None (backward compatible)

## Verification

- `python -m py_compile src/services/camera/detection_worker.py` — syntax OK
- `python -m py_compile src/services/camera/ldc_worker.py` — syntax OK
- `python -c "from src.services.camera.detection_worker import DetectionWorker; print('OK')"` — import OK
- `python -c "from src.services.camera.ldc_worker import LDCWorker; print('OK')"` — import OK
- Grep for `INSERT INTO detection_events` in detection_worker.py — confirms write logic exists
- Grep for `INSERT INTO wear_history` in ldc_worker.py — confirms write logic exists
- Verify column count in INSERT matches schema (9 columns, 9 `?` placeholders)

## Inputs

- `src/services/camera/detection_worker.py` — current DetectionWorker with results_store publishing, no DB writes
- `src/services/camera/ldc_worker.py` — current LDCWorker with results_store publishing, no DB writes
- `src/services/database/schemas.py` — SCHEMA_CAMERA_DB defines `detection_events` (9 non-auto columns) and `wear_history` (9 non-auto columns)

## Expected Output

- `src/services/camera/detection_worker.py` — constructor accepts `db_service=None`, main loop writes broken_tooth and crack events to detection_events
- `src/services/camera/ldc_worker.py` — constructor accepts `db_service=None`, main loop writes wear measurements to wear_history

## Observability Impact

- **New log signals:** `logger.warning("DB write failed — broken_tooth event dropped")`, `logger.warning("DB write failed — crack event dropped")` in DetectionWorker; `logger.warning("DB write failed — wear_history event dropped")` in LDCWorker. These fire when `write_async` returns `False` (queue full or DB error).
- **Inspection:** Query `detection_events` and `wear_history` tables in camera.db to confirm writes are landing. No writes appear when `db_service` is `None` (backward compatible).
- **Failure state:** When the write queue is full, warnings are emitted but detection/wear processing continues uninterrupted. No crash, no retry — events are dropped with a visible log line.
- **Future agent diagnostic:** grep logs for `"DB write failed"` to detect write-queue saturation.
