# S13: Unit Labels Naming

**Goal:** Add units (mm/dk, m/dk, A, %) to numerical labels and rename "İnme Hızı" → "İlerleme Hızı" across all GUI pages.
**Demo:** Add units (mm/dk, m/dk, A, %) to numerical labels and rename "İnme Hızı" → "İlerleme Hızı" across all GUI pages.

## Must-Haves


## Tasks

- [x] **T01: 13-unit-labels-naming 01** `est:1min`
  - Add units (mm/dk, m/dk, A, %) to numerical labels and rename "İnme Hızı" → "İlerleme Hızı" across all GUI pages.

Purpose: Improve UX by showing units next to values and using consistent Turkish terminology (İlerleme = progression/advance, more appropriate than İnme = descent).
Output: Updated GUI labels with units and consistent naming.

## Files Likely Touched

- `src/gui/controllers/control_panel_controller.py`
- `src/gui/controllers/monitoring_controller.py`
