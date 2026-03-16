# GSD State

**Active Milestone:** M001: Migration
**Active Slice:** S21: AI Detection Pipeline
**Phase:** executing
**Requirements Status:** 23 active · 0 validated · 0 deferred · 0 out of scope

## Milestone Registry
- 🔄 **M001:** Migration

## Recent Decisions
- Both RT-DETR models consolidated into single DetectionWorker thread
- LDC model vendored as modelB4.py into src/services/camera/
- Workers import torch/ultralytics inside run() for zero-import guard
- HealthCalculator called from LDCWorker after each wear update
- No kornia dependency

## Blockers
- None

## Next Action
Execute T01 (vendor modelB4, build HealthCalculator, update deps and config).
