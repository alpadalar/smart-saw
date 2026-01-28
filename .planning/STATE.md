# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-28)

**Core value:** ML ve anomali kayitlarinda tork ve kafa yuksekligi verilerinin saklanmasi — gecmise donuk analiz icin kritik verinin eksik kalmamasi.
**Current focus:** ML prediction parity investigation — making new code behave identically to old code

## Current Position

Phase: 12 of 14 (ML Prediction Parity Investigation & Fix)
Plan: 1 of 1 in current phase
Status: Phase complete
Last activity: 2026-01-28 — Completed 12-01-PLAN.md

Progress: █████████░ 93%

## Performance Metrics

**Velocity:**
- Total plans completed: 13
- Average duration: 2 min
- Total execution time: ~24 min

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

**Recent Trend:**
- Last 5 plans: 08-01 (1 min), 09-01 (2 min), 10-01 (3 min), 11-01 (1 min), 12-01 (1 min)
- Trend: Stable

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
All decisions from v1.0, v1.1, v1.2, and v1.3 milestones captured.

**v1.3 Decisions:**
- MQTT: Lock-free asyncio.Queue kullanilacak (not threading queue)
- Vibration: IQR method'a gecis (DBSCAN O(n^2) -> IQR O(n))
- Config'deki method ayarlari (iqr, z_score, dbscan) calismaya devam edecek
- AnomalyManager: dict.update() ile atomic state update (9 lock -> 1 lock)

**v1.4 Decisions:**
- GUI->main thread async: asyncio.run_coroutine_threadsafe() kullanilacak
- Event loop propagation: Optional parameter ile backward compatibility korundu

**v1.5 Decisions:**
- ML Speed Calculation: Use averaged buffer values instead of raw current values (matches old code)
- Torque Conversion: No input clamping in torque_to_current() (matches old code polynomial behavior)

### Deferred Issues

None.

### Blockers/Concerns

None.

### Roadmap Evolution

- Milestone v1.0 created: Database schema updates, 3 phases (Phase 1-3)
- Milestone v1.0 COMPLETE: 2026-01-15
- Milestone v1.1 created: Modbus connection resilience, 1 phase (Phase 4)
- Milestone v1.1 COMPLETE: 2026-01-15
- Milestone v1.2 created: ML speed memory & chart UX, 2 phases (Phase 5-6)
- Milestone v1.2 COMPLETE: 2026-01-15
- Milestone v1.3 created: Processing performance, 3 phases (Phase 7-9)
- Milestone v1.3 COMPLETE: 2026-01-15
- Milestone v1.4 created: Control mode fixes, 2 phases (Phase 10-11)
- Milestone v1.4 COMPLETE: 2026-01-28
- Milestone v1.5 created: ML parity & UX polish, 3 phases (Phase 12-14)

## Session Continuity

Last session: 2026-01-28
Stopped at: Completed 12-01-PLAN.md (Phase 12 complete)
Resume file: None
