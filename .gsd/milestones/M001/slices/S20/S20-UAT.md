# S20: Camera Capture — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: No camera hardware available in dev environment. S20 is contract-level — proving imports, instantiation, thread-safe store semantics, and graceful failure. Live runtime testing requires S22 lifecycle wiring and physical camera.

## Preconditions

- Working directory is the M001 worktree
- Python virtual environment is active with `opencv-python-headless>=4.11.0` installed
- No physical camera device required (tests verify graceful failure path)

## Smoke Test

```bash
python -c "from src.services.camera import CameraResultsStore, CameraService; print('smoke OK')"
```

Expected: prints `smoke OK` — both classes importable from the package.

## Test Cases

### 1. CameraResultsStore thread-safe operations

1. Run:
   ```bash
   python -c "
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   s.update('k', 1)
   assert s.get('k') == 1
   d = s.snapshot()
   assert d == {'k': 1}
   s.update('k', 2)
   assert d['k'] == 1, 'snapshot must be independent copy'
   assert s.get('k') == 2
   print('PASS')
   "
   ```
2. **Expected:** prints `PASS` — update, get, and snapshot copy semantics work correctly.

### 2. CameraResultsStore update_batch and defaults

1. Run:
   ```bash
   python -c "
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   s.update_batch({'a': 1, 'b': 2, 'c': 3})
   assert s.snapshot() == {'a': 1, 'b': 2, 'c': 3}
   assert s.get('missing') is None
   assert s.get('missing', 'default') == 'default'
   print('PASS')
   "
   ```
2. **Expected:** prints `PASS` — batch update merges atomically, get returns default for missing keys.

### 3. CameraResultsStore empty snapshot baseline

1. Run:
   ```bash
   python -c "
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   assert s.snapshot() == {}
   print('PASS')
   "
   ```
2. **Expected:** prints `PASS` — fresh store returns empty dict (diagnostic baseline).

### 4. CameraService instantiation without I/O

1. Run:
   ```bash
   python -c "
   from src.services.camera.camera_service import CameraService
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   cs = CameraService({
       'device_id': 99,
       'resolution': {'width': 640, 'height': 480},
       'fps': 30,
       'jpeg_quality': 85,
       'recordings_path': '/tmp/test_rec'
   }, s)
   assert not cs.is_running
   assert cs.get_current_frame() is None
   print('PASS')
   "
   ```
2. **Expected:** prints `PASS` — constructor does no I/O, is_running is False, no current frame.

### 5. CameraService graceful failure with non-existent device

1. Run:
   ```bash
   python -c "
   import asyncio
   from src.services.camera.camera_service import CameraService
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   cs = CameraService({
       'device_id': 99,
       'resolution': {'width': 640, 'height': 480},
       'fps': 30,
       'jpeg_quality': 85,
       'recordings_path': '/tmp/test_rec'
   }, s)
   result = asyncio.run(cs.start())
   assert result is False, 'start() must return False for missing camera'
   assert not cs.is_running
   print('PASS')
   "
   ```
2. **Expected:** prints `PASS` with a log line containing `Camera open failed — device_id=99 not available`. No crash, no exception.

### 6. opencv-python-headless in requirements

1. Run:
   ```bash
   grep 'opencv-python-headless' requirements.txt
   ```
2. **Expected:** matches `opencv-python-headless>=4.11.0`

### 7. cv2 importable with correct version

1. Run:
   ```bash
   python -c "import cv2; v = cv2.__version__; assert v.startswith('4.'); print(f'cv2 {v} OK')"
   ```
2. **Expected:** prints `cv2 4.x.x OK`

### 8. Zero-import guard preserved

1. Run:
   ```bash
   python -c "
   import ast
   with open('src/core/lifecycle.py') as f:
       tree = ast.parse(f.read())
   for node in ast.iter_child_nodes(tree):
       if isinstance(node, ast.ImportFrom) and node.module and 'camera' in node.module:
           raise AssertionError(f'Top-level camera import at line {node.lineno}')
       if isinstance(node, ast.Import):
           for alias in node.names:
               if 'camera' in alias.name:
                   raise AssertionError(f'Top-level camera import at line {node.lineno}')
   print('PASS — zero-import guard intact')
   "
   ```
2. **Expected:** prints `PASS — zero-import guard intact` — lifecycle.py has no unconditional camera imports.

## Edge Cases

### start_recording before start

1. Run:
   ```bash
   python -c "
   from src.services.camera.camera_service import CameraService
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   cs = CameraService({'device_id': 0, 'resolution': {'width': 640, 'height': 480}, 'fps': 30, 'jpeg_quality': 85, 'recordings_path': '/tmp/test_rec'}, s)
   assert cs.start_recording() is False, 'cannot record when not running'
   print('PASS')
   "
   ```
2. **Expected:** prints `PASS` — start_recording returns False when service is not running.

### stop when not running

1. Run:
   ```bash
   python -c "
   import asyncio
   from src.services.camera.camera_service import CameraService
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   cs = CameraService({'device_id': 0, 'resolution': {'width': 640, 'height': 480}, 'fps': 30, 'jpeg_quality': 85, 'recordings_path': '/tmp/test_rec'}, s)
   asyncio.run(cs.stop())
   print('PASS — stop on idle is noop')
   "
   ```
2. **Expected:** prints `PASS — stop on idle is noop` — stop() is a no-op when service is not running.

### Config defaults

1. Run:
   ```bash
   python -c "
   from src.services.camera.camera_service import CameraService
   from src.services.camera.results_store import CameraResultsStore
   s = CameraResultsStore()
   cs = CameraService({}, s)
   assert cs._device_id == 0
   assert cs._width == 640
   assert cs._height == 480
   assert cs._fps == 30
   assert cs._jpeg_quality == 85
   print('PASS — defaults applied')
   "
   ```
2. **Expected:** prints `PASS — defaults applied` — empty config uses sensible defaults.

## Failure Signals

- `ImportError` on `from src.services.camera import CameraService` — cv2 not installed or Qt conflict
- `CameraService.start()` raises exception instead of returning False — missing graceful failure handling
- `CameraResultsStore.snapshot()` returns reference to internal dict (mutation leaks) — copy semantics broken
- Top-level `import camera` in lifecycle.py — zero-import guard broken

## Requirements Proved By This UAT

- CAM-03 (partial) — OpenCV capture code exists with configurable resolution/FPS, but not proven end-to-end without camera hardware
- CAM-04 (partial) — JPEG encoder thread pool built, but not proven with actual frames
- CAM-05 (partial) — Timestamped directory creation logic exists, verified at code level
- DET-05 (partial) — CameraResultsStore thread-safe semantics proven via update/get/snapshot tests

## Not Proven By This UAT

- Actual frame capture from a real camera device
- JPEG file writing during recording (requires running camera)
- FPS measurement accuracy
- Frame drop behavior under load
- Multi-thread save worker pool performance
- Integration with lifecycle (S22), detection (S21), IoT (S23), or GUI (S24)

## Notes for Tester

- All tests run without a physical camera — they verify the software contract, not hardware integration
- The `device_id=99` tests will emit an OpenCV error line (`[ERROR:0@...]`) to stderr — this is expected and part of graceful failure handling
- If testing on a machine with a camera, `device_id=0` in start() should return True and `is_running` should be True
