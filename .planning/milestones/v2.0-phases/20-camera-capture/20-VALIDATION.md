---
phase: 20
slug: camera-capture
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Wave 0 installs if missing) |
| **Config file** | none — Wave 0 creates tests/ directory |
| **Quick run command** | `python3 -m pytest tests/test_camera_results_store.py tests/test_camera_service.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_camera_results_store.py tests/test_camera_service.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | CAM-03 | unit | `python3 -m pytest tests/test_camera_results_store.py -x` | ❌ W0 | ⬜ pending |
| 20-01-02 | 01 | 1 | CAM-03 | unit | `python3 -m pytest tests/test_camera_service.py::test_start_returns_false_on_no_device -x` | ❌ W0 | ⬜ pending |
| 20-01-03 | 01 | 1 | CAM-03 | unit | `python3 -m pytest tests/test_camera_service.py::test_cap_props_applied -x` | ❌ W0 | ⬜ pending |
| 20-01-04 | 01 | 1 | CAM-04 | unit | `python3 -m pytest tests/test_camera_service.py::test_recording_writes_jpegs -x` | ❌ W0 | ⬜ pending |
| 20-01-05 | 01 | 1 | CAM-05 | unit | `python3 -m pytest tests/test_camera_service.py::test_recording_dir_format -x` | ❌ W0 | ⬜ pending |
| 20-01-06 | 01 | 1 | CAM-03 | unit | `python3 -m pytest tests/test_camera_results_store.py::test_latest_frame_updated -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/test_camera_results_store.py` — stubs for CAM-03 (thread-safe store)
- [ ] `tests/test_camera_service.py` — stubs for CAM-03 (capture), CAM-04 (JPEG write), CAM-05 (dir structure)
- [ ] `pip install pytest` — if not present

*Note: Tests for CameraService should mock `cv2.VideoCapture` to avoid requiring physical hardware in CI. Use `unittest.mock.patch("cv2.VideoCapture")`.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Auto-discovery finds real camera device | CAM-03 | Requires physical USB camera attached | Plug camera, run `python3 -c "from src.services.camera.camera_service import CameraService; ..."`, verify logs show discovered device |
| FPS actual matches hardware capability (~10fps at 720p) | CAM-03 | Hardware-dependent measurement | Run capture for 10s, check `fps_actual` in results store ≈ 10 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
