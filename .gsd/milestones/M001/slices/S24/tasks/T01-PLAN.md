---
estimated_steps: 8
estimated_files: 1
---

# T01: Build CameraController widget

**Slice:** S24 — Camera GUI
**Milestone:** M001

## Description

Create the CameraController QWidget — the camera page that lives inside MainController's QStackedWidget. This is a self-contained widget (1528×1080 content area) that reads exclusively from CameraResultsStore via 3 QTimers. It displays: live camera feed, broken/crack detection panels with counts and OK/alert indicators, 4 sequential thumbnails, wear percentage, health score with status text and dynamic color. All programmatic layout — no .ui file. No cv2 or torch imports at module level.

## Steps

1. Create `src/gui/controllers/camera_controller.py` with standard imports: PySide6.QtWidgets (QWidget, QFrame, QLabel), PySide6.QtCore (QTimer, Qt), PySide6.QtGui (QImage, QPixmap, QFont, QColor). Import logging. No cv2, torch, or camera service imports.

2. Define `CameraController(QWidget)` class with `__init__(self, results_store, parent=None)`. Store `self.results_store = results_store`. Call `self._setup_ui()` then `self._setup_timers()`.

3. Implement `_setup_ui()` with programmatic layout for 1528×1080:
   - Set dark background (#0A0E1A)
   - **KameraFrame** — QFrame at roughly (20, 20, 934, 525) containing a QLabel (`self.camera_label`) for the live feed. Background #1A1F37 with border-radius. "Kamera Görüntüsü" title label.
   - **SiraliGoruntuFrame** — QFrame below camera frame (~20, 555, 934, 170) with 4 QLabel thumbnails (`self.thumbnail_labels[]`) each 220×140, plus "Sıralı Görüntüler" title.
   - **KirikTespitiFrame** — QFrame right side (~970, 20, 538, 350) with "Kırık Diş Tespiti" title, broken count label, tooth count label, last detection timestamp label, OK/alert status indicator label (green ✓ or red ✗).
   - **CatlakTespitiFrame** — QFrame right side below broken (~970, 385, 538, 350) with "Çatlak Tespiti" title, crack count label, last detection timestamp label, OK/alert status indicator.
   - **AsinmaYuzdesiFrame** — QFrame bottom area (~20, 740, 300, 120) with "Aşınma Yüzdesi" title and wear % value label.
   - **TestereSagligiFrame** — QFrame bottom area (~340, 740, 300, 120) with "Testere Sağlığı" title and health score value label.
   - **TestereDurumuFrame** — QFrame bottom area (~660, 740, 300, 120) with "Testere Durumu" title and health status text label with dynamic color.
   - **Recording/FPS info** — small labels at bottom-right showing frame count and recording state.
   - All frames use dark theme: background rgba(26, 31, 55, 200), border-radius 15px, #F4F6FC text, 'Plus Jakarta Sans' font family.

4. Implement `_setup_timers()`:
   - `self._frame_timer = QTimer(self)` → 500ms → `self._update_frame`
   - `self._stats_timer = QTimer(self)` → 1000ms → `self._update_stats`
   - `self._health_timer = QTimer(self)` → 2000ms → `self._update_health`
   - Start all three timers.

5. Implement `_update_frame()`:
   - Call `snapshot = self.results_store.snapshot()`
   - Get `snapshot.get('latest_frame')` — if bytes, create `QImage()`, call `qimage.loadFromData(jpeg_bytes)`, convert to QPixmap, scale to camera_label size with KeepAspectRatio + SmoothTransformation, set on camera_label.
   - Update thumbnail strip: shift existing thumbnails left, add new one from current frame (scaled to 220×140). Keep max 4.
   - Wrap in try/except with logger.error.

6. Implement `_update_stats()`:
   - Read from snapshot: broken_count, tooth_count, crack_count, last_detection_ts, frame_count, is_recording
   - Update broken count label, tooth count label, crack count label
   - Update OK/alert indicators: if broken_count > 0 → red "✗ UYARI" else green "✓ OK"; same for crack_count
   - Update frame count and recording state labels
   - Wrap in try/except with logger.error.

7. Implement `_update_health()`:
   - Read from snapshot: wear_percentage, health_score, health_status, health_color
   - Update wear % label (e.g. "23.5%")
   - Update health score label (e.g. "85.2%")
   - Update health status label text and color using health_color hex value
   - Wrap in try/except with logger.error.

8. Implement `stop_timers()`:
   - Stop all 3 QTimers. Log "CameraController timers stopped".

## Must-Haves

- [ ] CameraController(results_store, parent=None) constructor signature
- [ ] Programmatic layout — no .ui file
- [ ] No module-level cv2, torch, or camera service imports
- [ ] 3 QTimers at 500ms/1000ms/2000ms intervals
- [ ] Live feed display using QImage.loadFromData() for JPEG decoding
- [ ] Broken tooth detection panel with count, OK/alert indicator
- [ ] Crack detection panel with count, OK/alert indicator
- [ ] 4 sequential thumbnail labels
- [ ] Wear percentage display
- [ ] Health score display
- [ ] Health status text with dynamic color from health_color
- [ ] stop_timers() method that stops all 3 QTimers
- [ ] Dark theme styling consistent with other controllers

## Verification

- `python -m py_compile src/gui/controllers/camera_controller.py` — compiles clean
- `python -c "from src.gui.controllers.camera_controller import CameraController; print('OK')"` — imports successfully
- `grep -c 'import cv2' src/gui/controllers/camera_controller.py` → 0
- `grep -c 'import torch' src/gui/controllers/camera_controller.py` → 0
- `python -c "import inspect; from src.gui.controllers.camera_controller import CameraController; sig = inspect.signature(CameraController.__init__); params = list(sig.parameters.keys()); assert 'results_store' in params, f'Missing results_store: {params}'; assert hasattr(CameraController, 'stop_timers'), 'Missing stop_timers'; print('Contract OK')"` — passes

## Inputs

- `src/services/camera/results_store.py` — CameraResultsStore with snapshot() API returning dict with keys: latest_frame, broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status, health_color, frame_count, is_recording, last_detection_ts
- S24-RESEARCH.md — Widget layout geometry, JPEG-to-QImage conversion pattern, data contract table
- Existing controllers (`sensor_controller.py`, `monitoring_controller.py`) — pattern reference for dark theme styling, QTimer usage, stop_timers() convention

## Expected Output

- `src/gui/controllers/camera_controller.py` — New ~400-500 line QWidget with full camera page layout and 3 timer-driven update methods
