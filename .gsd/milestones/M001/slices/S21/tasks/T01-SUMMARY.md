---
id: T01
parent: S21
milestone: M001
provides:
  - Vendored LDC model definition (modelB4.py) for wear edge detection
  - HealthCalculator class with scoring, status, and color thresholds
  - AI/Vision dependencies declared (ultralytics, torch, torchvision)
  - LDC checkpoint path in camera config
key_files:
  - src/services/camera/modelB4.py
  - src/services/camera/health_calculator.py
  - requirements.txt
  - config/config.yaml
key_decisions:
  - HealthCalculator uses class constants (not instance vars) for BROKEN_WEIGHT/WEAR_WEIGHT — matches reference formula exactly
patterns_established:
  - Vendored ML model files get `from __future__ import annotations` prepended, rest untouched
  - Health calculator is a standalone class with no torch dependency — importable without triggering heavy ML imports
observability_surfaces:
  - logger.debug on each saw health calculation with broken%, wear%, health%
  - logger.error on calculation exceptions (broken percentage, saw health)
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Vendor modelB4, build HealthCalculator, update deps and config

**Vendored LDC model definition, built HealthCalculator with correct 70/30 weighted formula, added AI deps and config**

## What Happened

Copied modelB4.py from old project into `src/services/camera/modelB4.py` with `from __future__ import annotations` prepended. The file is a pure PyTorch module definition (~240 lines) with LDC, CoFusion, DenseBlock, UpConvBlock classes — kept verbatim.

Built `HealthCalculator` class porting the formula from old project's `SawHealthCalculator`. Same weighted formula (BROKEN_WEIGHT=0.7, WEAR_WEIGHT=0.3), same Turkish status labels, same hex color codes. Added clamping on both broken percentage (0-100) and wear input (0-100). Exception handler returns 100.0 (assume healthy).

Added `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0` to requirements.txt in a new "# AI / Vision" section. Added `ldc_checkpoint_path: "data/models/ldc/16_model.pth"` to `camera.wear` in config.yaml.

## Verification

- `from src.services.camera.modelB4 import LDC` → **OK** (torch loads, LDC class available)
- `HealthCalculator().calculate_saw_health(100, 5, 20.0)` → **90.5** (within 90-100 range) → **OK**
- All 10 threshold boundary tests pass (80/60/40/20 for status and color) → **OK**
- `grep` for ultralytics, torch>=, torchvision in requirements.txt → **OK**
- `grep` for ldc_checkpoint_path in config.yaml → **OK**
- `from src.services.camera import CameraResultsStore` → **OK** (zero-import guard intact, no torch triggered)

### Slice-Level Verification Status (T01 scope)

| Check | Status |
|-------|--------|
| health_calculator OK (score math) | ✅ pass |
| status/color OK | ⚠️ partial — plan test has `get_health_status(55.0)=='İyi'` but 55 < 60 correctly returns "Orta" per reference code. All actual thresholds verified correct. |
| modelB4 OK | ✅ pass |
| detection_worker OK | ⏳ T02 |
| ldc_worker OK | ⏳ T03 |
| zero-import OK | ✅ pass |
| detection instantiation OK | ⏳ T02 |
| ldc instantiation OK | ⏳ T03 |
| requirements OK | ✅ pass |
| config OK | ✅ pass |

## Diagnostics

- `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); print(h.calculate_saw_health(100, 5, 20.0))"` — quick health score check
- `python3 -c "from src.services.camera.modelB4 import LDC; print(sum(p.numel() for p in LDC().parameters()))"` — model parameter count
- Health calculator logs at DEBUG level — enable with `logging.basicConfig(level=logging.DEBUG)`

## Deviations

- Slice verification test `get_health_status(55.0)=='İyi'` is a test error in the plan — 55 < 60 returns "Orta" per the reference code's >=60 threshold. The HealthCalculator implementation matches the reference exactly. Downstream tasks should use `get_health_status(65.0)=='İyi'` instead.

## Known Issues

None.

## Files Created/Modified

- `src/services/camera/modelB4.py` — New: vendored LDC model definition with `from __future__ import annotations`
- `src/services/camera/health_calculator.py` — New: HealthCalculator class with calculate_saw_health, get_health_status, get_health_color
- `requirements.txt` — Added AI/Vision section with ultralytics, torch, torchvision
- `config/config.yaml` — Added ldc_checkpoint_path to camera.wear section
