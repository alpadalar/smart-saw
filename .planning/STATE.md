# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-29)

**Core value:** ML ve anomali kayitlarinda tork ve kafa yuksekligi verilerinin saklanmasi — gecmise donuk analiz icin kritik verinin eksik kalmamasi.
**Current focus:** v1.6 Touch UX & Data Traceability — planning Phase 15

## Current Position

Phase: 15 - Touch Long Press Fix
Plan: 1 of 1
Status: Phase complete
Last activity: 2026-01-29 — Completed 15-01-PLAN.md

Progress: [█-----------] 5.6% (Phase 15 of 18)

## Performance Metrics

**Velocity:**
- Total plans completed: 16
- Average duration: 2 min
- Total execution time: ~30 min

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

**Recent Trend:**
- Last 5 plans: 11-01 (1 min), 12-01 (1 min), 13-01 (1 min), 14-01 (2 min), 15-01 (3 min)
- Trend: Stable

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
All decisions from v1.0, v1.1, v1.2, v1.3, v1.4, and v1.5 milestones captured.

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
- GUI Labels: Only change visible label text, keep variable names unchanged (minimal code churn)
- BandDeviationGraph: New get_axis_max/get_axis_min methods to preserve existing get_max_value/get_min_value behavior

**v1.6 Decisions:**
- Touch activation: Instant (0ms delay) - industrial users expect immediate response
- Touch bounds: Strict, no tolerance zone - prevents accidental adjacent button activation
- Multi-touch: First button wins - prevents conflicting jog commands
- Emergency stop: Always responsive to any finger - safety feature must be accessible
- App focus loss: Stop jog on focusOutEvent - safety mechanism for backgrounded app

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
- Milestone v1.5 COMPLETE: 2026-01-28
- Milestone v1.6 created: Touch UX & data traceability, 4 phases (Phase 15-18)

## Session Continuity

Last session: 2026-01-29
Stopped at: Completed 15-01-PLAN.md (Touch Long Press Fix)
Resume file: None
