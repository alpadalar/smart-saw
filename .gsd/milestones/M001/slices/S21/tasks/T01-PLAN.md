---
estimated_steps: 5
estimated_files: 4
---

# T01: Vendor modelB4, build HealthCalculator, update deps and config

**Slice:** S21 — AI Detection Pipeline
**Milestone:** M001

## Description

Lay the foundation for S21 by vendoring the LDC model definition, building the HealthCalculator class, and declaring new dependencies. All three are pure logic / vendoring with no runtime dependencies on models or hardware — testable immediately.

## Steps

1. Copy `/media/workspace/eskiimas/smart-saw/src/vision/ldc/modelB4.py` to `src/services/camera/modelB4.py`. Add `from __future__ import annotations` as the first line (before all other imports). Keep the rest of the file exactly as-is — it's a pure PyTorch module definition (~240 lines, LDC class with CoFusion, DenseBlock, UpConvBlock etc). The `if __name__ == '__main__'` block can stay.

2. Create `src/services/camera/health_calculator.py` porting from old project's `saw_health_calculator.py`. The class should have:
   - Constants: `BROKEN_WEIGHT = 0.7`, `WEAR_WEIGHT = 0.3`
   - `calculate_broken_percentage(detected_teeth: int, detected_broken: int) -> float` — returns `(broken / teeth) * 100`, clamped to 0-100. Returns 0.0 if teeth <= 0.
   - `calculate_saw_health(detected_teeth: int, detected_broken: int, wear_percentage: float) -> float` — formula: `health = 100 - ((broken_pct/100 * BROKEN_WEIGHT + clamp(wear,0,100)/100 * WEAR_WEIGHT) * 100)`. Clamped to 0-100. On exception returns 100.0 (assume healthy).
   - `get_health_status(saw_health: float) -> str` — thresholds: >=80 "Sağlıklı", >=60 "İyi", >=40 "Orta", >=20 "Kritik", else "Tehlikeli"
   - `get_health_color(saw_health: float) -> str` — thresholds: >=80 "#00FF00", >=60 "#90EE90", >=40 "#FFFF00", >=20 "#FFA500", else "#FF0000"
   - Add `from __future__ import annotations` at top. Use `logging.getLogger(__name__)` for logger.

3. Add to `requirements.txt` (in a new "# AI / Vision" section after "# Computer Vision"):
   ```
   # AI / Vision
   ultralytics>=8.3.70
   torch>=2.6.0
   torchvision>=0.21.0
   ```

4. Add `ldc_checkpoint_path` to the camera wear section in `config/config.yaml`:
   ```yaml
   wear:
     enabled: true
     interval_seconds: 5.0
     ldc_checkpoint_path: "data/models/ldc/16_model.pth"
   ```

5. Verify: run the import and calculation tests specified in the slice verification.

## Must-Haves

- [ ] `modelB4.py` copied with `from __future__ import annotations` at top
- [ ] `HealthCalculator` class with correct formula matching old project exactly
- [ ] Health status thresholds: Sağlıklı/İyi/Orta/Kritik/Tehlikeli at 80/60/40/20
- [ ] Health color thresholds: #00FF00/#90EE90/#FFFF00/#FFA500/#FF0000 at 80/60/40/20
- [ ] `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0` in requirements.txt
- [ ] `ldc_checkpoint_path` in config camera.wear section

## Verification

- `python3 -c "from src.services.camera.modelB4 import LDC; print('modelB4 OK')"`
- `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); score=h.calculate_saw_health(100, 5, 20.0); assert 90 < score < 100, f'unexpected {score}'; print(f'score={score:.1f} OK')"`
- `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); assert h.get_health_status(85.0)=='Sağlıklı'; assert h.get_health_status(55.0)=='İyi'; assert h.get_health_status(35.0)=='Orta'; assert h.get_health_status(15.0)=='Tehlikeli'; assert h.get_health_color(85.0)=='#00FF00'; assert h.get_health_color(15.0)=='#FF0000'; print('status/color OK')"`
- `grep -q 'ultralytics' requirements.txt && grep -q 'torch>=' requirements.txt && grep -q 'torchvision' requirements.txt && echo 'requirements OK'`
- `grep -q 'ldc_checkpoint_path' config/config.yaml && echo 'config OK'`
- `python3 -c "from src.services.camera import CameraResultsStore; print('zero-import OK')"` — still works, no torch triggered

## Inputs

- `/media/workspace/eskiimas/smart-saw/src/vision/ldc/modelB4.py` — source LDC model definition to vendor
- `/media/workspace/eskiimas/smart-saw/src/core/saw_health_calculator.py` — reference for HealthCalculator formula, thresholds, colors
- `requirements.txt` — existing deps file to extend
- `config/config.yaml` — existing camera config to extend

## Expected Output

- `src/services/camera/modelB4.py` — vendored LDC model definition with `from __future__ import annotations`
- `src/services/camera/health_calculator.py` — HealthCalculator class with calculate_saw_health, get_health_status, get_health_color
- `requirements.txt` — includes ultralytics, torch, torchvision
- `config/config.yaml` — camera.wear section includes ldc_checkpoint_path
