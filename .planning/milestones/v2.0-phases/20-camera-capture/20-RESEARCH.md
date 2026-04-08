# Phase 20: Camera Capture - Research

**Researched:** 2026-03-25
**Domain:** OpenCV VideoCapture, threading, JPEG encoding, asyncio/threading hybrid
**Confidence:** HIGH

## Summary

Phase 20 implements `CameraResultsStore` (thread-safe key-value store) and `CameraService`
(capture thread + save worker pool) from scratch, using the existing reference implementations in
`src/services/camera/` as a blueprint but rewriting to match current project conventions. The
reference code is already present in the repo and is nearly production-ready; the delta between
"reference" and "new" code centers on two CONTEXT decisions that differ from the reference: (1)
auto-discovery of camera device ID instead of using the config hint directly, and (2) a 30-second
retry loop on capture loss rather than an immediate hard stop. Both are additive changes.

Phase 19 Foundation is confirmed complete: `camera.enabled=true` is set in `config.yaml`,
`_init_camera()` in `lifecycle.py` is wired and already imports `CameraService` and
`CameraResultsStore` by path. The lifecycle expects both classes to exist at those exact paths
(`src/services/camera/results_store.py`, `src/services/camera/camera_service.py`) with the
constructor signatures visible in the reference code.

The camera hardware is confirmed present on this machine (`/dev/video0`), opencv-python-headless
4.11.0 is installed, and the device negotiates 1280×720 successfully. Actual achievable FPS is
~10 fps (hardware cap), not the 30 fps requested in config — this is expected behavior and should
be logged at startup, not treated as an error.

**Primary recommendation:** Write `results_store.py` and `camera_service.py` by adapting the
reference implementations, adding auto-discovery and retry logic per CONTEXT decisions. All
other files in `src/services/camera/` (detection_worker, ldc_worker, etc.) are Phase 21 — do
not touch them.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Old project `camera_service.py` and `results_store.py` used as reference only — rewrite
  from scratch following new architecture conventions (docstring format, error handling patterns,
  logging style, naming conventions).
- **D-02:** Other camera module files (`detection_worker.py`, `ldc_worker.py`, `health_calculator.py`,
  `modelB4.py`) belong to Phase 21 — do not touch them in Phase 20.
- **D-03:** Recording activates only when testere durumu is "yukari cikiyor" (saw rising). Phase 20
  exposes `start_recording()` / `stop_recording()` API; the triggering logic is Phase 22.
- **D-04:** CameraService provides `start_recording()` / `stop_recording()` API only. Trigger
  decision is deferred to Phase 22 VisionService.
- **D-05:** Auto-discovery: scan all camera devices on the system, use the first one found. Config
  `device_id` is a hint only (start scanning from that index).
- **D-06:** Capture loss during running: retry for 30 seconds, stop capture thread and log if
  still failing. Main application loop must not be affected.

### Claude's Discretion

- fps_actual tracking implementation in capture loop (moving average, window size, etc.)
- Frame queue size and overflow strategy
- Save worker thread count (reference uses `min(4, cpu_count)` — can adjust)
- Auto-discovery device ID scan range

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAM-03 | OpenCV frame capture (resolution and FPS configurable) | VideoCapture API verified; `CAP_PROP_FRAME_WIDTH/HEIGHT/FPS/BUFFERSIZE` all apply correctly on this hardware |
| CAM-04 | Frames saved to disk as JPEG (multi-thread encoder) | `cv2.imencode` + `cv2.imwrite` with `IMWRITE_JPEG_QUALITY` verified; multi-thread save pool pattern from reference confirmed correct |
| CAM-05 | Recording directory structure: `recordings/YYYYMMDD-HHMMSS/` | `datetime.now().strftime("%Y%m%d-%H%M%S")` + `os.makedirs(exist_ok=True)` pattern verified in reference; `recordings_path` key exists in `config.yaml` |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| opencv-python-headless | 4.11.0 (installed) | VideoCapture, imencode, imwrite | Must be headless — full opencv has Qt5/Qt6 symbol conflict with PySide6 (documented in REQUIREMENTS.md Out of Scope) |
| numpy | 1.26.4 (installed) | ndarray frame representation | OpenCV frames are numpy arrays; numpy cap removed in Phase 19 |
| threading | stdlib | Daemon threads for capture + save workers | Non-async blocking I/O; matches project pattern (SQLiteService writer, health monitor) |
| queue | stdlib | Frame queue between capture thread and save workers | Producer-consumer decoupling; `Queue(maxsize=N)` with `put_nowait` + drop on Full |
| collections.deque | stdlib | Moving average window for fps_actual | O(1) append/pop with bounded size; clean implementation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| os | stdlib | makedirs, path.join, cpu_count | Creating recording directories |
| sys | stdlib | Platform check for CAP_DSHOW on Windows | Platform-aware VideoCapture backend |
| time | stdlib | Monotonic timestamps for FPS calculation, retry sleep | Inside threads (not async context) |
| datetime | stdlib | Recording directory timestamp formatting | `datetime.now().strftime("%Y%m%d-%H%M%S")` |

**Installation:** All dependencies already installed. No new packages needed for Phase 20.

**Version verification (confirmed 2026-03-25):**
- `opencv-python-headless` 4.11.0 — confirmed `import cv2; cv2.__version__` = `"4.11.0"`
- `numpy` 1.26.4 — confirmed `import numpy; numpy.__version__` = `"1.26.4"`

---

## Architecture Patterns

### Recommended Project Structure

Phase 20 touches exactly two files:

```
src/services/camera/
├── results_store.py     # NEW — CameraResultsStore (thread-safe key-value store)
├── camera_service.py    # NEW — CameraService (capture thread + save worker pool)
├── __init__.py          # EXISTING — do not modify (Phase 19 scaffold)
├── detection_worker.py  # EXISTING — Phase 21, do not touch
├── ldc_worker.py        # EXISTING — Phase 21, do not touch
├── health_calculator.py # EXISTING — Phase 21, do not touch
└── modelB4.py           # EXISTING — Phase 21, do not touch
```

### Pattern 1: CameraResultsStore — Thread-Safe Key-Value Store

**What:** A `threading.Lock`-protected dict. All camera state (latest_frame, frame_count,
is_recording, recording_path, fps_actual) lives here as the sole cross-thread boundary.

**When to use:** Whenever capture thread needs to publish state to GUI/IoT/detection consumers.

**Standard keys to initialize at `start()`:**

```python
# Source: reference results_store.py + camera_service.py
self._results_store.update_batch({
    "is_recording": False,
    "frame_count": 0,
    "fps_actual": 0.0,
    "latest_frame": None,
    "recording_path": None,
})
```

**API contract (must match exactly — lifecycle.py and Phase 21-24 consumers depend on it):**

```python
class CameraResultsStore:
    def update(self, key: str, value: Any) -> None: ...
    def update_batch(self, data: dict) -> None: ...
    def get(self, key: str, default: Any = None) -> Any: ...
    def snapshot(self) -> dict: ...  # shallow copy, thread-safe
```

### Pattern 2: CameraService — Capture Thread + Save Worker Pool

**What:** Constructor does no I/O. `start()` is `async` (lifecycle calls `await camera_service.start()`).
Spawns one capture daemon thread and N save-worker daemon threads.

**When to use:** This is the single implementation; no variants.

**Constructor signature (must match lifecycle.py call):**

```python
# Source: lifecycle.py line 422
self.camera_service = CameraService(camera_config, self.camera_results_store)
```

**`start()` return contract:**

```python
async def start(self) -> bool:
    """Returns False (no crash) if device cannot be opened."""
```

Lifecycle calls `await self.camera_service.start()` without checking return value — the service
must never raise; log and return `False` on camera open failure.

**`stop()` shutdown contract:**

```python
async def stop(self) -> None:
    """Signal threads, flush queue, release device."""
```

Lifecycle calls `await self.camera_service.stop()` in shutdown sequence (line 192).

**`get_current_frame()` contract (Phase 21 consumer):**

```python
def get_current_frame(self) -> np.ndarray | None:
    """Return latest raw frame for DetectionWorker."""
```

### Pattern 3: Daemon Thread Lifecycle

**What:** All background threads use `daemon=True` so they exit automatically when the process
ends. Named threads for debuggability.

```python
# Source: reference camera_service.py, matches project pattern (SQLiteService writer, health monitor)
self._capture_thread = threading.Thread(
    target=self._capture_loop, daemon=True, name="camera-capture"
)
for i in range(self._num_save_threads):
    t = threading.Thread(
        target=self._save_worker, daemon=True, name=f"camera-save-{i}"
    )
```

### Pattern 4: Auto-Discovery (D-05 — new vs. reference)

**What:** Scan device IDs starting from the config hint. Use the first device that opens.

**Decision rationale:** Industrial environment — USB camera IDs may shift after reboot.

**Recommended implementation:**

```python
def _discover_camera(self) -> cv2.VideoCapture | None:
    """Scan device IDs and return the first openable VideoCapture.

    Starts at config device_id hint, scans _DISCOVERY_RANGE total IDs.
    Returns None if no device found.
    """
    hint = self._device_id  # from config
    for offset in range(_DISCOVERY_RANGE):  # e.g., range(4)
        dev_id = (hint + offset) % _DISCOVERY_RANGE
        cap = self._open_device(dev_id)
        if cap is not None:
            if dev_id != hint:
                logger.info("Camera auto-discovered at device_id=%d (hint was %d)", dev_id, hint)
            return cap
    return None
```

Scan range: 4 IDs (0-3) is sufficient. Only `/dev/video0` is available on this machine; range
of 4 keeps discovery fast (~0.1s per attempt) without scanning indefinitely.

### Pattern 5: Capture Loss Retry (D-06 — new vs. reference)

**What:** When `cap.read()` fails in the capture loop, retry for 30 seconds before giving up.

```python
# In _capture_loop():
_retry_deadline = None
while not self._stop_event.is_set():
    ret, frame = self._cap.read()
    if not ret:
        if _retry_deadline is None:
            _retry_deadline = time.monotonic() + 30.0
            logger.warning("Camera read failed — retrying for 30s")
        if time.monotonic() > _retry_deadline:
            logger.error("Camera read failed for 30s — stopping capture thread")
            break
        time.sleep(0.1)
        continue
    _retry_deadline = None  # reset on success
    # ... process frame ...
```

### Pattern 6: fps_actual Moving Average (Claude's Discretion)

**Recommendation:** `collections.deque(maxlen=30)` of monotonic timestamps. Compute FPS as
`(len(window) - 1) / (window[-1] - window[0])` when window has ≥ 2 entries. Update
`results_store` every 30 frames (not every frame — reduces lock contention).

```python
from collections import deque

_fps_window: deque = deque(maxlen=30)

# In capture loop after successful read:
_fps_window.append(time.monotonic())
if len(_fps_window) >= 2:
    fps = (len(_fps_window) - 1) / (_fps_window[-1] - _fps_window[0])
    if self._frame_count % 30 == 0:
        self._results_store.update("fps_actual", round(fps, 1))
```

**Window size 30:** At 10 fps this gives a 3-second smoothing window — stable reading. At 30
fps it gives 1-second window — responsive. Measured actual FPS on this hardware: ~10 fps despite
30 fps request (hardware cap; expected, not an error).

### Pattern 7: Frame Queue — Save Worker Pool (Claude's Discretion)

**Recommendation:**
- `Queue(maxsize=100)` — matches reference; at 10 fps this is 10 seconds of buffering.
  With ~15 KB JPEG frames that is ~1.5 MB in memory; well within limits.
- Overflow strategy: `put_nowait()` + `except queue.Full: logger.warning("dropping frame")`
- Save workers: `min(4, os.cpu_count() or 2)` — reference value; 4 workers on this 8-core
  machine. JPEG disk write measured at 1.85ms/frame; 4 workers can sustain 2160 frames/sec,
  far above capture rate.
- Sentinel shutdown: send `None` per worker to exit their `while True` loop cleanly.

### Anti-Patterns to Avoid

- **Calling `time.sleep()` in async context:** Capture loop and save workers run in daemon
  threads, not the asyncio event loop. `time.sleep()` is correct here. Never use
  `asyncio.sleep()` inside thread targets.
- **Accessing `self._cap` outside the capture thread:** `cv2.VideoCapture` is not thread-safe.
  Only the capture thread reads frames; other threads use `get_current_frame()` with a lock.
- **Importing cv2 at module level in lifecycle.py:** The zero-import guard requires camera
  modules be imported lazily. `lifecycle.py` already does this correctly; the new files must
  not add top-level imports that would be pulled in at lifecycle import time.
- **Using `frame_queue.join()` in `stop_recording()` without a timeout:** Can block indefinitely
  if a save worker has died. Reference code uses it directly — add a reasonable approach.
- **Raising exceptions from `start()`:** Lifecycle catches `Exception` broadly in `_init_camera()`
  and logs a warning. A camera failure must not crash the application. Return `False` instead.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread-safe dict | Custom synchronization | `threading.Lock` + plain dict | Standard library; correct under GIL; reference already uses this pattern |
| JPEG encoding | Pure Python encoder | `cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, q])` | Optimized C++ backend; 2.81ms per 1280×720 frame verified |
| JPEG disk write | `open()`+write | `cv2.imwrite(path, frame, encode_params)` | Combined encode+write in one call when writing from save worker |
| Producer-consumer queue | Custom ring buffer | `queue.Queue(maxsize=N)` | Thread-safe, has `put_nowait()`, `task_done()`, `join()` semantics |
| FPS measurement | External profiler | `collections.deque` timestamp window | Lightweight, zero dependencies, O(1) update |
| Camera device open | Low-level V4L2 | `cv2.VideoCapture(dev_id)` | Handles V4L2/DSHOW/CAP_ANY backends transparently |

**Key insight:** This domain is almost entirely covered by stdlib (`threading`, `queue`,
`collections`) and OpenCV. No additional packages are needed.

---

## Common Pitfalls

### Pitfall 1: VideoCapture Negotiation Mismatch

**What goes wrong:** `cap.set(cv2.CAP_PROP_FPS, 30)` returns True but the camera delivers 10 fps.
**Why it happens:** V4L2 cameras silently clamp to hardware-supported modes. This hardware
delivers 10 fps at 1280×720 (measured: 8.3–10 fps).
**How to avoid:** Always read back actual values with `cap.get()` after setting and log them.
Never assume set == actual.
**Warning signs:** `fps_actual` in results store diverges significantly from config value.

### Pitfall 2: `frame_queue.join()` Blocking Forever in `stop_recording()`

**What goes wrong:** `stop_recording()` calls `self._frame_queue.join()` which blocks until all
tasks are done. If a save worker crashes or has already exited, `task_done()` is never called.
**Why it happens:** `task_done()` is only called in the `finally` block of the save worker loop.
If the worker thread dies from an unhandled exception before `task_done()`, the join hangs.
**How to avoid:** Wrap save worker body in `try/finally` with `task_done()` unconditionally in
`finally`. The reference does this correctly.
**Warning signs:** Application hangs on shutdown; `stop_recording()` never returns.

### Pitfall 3: Raw Frame Access Race Condition

**What goes wrong:** `get_current_frame()` returns a reference to an ndarray that the capture
thread overwrites on the next iteration.
**Why it happens:** Without a copy, the frame returned to the caller may be mutated while they
process it.
**How to avoid:** Return `self._current_frame` under lock (the reference does this). If
DetectionWorker needs to hold the frame across a long inference call, it must `.copy()` it.
The reference pattern is correct — do not change it.
**Warning signs:** Corrupted or garbled frames at detection worker input.

### Pitfall 4: Auto-Discovery Opening Wrong Device

**What goes wrong:** Scanning from device ID 0 opens an internal webcam instead of the
industrial USB camera.
**Why it happens:** `/dev/video0` may be the wrong camera if multiple devices exist.
**How to avoid:** Start scan from `config.device_id` hint. Log which device ID was actually
used. On this machine, only `/dev/video0` is present (verified).
**Warning signs:** First frame shows wrong image; resolution negotiation returns unexpected values.

### Pitfall 5: Capture Thread Accessing Asyncio Objects

**What goes wrong:** Capture thread calls `asyncio.get_event_loop()` or emits to a PySide6
signal connected to async code, blocking the event loop.
**Why it happens:** Cross-thread asyncio calls require thread-safe variants.
**How to avoid:** Capture thread writes only to `CameraResultsStore` (pure threading primitives).
It never touches asyncio. GUI consumers poll the store via QTimer (Phase 24).
**Warning signs:** `RuntimeError: This event loop is already running` or GUI freeze.

### Pitfall 6: cv2.VideoCapture Not Released on Exception

**What goes wrong:** If `start()` raises after opening the camera device, `cap.release()` is
never called. The device stays locked, and subsequent open attempts fail.
**Why it happens:** Early return or exception between `cap = VideoCapture(...)` and
`self._cap = cap`.
**How to avoid:** Release in the `except` block of `start()`, same as the reference does on
`not cap.isOpened()`.
**Warning signs:** "Device or resource busy" error on second startup attempt.

---

## Code Examples

Verified patterns from reference code and direct testing on this machine:

### Camera Open with Platform Backend
```python
# Source: reference camera_service.py
import sys, cv2
if sys.platform.startswith("win"):
    cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(device_id)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, fps)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency

# Log actual negotiated values — they may differ from requested
actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
actual_fps = cap.get(cv2.CAP_PROP_FPS)
```

### JPEG Encode (in-memory, for results store)
```python
# Source: reference camera_service.py; verified 2.81ms at 1280x720
encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
ok, jpeg_buf = cv2.imencode(".jpg", frame, encode_params)
if ok:
    self._results_store.update("latest_frame", jpeg_buf.tobytes())
```

### JPEG Write to Disk (save worker)
```python
# Source: reference camera_service.py; verified 1.85ms per frame
def _save_worker(self) -> None:
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
    while True:
        item = self._frame_queue.get()
        if item is None:
            self._frame_queue.task_done()
            break
        try:
            count, frame, output_dir = item
            path = os.path.join(output_dir, f"frame_{count:06d}.jpg")
            cv2.imwrite(path, frame, encode_params)
        except Exception:
            logger.error("Save worker error", exc_info=True)
        finally:
            self._frame_queue.task_done()
```

### Recording Directory Creation (CAM-05)
```python
# Source: reference camera_service.py
from datetime import datetime
import os

recording_dir = os.path.join(
    self._recordings_path,
    datetime.now().strftime("%Y%m%d-%H%M%S"),
)
os.makedirs(recording_dir, exist_ok=True)
```

### Sentinel Shutdown for Save Workers
```python
# Source: reference camera_service.py
# In stop():
for _ in self._save_threads:
    try:
        self._frame_queue.put(None, timeout=1.0)
    except queue.Full:
        pass

for t in self._save_threads:
    t.join(timeout=2.0)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `opencv-python` (full) | `opencv-python-headless` | Established in REQUIREMENTS.md | Avoids Qt5/Qt6 symbol conflict with PySide6 on Linux |
| numpy cap `<2.0` | `numpy>=1.24.0` (no upper bound) | Phase 19 | Allows ultralytics/torch to install |
| config `device_id` direct use | Auto-discovery starting from hint | D-05 (this phase) | Industrial robustness; USB ID may change |
| Immediate stop on capture loss | 30-second retry loop | D-06 (this phase) | Application resilience; transient USB disconnect recovers |

**Deprecated/outdated:**
- `np.ptp()`: Replaced with `np.max() - np.min()` in Phase 19 (removed in numpy 2.0).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| opencv-python-headless | CAM-03, CAM-04 | Yes | 4.11.0 | — |
| numpy | Frame array handling | Yes | 1.26.4 | — |
| Python 3 | Runtime | Yes | 3.13.12 | — |
| /dev/video0 | CAM-03 (test) | Yes | — | Service returns False on open failure (non-fatal) |
| /dev/video1 | Auto-discovery | No (not available) | — | Auto-discovery skips unavailable IDs |
| data/recordings/ | CAM-05 | Created at runtime | — | `os.makedirs(exist_ok=True)` in `start_recording()` |

**Missing dependencies with no fallback:** None — all required libraries present.

**Missing dependencies with fallback:** `/dev/video1` not present but auto-discovery handles
this gracefully.

**FPS note:** Camera hardware delivers ~10 fps at 1280×720 (not 30 fps as configured).
This is a hardware capability limit, not a software failure. `fps_actual` in results store
will reflect the real rate (~10 fps). Log at startup, not as error.

---

## Validation Architecture

> nyquist_validation key absent from .planning/config.json — treated as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Not detected (no pytest.ini, no test/ directory) |
| Config file | None — Wave 0 must create |
| Quick run command | `python3 -m pytest tests/ -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAM-03 | CameraResultsStore.update() and .get() are thread-safe | unit | `python3 -m pytest tests/test_camera_results_store.py -x` | No — Wave 0 |
| CAM-03 | CameraService.start() returns False (not raise) when camera unavailable | unit | `python3 -m pytest tests/test_camera_service.py::test_start_returns_false_on_no_device -x` | No — Wave 0 |
| CAM-03 | Config resolution/FPS values applied to VideoCapture via CAP_PROP_* | unit (mock) | `python3 -m pytest tests/test_camera_service.py::test_cap_props_applied -x` | No — Wave 0 |
| CAM-04 | JPEG bytes written to disk in correct path during recording | unit | `python3 -m pytest tests/test_camera_service.py::test_recording_writes_jpegs -x` | No — Wave 0 |
| CAM-05 | Recording directory created as recordings/YYYYMMDD-HHMMSS/ | unit | `python3 -m pytest tests/test_camera_service.py::test_recording_dir_format -x` | No — Wave 0 |
| CAM-03 | latest_frame in results store updated after each captured frame | unit | `python3 -m pytest tests/test_camera_results_store.py::test_latest_frame_updated -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_camera_results_store.py tests/test_camera_service.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_camera_results_store.py` — covers CAM-03 (thread-safe store)
- [ ] `tests/test_camera_service.py` — covers CAM-03 (capture), CAM-04 (JPEG write), CAM-05 (dir structure)
- [ ] `tests/__init__.py` — package marker
- [ ] Framework install: `pip install pytest` — if not present

> **Note:** Tests for CameraService should mock `cv2.VideoCapture` to avoid requiring physical
> hardware in CI. Use `unittest.mock.patch("cv2.VideoCapture")`.

---

## Integration with Existing Code

### What lifecycle.py already expects (do not change these)

`lifecycle.py` line 422 calls:
```python
self.camera_service = CameraService(camera_config, self.camera_results_store)
await self.camera_service.start()
```

`lifecycle.py` line 192 calls:
```python
await self.camera_service.stop()
```

`lifecycle.py` line 182–190 calls (Phase 21 workers, not this phase):
```python
self.detection_worker.stop()
self.detection_worker.join(timeout=timeout)
self.ldc_worker.stop()
self.ldc_worker.join(timeout=timeout)
```

### Phase 21 consumer contract (must be honored now)

DetectionWorker (Phase 21) calls:
```python
frame = self._camera_service.get_current_frame()
```

This method must exist and return `np.ndarray | None` under a `_frame_lock`.

### Phase 22 trigger contract (must be honored now)

VisionService (Phase 22) calls:
```python
camera_service.start_recording()   # -> bool
camera_service.stop_recording()    # -> bool
```

Both must exist; Phase 22 decides when to call them.

### CameraResultsStore keys consumed downstream

| Key | Type | Consumer |
|-----|------|----------|
| `latest_frame` | `bytes \| None` | Phase 24 GUI (QTimer poll), Phase 23 IoT |
| `frame_count` | `int` | Phase 22 VisionService |
| `is_recording` | `bool` | Phase 24 GUI status display |
| `recording_path` | `str \| None` | Phase 22 VisionService, Phase 24 GUI |
| `fps_actual` | `float` | Phase 24 GUI stats display |

---

## Open Questions

1. **`stop_recording()` + `frame_queue.join()` timeout**
   - What we know: Reference calls `self._frame_queue.join()` with no timeout; can hang if worker
     dies. Save workers use `finally: task_done()` which prevents this in practice.
   - What's unclear: Whether to add a wall-clock timeout as belt-and-suspenders safety.
   - Recommendation: Keep `frame_queue.join()` as in reference (safe via `finally`), but document
     the contract. Add a `logger.warning` if join takes >5 seconds.

2. **Auto-discovery range upper bound**
   - What we know: Only `/dev/video0` is present on this machine; range of 4 is safe.
   - What's unclear: Whether the industrial deployment machine has more video devices.
   - Recommendation: Make scan range a module-level constant `_DISCOVERY_RANGE = 4`. Easy to
     adjust without changing logic.

3. **`recording_path` passed to results store vs. passed to queue items**
   - What we know: Reference passes `(count, frame, recording_dir)` as queue item, so save
     workers always know where to write even if recording_dir changes between enqueue and dequeue.
   - Recommendation: Keep this pattern from the reference — it is correct and race-condition safe.

---

## Sources

### Primary (HIGH confidence)
- Reference `src/services/camera/camera_service.py` — Existing codebase, read directly
- Reference `src/services/camera/results_store.py` — Existing codebase, read directly
- `src/core/lifecycle.py` — Integration points verified by reading lines 80-460
- `config/config.yaml` §camera — Config schema verified
- Direct hardware testing — VideoCapture, JPEG encode/write, FPS measured on this machine

### Secondary (MEDIUM confidence)
- OpenCV 4.11 API (`CAP_PROP_*`, `imencode`, `imwrite`) — Verified against installed version
- Project conventions (CONVENTIONS.md, ARCHITECTURE.md) — Read directly

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies installed and tested directly
- Architecture: HIGH — reference code exists; integration points verified in lifecycle.py
- Pitfalls: HIGH — all identified from reference code and live testing (FPS mismatch confirmed)

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain; no fast-moving dependencies)
