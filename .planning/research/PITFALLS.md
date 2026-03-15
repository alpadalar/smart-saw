# Pitfalls Research

**Domain:** Adding camera vision & AI detection to an existing industrial async control system
**Researched:** 2026-03-16
**Confidence:** HIGH (OpenCV threading, PyTorch CUDA, Qt display patterns verified via official docs and community issue trackers)

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or safety failures.

---

### Pitfall 1: cv2.VideoCapture.read() Blocks the Asyncio Event Loop

**What goes wrong:**
A developer calls `cap.read()` directly inside an `async def` coroutine or anywhere reachable from the 10 Hz asyncio processing loop. The call blocks for 30–100ms waiting for a USB/V4L2 frame. The asyncio event loop stalls. Modbus reads start missing their 100ms slot, IoT telemetry backs up, and the SQLite write queue grows. The effect looks like intermittent Modbus timeouts or database queue alarms — nothing in the camera code shows an obvious error.

**Why it happens:**
`cv2.VideoCapture.read()` is a synchronous, blocking C extension call. Although it releases the GIL while waiting in V4L2 or GStreamer, it still occupies the OS thread that asyncio is running on. Asyncio cannot schedule other coroutines while the thread is blocked.

**How to avoid:**
Run all camera capture in a dedicated `threading.Thread` (never in the asyncio event loop thread). The capture thread fills a `queue.Queue(maxsize=1)` or a `threading.Event` + shared frame reference using a lock. The asyncio side only reads the latest frame — never waits for capture.

```python
# WRONG: called from asyncio context
async def update_display():
    ret, frame = cap.read()  # Blocks event loop for 30-100ms

# RIGHT: camera runs in its own thread
class CameraCapture(threading.Thread):
    def run(self):
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._latest_frame = frame
```

**Warning signs:**
- Modbus read rate drops below 8 Hz when camera is enabled
- `data_pipeline.get_stats()['errors']` increases after camera start
- Health monitor logs database queue warnings shortly after camera init

**Phase to address:** Camera module phase (frame capture implementation). The capture thread must be designed before the detection pipeline is connected.

---

### Pitfall 2: Sharing a Single PyTorch/Ultralytics Model Across Multiple Threads

**What goes wrong:**
Three detection models (RT-DETR broken, RT-DETR crack, LDC edge) are loaded once at startup and called from different threads or at different times in the same detection loop. Internally, YOLO/Ultralytics models maintain per-call state (result buffers, preprocessing state). Concurrent or interleaved access causes `RuntimeError` during inference, silent wrong predictions, or CUDA context corruption requiring a process restart.

**Why it happens:**
Ultralytics documents explicitly that sharing a single model instance across threads causes race conditions on internal state. This is especially dangerous with two RT-DETR models that use the same Ultralytics predictor base class — their shared underlying C++ state is not re-entrant.

**How to avoid:**
Each detection pipeline gets its own model instance, loaded in the thread or context that will use it. For the sequential detection approach (broken → crack → LDC, one per frame), all three models load into the same detection thread and are called sequentially without sharing.

```python
# WRONG: one model, called from multiple call paths
class VisionService:
    def __init__(self):
        self.broken_model = YOLO("broken_best.pt")  # Shared instance

# RIGHT: models owned by the single detection thread
class DetectionThread(threading.Thread):
    def run(self):
        # Models instantiated inside the thread that uses them
        broken_model = YOLO("broken_best.pt")
        crack_model = YOLO("crack_best.pt")
        ldc_model = ...
        while self._running:
            frame = self._get_frame()
            broken_result = broken_model(frame)
            crack_result = crack_model(frame)
```

**Warning signs:**
- `RuntimeError` during `.predict()` calls that appears randomly
- Predictions differ between runs on the same frame
- CUDA errors after model is called from more than one call site

**Phase to address:** AI detection pipeline phase. The detection thread architecture must be settled before model loading code is written.

---

### Pitfall 3: torch.load() and CUDA Context Initialization Blocks Asyncio at Startup

**What goes wrong:**
Model loading (`torch.load()` or `YOLO("model.pt")`) is placed in `ApplicationLifecycle._init_camera()` and called with `await asyncio.get_event_loop().run_in_executor(None, ...)` — or worse, called synchronously. CUDA context initialization on first load takes 2–6 seconds. During this window, the asyncio event loop is frozen or the executor threadpool is saturated, delaying the rest of the startup sequence (Modbus connect, data pipeline start). If models are loaded synchronously they fully block the event loop.

**Why it happens:**
`torch.load()` is CPU-bound and performs CUDA driver initialization on first call. There is a confirmed PyTorch issue (`torch.load block asyncio loop · Issue #5879`) documenting that PyTorch holds the GIL and blocks the event loop. CUDA context init is an additional 1–3 second hit on first model load.

**How to avoid:**
Load all models in the detection thread's `run()` method after the thread starts, not in the lifecycle `start()` sequence. Lifecycle only starts the thread; the thread loads its own models asynchronously from the asyncio perspective. Signal readiness via an `asyncio.Event` set with `call_soon_threadsafe` when loading completes.

```python
class DetectionThread(threading.Thread):
    def run(self):
        # All model loading happens here, off the event loop thread
        self._broken_model = YOLO("broken_best.pt")
        self._crack_model = YOLO("crack_best.pt")
        self._ready_event.set()  # Signal lifecycle that models are ready
        self._detection_loop()
```

**Warning signs:**
- Startup takes 5+ seconds longer when camera is enabled
- Modbus "initial connection failed" logs on hardware that previously connected immediately
- Lifecycle startup sequence hangs on camera init step

**Phase to address:** Lifecycle integration phase (camera services startup/shutdown). Define the async-boundary contract between lifecycle and detection thread before model loading is implemented.

---

### Pitfall 4: QLabel.setPixmap() Called from Camera Thread (Not GUI Thread)

**What goes wrong:**
The camera display code calls `self.camera_label.setPixmap(...)` from a camera capture thread or detection thread. Qt silently queues the paint event on some platforms but crashes on others with "QObject: Cannot create children for a parent that is in a different thread." Even when it does not crash, the display update races with Qt's own repaint cycle, causing tearing, missed frames, or occasional segfaults on Linux.

**Why it happens:**
Qt enforces that all GUI operations happen on the thread that created the `QApplication`. `QLabel` and `QPixmap` are not thread-safe. Any cross-thread pixmap update bypasses Qt's object ownership model.

**How to avoid:**
Camera thread emits a Qt signal (`frame_ready = Signal(QImage)`) connected to a slot on the `CameraPage` widget. The signal carries a `QImage` (not `np.ndarray` or `QPixmap` — those are not safe to cross thread boundaries). The slot converts to `QPixmap` and calls `setPixmap` — all in the GUI thread.

```python
# Camera capture thread
class CameraThread(QThread):  # or threading.Thread with signal emission
    frame_ready = Signal(QImage)

    def _emit_frame(self, bgr_frame):
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.frame_ready.emit(image.copy())  # .copy() detaches from numpy buffer

# GUI widget slot
class CameraPage(QWidget):
    @Slot(QImage)
    def _on_frame_ready(self, image: QImage):
        self.camera_label.setPixmap(QPixmap.fromImage(image))
```

**Warning signs:**
- Application crashes when navigating to the camera page
- Occasional segfaults that only occur when the camera is running
- "QObject::setParent" or "timers cannot be stopped" error messages on shutdown

**Phase to address:** Camera GUI page phase. The signal/slot frame delivery pattern must be established before any display code is written.

---

### Pitfall 5: Config-Driven Optional Import Breaks at Runtime When camera.enabled=false

**What goes wrong:**
The camera module file is imported unconditionally by `lifecycle.py` even when `camera.enabled: false`. Inside that file, `import cv2`, `import torch`, or `from ultralytics import YOLO` fail with `ModuleNotFoundError` if those packages are not installed. The application crashes at startup on machines without the vision stack, even though the feature is disabled in config.

A related failure: the try/except guard wraps the import but the module variable is set to `None`, and later code that checks `if cv2 is None: return` misses a call site. One unguarded reference to `cv2` (e.g., in a type annotation evaluated at import time) causes `NameError`.

**Why it happens:**
Python evaluates module-level imports and type annotations at import time, not at use time. A `try: import cv2 except ImportError: cv2 = None` guard is bypassed by any `def foo(frame: cv2.Mat)` annotation in the same file.

**How to avoid:**
- The lifecycle uses `if config['camera']['enabled']` before importing anything camera-related
- Camera module files use `from __future__ import annotations` to defer annotation evaluation
- All camera imports live inside `if TYPE_CHECKING:` blocks or inside function bodies that are only called when the feature is enabled
- Use a boolean flag, not module-as-None: `CAMERA_AVAILABLE = False` then check the flag

```python
# lifecycle.py
async def _init_camera(self):
    if not self.config.get('camera', {}).get('enabled', False):
        logger.info("Camera disabled in config - skipping")
        return

    # Import ONLY after the config check passes
    from ..services.vision.camera_service import CameraService
    self.camera_service = CameraService(self.config)
```

**Warning signs:**
- `ModuleNotFoundError: No module named 'cv2'` in traceback that includes lifecycle startup
- Application that worked without camera suddenly fails after adding camera module files
- Type annotations referencing `cv2` or `torch` appear at module level

**Phase to address:** Camera module foundation phase (the very first camera phase). The import guard pattern must be established before any other camera code is written.

---

### Pitfall 6: BGR vs RGB Color Space Corruption in the Detection-Display Pipeline

**What goes wrong:**
OpenCV reads frames in BGR. The detection model (RT-DETR) expects RGB (standard PyTorch/torchvision convention). The display path (QImage) also expects RGB. A missing `cvtColor` conversion at one stage causes: (a) wrong colors in the live display — the image looks orange/blue-tinted, or (b) reduced detection accuracy because the model sees swapped channels that don't match training data color statistics, causing lower confidence scores on real detections.

The worst case: a conversion is applied twice (once before detection, once before display), causing a double-swap that looks correct in the display but feeds corrupted data to the model.

**Why it happens:**
The BGR/RGB distinction is a constant source of confusion when multiple consumers (model inference, recording, display) each touch the same frame. Each consumer has a different expectation, and the format is invisible at runtime — a `np.ndarray` carries no channel order metadata.

**How to avoid:**
Define one canonical frame format for the internal pipeline (choose RGB for model compatibility) and convert once at the camera capture boundary. Document this explicitly in the camera service.

```python
class CameraCapture:
    def get_frame_rgb(self) -> np.ndarray:
        """Returns frame in RGB format. Convert once here, never again downstream."""
        with self._lock:
            if self._latest_frame_bgr is None:
                return None
            return cv2.cvtColor(self._latest_frame_bgr, cv2.COLOR_BGR2RGB)

    def save_jpeg_bgr(self, path: str):
        """cv2.imwrite expects BGR — use raw frame, not converted."""
        with self._lock:
            if self._latest_frame_bgr is not None:
                cv2.imwrite(path, self._latest_frame_bgr)
```

**Warning signs:**
- Live display shows orange skin tones or blue sky that should appear red/normal
- Detection confidence scores are systematically lower than expected from the model's training metrics
- A "color looks correct" check passes in isolation but fails end-to-end

**Phase to address:** Camera module phase (frame capture and format contract). Establish the canonical format decision in the camera service before the display or detection pipelines touch any frames.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Call detection every frame (30 Hz) instead of on a timer | Simpler code | GPU thrashes at 30 Hz; existing 10 Hz ML model and detection compete for CUDA; detection latency spikes under load | Never — use a configurable detection interval (e.g., every 3rd frame or 1 Hz) |
| Storing raw frames (PNG/BMP) instead of JPEG | No lossy compression | Disk fills in hours on an industrial panel PC with limited storage | Never for continuous recording; JPEG with quality 85 is the right default |
| Running LDC edge detection on CPU inside detection thread | Avoids GPU memory pressure | LDC on large frames (1280x720) takes 80–200ms on CPU, stalling the detection thread | Acceptable only if frame resolution is 640x480 or smaller |
| Importing torch at module top-level for type hints | Convenient | Breaks camera.enabled=false deployments without GPU drivers | Never — use `TYPE_CHECKING` guard |
| Writing detection results to SQLite synchronously from detection thread | Simplest code | SQLite calls from a non-queue thread bypass the existing write-queue pattern, risking lock contention with the 10 Hz pipeline | Never — use the existing SQLite queue pattern |
| Loading all three models sequentially in lifecycle startup | Deterministic order | Blocks asyncio event loop for 6–18 seconds on cold start | Never — load in detection thread, not lifecycle |

---

## Integration Gotchas

Common mistakes when connecting camera/AI components to the existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SQLite (detection results) | Writing from detection thread directly using `sqlite3.connect()` | Use the existing `SQLiteService` queue pattern: call `db_service.queue_write(sql, params)` from the detection thread |
| IoT / ThingsBoard | Calling `iot_service.send_telemetry()` synchronously from detection thread | Queue detection results to the main data pipeline so the existing IoT batching handles them at the next 10 Hz cycle |
| 10 Hz processing loop | Passing detection results via a shared dict without a lock | Use `threading.Lock` or `queue.Queue` for the detection-result-to-pipeline handoff; the same lock pattern used by `AnomalyManager` |
| Lifecycle shutdown | Not stopping camera/detection threads before database flush | Add camera stop to lifecycle `stop()` before step 5 (SQLite flush), mirroring how GUI thread is joined first |
| Config | Reading `camera.enabled` at each call site | Read once during `_init_camera()` and store as `self._camera_enabled`; avoids scattered config reads |
| Health monitor | Not including camera/detection thread health in the 30s health check | Add frame rate and detection queue depth to `get_status()` so health monitor can alarm on camera stalls |

---

## Performance Traps

Patterns that work during testing but fail under sustained industrial operation.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Detection thread reads frames faster than they are produced | CPU spins at 100% in detection thread polling an empty queue | Use `queue.get(timeout=0.1)` instead of `get_nowait()` with a spin loop | Immediately — becomes visible as high CPU in `top` |
| QTimer interval set to 0ms for "fastest possible" display | Qt paint events flood the GUI thread; existing GUI updates (graphs, sensor labels) starve | Use 100–200ms QTimer interval for camera display (5–10 Hz is sufficient for live monitoring) | When camera page is open and operator interacts with other controls |
| Saving JPEG per-frame during active detection at 30 Hz | Disk I/O 1–3 MB/s sustained; SSD write amplification; detection thread stalls waiting for `cv2.imwrite` | Write JPEG in a separate writer thread with a bounded queue; only record when `testere_durumu == 3` (cutting state) | After 30–60 minutes of continuous operation |
| Loading 3 models without `torch.no_grad()` context | Gradient buffers allocated for every inference call; GPU memory doubles | Wrap all inference in `with torch.no_grad():` | Models load fine; OOM error appears during the first cutting session |
| Not calling `cap.release()` on camera service stop | USB camera device remains held; restart required to re-open camera | Always call `cap.release()` in the camera thread's cleanup; add to lifecycle stop sequence | When operator exits and restarts application |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Camera display working:** Often missing RGB conversion — verify colors look correct on real hardware, not just a test image
- [ ] **Detection results saving:** Often missing the SQLite queue pattern — verify with `db_service.get_stats()['queue_size']` that writes are going through the queue, not direct sqlite3 calls
- [ ] **config camera.enabled=false:** Often still imports cv2 — verify by running on a machine without OpenCV installed; startup should succeed
- [ ] **Lifecycle shutdown:** Often camera thread is not joined before shutdown completes — verify no "Timers cannot be stopped from another thread" errors on exit
- [ ] **GPU memory:** Often `torch.no_grad()` missing — verify with `torch.cuda.memory_allocated()` before and after inference; should not grow
- [ ] **Detection thread safety:** Often models accessed from more than one call site — verify there is exactly one path to each model's `.predict()` method
- [ ] **IoT integration:** Often detection results bypass the IoT service entirely — verify ThingsBoard receives detection telemetry by checking device attributes after a test cut
- [ ] **JPEG recording:** Often records every frame even when saw is idle — verify recording only activates when `testere_durumu == 3`

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Asyncio event loop blocked by `cap.read()` | MEDIUM | Refactor: move all capture to a dedicated thread; no asyncio changes needed in detection code |
| Model shared across threads (race condition) | MEDIUM | Add `threading.Lock` around all `.predict()` calls as temporary fix; proper fix is per-thread model instances |
| `torch.load()` blocking startup | LOW | Move model loading from `_init_camera()` to `DetectionThread.run()` — typically a 10-line change |
| Camera imported unconditionally (import error) | LOW | Add lifecycle config guard; add `from __future__ import annotations` to camera module files |
| BGR/RGB double conversion (bad predictions) | LOW | Add a `_frame_format = "RGB"` constant to camera service; audit all call sites in 30 minutes |
| QLabel.setPixmap() from wrong thread (crash) | HIGH | Must redesign frame delivery to use Qt signal/slot; no quick fix; plan 1–2 hours refactor |
| JPEG write stalling detection thread | MEDIUM | Extract JPEG write to a writer thread with bounded queue; 50-line change but requires adding a new thread lifecycle |
| Detection results not reaching IoT | LOW | Add detection result fields to the telemetry dict in data pipeline; no architectural change needed |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| cap.read() blocking asyncio (Pitfall 1) | Camera capture module phase | Measure Modbus read rate (must stay at 10 Hz) with camera running |
| Shared model instances (Pitfall 2) | Detection pipeline phase | Code review: grep for model instantiation outside thread `run()` method |
| torch.load() blocking startup (Pitfall 3) | Lifecycle integration phase | Time startup with and without camera enabled; delta must be < 500ms |
| setPixmap() from wrong thread (Pitfall 4) | Camera GUI page phase | Run application with Python's `-W error` mode; any cross-thread Qt warning becomes an error |
| Unconditional cv2 import (Pitfall 5) | Camera module foundation (first camera phase) | Test startup with camera.enabled=false on a machine without OpenCV installed |
| BGR/RGB corruption (Pitfall 6) | Camera module phase | Manual verification: display a known test image (red object); verify it appears red |
| JPEG recording stalling detection | JPEG recording phase | Profile detection thread frame processing time; must stay < 50ms per frame |
| SQLite detection writes bypassing queue | Detection results storage phase | Check `db_service.get_stats()` — queue_size should increase, not zero |
| Lifecycle shutdown ordering | Lifecycle integration phase | Automated: run app, start camera, kill gracefully; no segfault, no "timer" errors |
| torch.no_grad() missing (GPU OOM) | Detection pipeline phase | `torch.cuda.memory_allocated()` must be stable after 100 inference calls |

---

## Sources

- [opencv/opencv Issue #24393: How to avoid blocking with cv2.VideoCapture.read()](https://github.com/opencv/opencv/issues/24393) — confirms blocking nature of VideoCapture.read()
- [opencv/opencv Issue #24229: Does cv::VideoCapture have any thread lock?](https://github.com/opencv/opencv/issues/24229) — documents thread safety constraints
- [Ultralytics YOLO Thread-Safe Inference Guide](https://docs.ultralytics.com/guides/yolo-thread-safe-inference/) — official guidance on per-thread model instantiation
- [pytorch/pytorch Issue #5879: torch.load blocks asyncio loop](https://github.com/pytorch/pytorch/issues/5879) — confirmed asyncio blocking during torch.load
- [PyTorch CUDA semantics documentation](https://docs.pytorch.org/docs/stable/notes/cuda.html) — CUDA context initialization overhead
- [PySide6 QImage documentation](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html) — thread safety constraints for QPixmap/QImage
- [How to display OpenCV video in PyQt apps (gist)](https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1) — QThread + Signal pattern for OpenCV/Qt
- [Multithreading PySide6 applications with QThreadPool — pythonguis.com](https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/) — Qt threading patterns
- [Python optional imports discussion — discuss.python.org](https://discuss.python.org/t/optional-imports-for-optional-dependencies/104760) — config-driven import guard patterns
- [PyTorch Frequently Asked Questions — memory management](https://docs.pytorch.org/docs/stable/notes/faq.html) — `torch.no_grad()` and GPU memory
- [Codebase ARCHITECTURE.md](../.planning/codebase/ARCHITECTURE.md) — existing concurrency model (asyncio + threading hybrid)
- [src/core/lifecycle.py](../src/core/lifecycle.py) — existing startup/shutdown sequence; camera services must follow same pattern

---
*Pitfalls research for: camera vision & AI detection integration into existing industrial async control system*
*Researched: 2026-03-16*
