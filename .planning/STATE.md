---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Camera Vision & AI Detection
status: Ready to plan
stopped_at: Phase 21 context gathered
last_updated: "2026-03-25T21:19:53.831Z"
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 2
  completed_plans: 2
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-16)

**Core value:** Endustriyel testere operasyonlarinin guvenilir kontrolu ve serit testere sagliginin yapay zeka ile surekli izlenmesi.
**Current focus:** Phase 20 — camera-capture

## Current Position

Phase: 21
Plan: Not started

## Performance Metrics

**Velocity:**

- Total plans completed: 19
- Average duration: 2 min
- Total execution time: ~37 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-ml-schema-update | 1 | 1 min | 1 min |
| 02-anomaly-schema-update | 1 | 1 min | 1 min |
| 03-data-population | 2 | 3 min | 1.5 min |
| 04-modbus-timeout | 1 | 2 min | 2 min |
| 05-ml-speed-restoration | 1 | 4 min | 4 min |
| 06-dynamic-chart-axis-labels | 1 | 3 min | 3 min |
| 07-mqtt-lock-free-queue | 1 | 2 min | 2 min |
| 08-vibration-dbscan-to-iqr | 1 | 1 min | 1 min |
| 09-anomaly-manager-lock-consolidation | 1 | 2 min | 2 min |
| 10-ai-mode-switch-fix | 1 | 3 min | 3 min |
| 11-initial-delay-logic | 1 | 1 min | 1 min |
| 12-ml-prediction-parity | 1 | 1 min | 1 min |
| 13-unit-labels-naming | 1 | 1 min | 1 min |
| 14-chart-axis-sapma-gauge | 1 | 2 min | 2 min |
| 15-touch-long-press-fix | 1 | 3 min | 3 min |
| 16-ml-db-none-values-investigation | 1 | 3 min | 3 min |
| 17-ml-db-schema-update | 1 | 2 min | 2 min |
| 18-anomaly-db-schema-update | 1 | 2 min | 2 min |

**Recent Trend:**

- Last 5 plans: 3 min, 3 min, 2 min, 2 min, 2 min
- Trend: Stable

| Phase 19-foundation P01 | 2 | 2 tasks | 6 files |
| Phase 20-camera-capture P01 | 4 | 3 tasks | 5 files |

## Accumulated Context

### Decisions

All decisions from v1.0-v1.6 milestones captured in PROJECT.md Key Decisions table.

Key v2.0 decisions established in research:

- opencv-python-headless (not full) — Qt5/Qt6 symbol conflict on Linux
- CameraResultsStore is sole integration boundary — GUI and IoT only touch the store
- Camera threads are daemon threads, never touch asyncio event loop
- Models loaded inside DetectionThread.run(), not in lifecycle startup
- Lazy imports behind camera.enabled guard in lifecycle.py and main_controller.py
- [Phase 19-foundation]: numpy upper bound removed (>=1.24.0 only) — downstream camera slices need numpy 2.x for ultralytics/torch
- [Phase 19-foundation]: camera.enabled defaults to false — zero behavioral change until hardware connected
- [Phase 19-foundation]: camera.db created by _init_camera() not _init_databases() — camera lifecycle isolated, no config.yaml database entry needed
- [Phase 19-foundation]: No camera module imports in lifecycle.py — lazy import pattern deferred to S22 to avoid ImportError when opencv not installed
- [Phase 20-camera-capture]: Auto-discovery scans 4 device IDs from config hint — industrial robustness for USB ID shifts
- [Phase 20-camera-capture]: 30-second retry on capture loss — transient USB disconnect must not crash main application
- [Phase 20-camera-capture]: fps_actual moving average via deque(maxlen=30) updated every 30 frames — low lock contention

### Blockers/Concerns

- Phase 21: LDC model source (modelB4.py) must be matched to eskiimas/smart-saw version exactly — wrong variant produces different wear values
- Phase 21: RT-DETR inference timing on panel PC CPU unknown — 2 Hz detection interval is estimate, measure during impl
- Phase 24: Sidebar 5th button geometry (y=649 projected) must be verified against actual .ui or main_controller.py layout

### Roadmap Evolution

- Milestone v1.0 COMPLETE: 2026-01-15
- Milestone v1.1 COMPLETE: 2026-01-15
- Milestone v1.2 COMPLETE: 2026-01-15
- Milestone v1.3 COMPLETE: 2026-01-15
- Milestone v1.4 COMPLETE: 2026-01-28
- Milestone v1.5 COMPLETE: 2026-01-28
- Milestone v1.6 COMPLETE: 2026-03-16
- Milestone v2.0 STARTED: 2026-03-16

## Session Continuity

Last session: 2026-03-25T21:19:53.825Z
Stopped at: Phase 21 context gathered
Resume file: .planning/phases/21-ai-detection-pipeline/21-CONTEXT.md
