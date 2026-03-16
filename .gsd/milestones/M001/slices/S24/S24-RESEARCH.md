# S24: Camera GUI — Research

**Date:** 2026-03-16

## Summary

This is a well-understood port of the old project's `pyside_camera.py` (1347 lines) into the current codebase's stacked-widget architecture. The old camera page was a standalone fullscreen QWidget with its own sidebar — the new system uses a `QStackedWidget` inside `MainController` where each page is a child widget at 1528×1080 (content area, no sidebar). The camera page reads exclusively from `CameraResultsStore` — no imports from `services/camera/` in the GUI module.

The integration requires threading `camera_results_store` through the chain: `lifecycle → GUIApplication → MainController → CameraController`. The data contract is already established: the store publishes `latest_frame` (JPEG bytes), `broken_count`, `tooth_count`, `crack_count`, `wear_percentage`, `health_score`, `health_status`, `health_color`, `frame_count`, `is_recording`, `recording_path`, `fps_actual`, plus detection timestamps. The GUI controller needs only `snapshot()` calls on QTimer callbacks.

The 5th sidebar nav button goes at y=649 (121px spacing from the 4th button at y=528), matching the old project's layout exactly.

## Recommendation

Build in two tasks:

1. **CameraController widget** — the camera page itself (`camera_controller.py`), a QWidget child of QStackedWidget. Programmatic layout (no .ui file — matches all other controllers in the current codebase). Reads from `CameraResultsStore` via 3 QTimers (500ms frame, 1000ms stats, 2000ms health). Includes: live frame display, broken/crack detection info frames with OK/alert indicators, sequential image thumbnails (4×240×150), wear percentage, health score with status text and color, and a `stop_timers()` method.

2. **MainController + GUIApplication + lifecycle wiring** — thread `camera_results_store` through the creation chain; add conditional 5th sidebar button; add camera page to stacked widget; wire `stop_timers()` into `closeEvent`.

## Implementation Landscape

### Key Files

- `src/gui/controllers/camera_controller.py` — **NEW**. The camera page widget. Receives `CameraResultsStore` via constructor. No dependency on `CameraService`, `VisionService`, or any camera thread — purely reads the store. Uses lazy cv2 import (only for frame decoding from JPEG bytes → QImage) inside method bodies, not at module level.
- `src/gui/controllers/main_controller.py` — **MODIFIED**. Add optional `camera_results_store=None` parameter to `__init__`. Conditionally create 5th sidebar button (`btnCamera`) at y=649 and CameraController page at stack index 4. Lazy-import `CameraController` inside config guard. Wire `camera_page.stop_timers()` into `closeEvent`. Update `_switch_page()` to handle index 4.
- `src/gui/app.py` — **MODIFIED**. Thread `camera_results_store` through `GUIApplication.__init__()` to `MainController`.
- `src/core/lifecycle.py` — **MODIFIED**. Pass `camera_results_store=self.camera_results_store` to `GUIApplication` constructor in `_init_gui()`.

### Data Contract (CameraResultsStore keys consumed by GUI)

| Key | Type | Timer | Usage |
|-----|------|-------|-------|
| `latest_frame` | `bytes` (JPEG) | 500ms | Decode to QImage → QPixmap → QLabel |
| `broken_count` | `int` | 1000ms | Detection stat label |
| `tooth_count` | `int` | 1000ms | Detection stat label |
| `crack_count` | `int` | 1000ms | Detection stat label |
| `broken_confidence` | `float` | 1000ms | Optional display |
| `crack_confidence` | `float` | 1000ms | Optional display |
| `wear_percentage` | `float` | 2000ms | Wear % label |
| `health_score` | `float` | 2000ms | Health % label |
| `health_status` | `str` | 2000ms | Status text (Sağlıklı/İyi/Orta/Kritik/Tehlikeli) |
| `health_color` | `str` (hex) | 2000ms | Label color styling |
| `is_recording` | `bool` | 1000ms | Recording state indicator |
| `frame_count` | `int` | 1000ms | Frame counter display |
| `last_detection_ts` | `str` | 1000ms | Last detection timestamp |

### Widget Layout (1528×1080 content area)

Ported from old `camera_widget_ui.py`, adjusted for content-area dimensions (old was 1920×1080 full screen; new is 1528×1080 — sidebar is handled by MainController):

- **KameraFrame** — main live feed area, ~934×525 at top-center, with detection stat overlays (broken count, crack count) inside
- **SiraliGoruntuFrame** — sequential thumbnails strip, 934×150, below the camera frame
- **KirikTespitiFrame** — broken tooth detection panel, right side, ~505×438
- **CatlakTespitiFrame** — crack detection panel, right side below broken, ~505×438
- **TestereDegisimFrame** — blade change info strip, below thumbnails
- **AsinmaYuzdesiFrame** — wear % display, bottom-left, 260×105
- **TestereSagligiFrame** — health score display, bottom-center, 260×105
- **TestereDurumuFrame** — health status text display, bottom-right, 260×105

All positions are translated from old coordinates by subtracting 392px from x (sidebar width) — except frames already positioned relative to the content area.

### JPEG-to-QImage Conversion Pattern

The store holds JPEG bytes (not raw numpy). Conversion in the GUI thread:

```python
from PySide6.QtGui import QImage, QPixmap

jpeg_bytes = self.results_store.get('latest_frame')
if jpeg_bytes:
    qimage = QImage()
    qimage.loadFromData(jpeg_bytes)  # QImage decodes JPEG natively
    self.camera_label.setPixmap(
        QPixmap.fromImage(qimage).scaled(
            self.camera_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    )
```

This avoids importing cv2 in the GUI module entirely — `QImage.loadFromData()` handles JPEG decoding.

### Build Order

1. **CameraController** first — it's self-contained, depends only on `CameraResultsStore` (already built in S20). Can be py_compile verified independently. This is the bulk of the work (~400-500 lines).
2. **Wiring** second — `app.py`, `main_controller.py`, `lifecycle.py` modifications. These are small, surgical edits that wire the controller into the application. Must be done together since they form a chain.

### Verification Approach

1. `py_compile` on all modified files
2. Import check: `from src.gui.controllers.camera_controller import CameraController` succeeds
3. Constructor check: `CameraController(results_store, parent=None)` accepts a `CameraResultsStore` instance
4. `stop_timers()` method exists and stops all 3 QTimers
5. MainController with `camera_results_store=None` → no camera button, no camera page (backward compat)
6. MainController with `camera_results_store=CameraResultsStore()` → 5th button at y=649, page at index 4
7. Lazy import guard: camera_controller.py module does NOT import cv2 or torch at module level
8. Zero-import guard preserved: with `camera.enabled=false`, no camera GUI code is imported

## Constraints

- **No .ui file** — all existing controllers in the current codebase use programmatic layout. CameraController must follow the same pattern. The old project's `camera_widget_ui.py` is reference for geometry/styling only.
- **No cv2 at module level in camera_controller.py** — the JPEG bytes in `CameraResultsStore` are decoded using `QImage.loadFromData()`, which handles JPEG natively. No OpenCV needed in the GUI layer.
- **Content area is 1528×1080** — the sidebar (392px wide) is owned by MainController. CameraController must not create its own sidebar or notification bar.
- **QTimer callbacks run in Qt thread** — safe for QLabel.setPixmap(). Never call blocking operations in timer callbacks.

## Common Pitfalls

- **setPixmap from wrong thread** — all frame updates happen via QTimer callbacks in the Qt thread. The CameraController never touches camera threads directly.
- **QImage from raw numpy** — not needed. Store holds JPEG bytes; use `QImage.loadFromData()` which is the simplest path and avoids BGR/RGB confusion entirely.
- **Module-level camera imports in main_controller.py** — the `from .camera_controller import CameraController` must be inside the `if camera_config.get('enabled', False):` guard to preserve zero-import guarantee.
