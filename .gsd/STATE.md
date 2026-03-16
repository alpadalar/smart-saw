# GSD State

**Active Milestone:** M001: Migration
**Active Slice:** S24: Camera GUI
**Phase:** executing
**Requirements Status:** 23 active · 0 validated · 0 deferred · 0 out of scope

## Milestone Registry
- 🔄 **M001:** Migration

## Recent Decisions
- CameraController uses QImage.loadFromData() for JPEG decoding — no cv2 in GUI
- CameraController lazy-imported inside guard, not in __init__.py — zero-import preserved

## Blockers
- None

## Next Action
Execute T01: Build CameraController widget
