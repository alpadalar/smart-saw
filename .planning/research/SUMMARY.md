# Project Research Summary

**Project:** Smart Saw Control System v1.6
**Domain:** Industrial HMI touch event handling & database traceability
**Researched:** 2026-01-29
**Confidence:** HIGH

## Executive Summary

The v1.6 milestone addresses two distinct technical domains: fixing touch long-press functionality for positioning page buttons and adding database traceability fields to ML/anomaly databases. Research reveals that both can be accomplished using existing infrastructure—**no new dependencies required**.

The touch event issue stems from Qt's event synthesis system. Qt automatically converts touch events to mouse events, but this synthesis has timing delays (~1 second) and can fail when parent widgets accept touch events directly. The recommended approach is to implement explicit touch event handling at the widget level using PySide6's built-in `QTouchEvent` classes, bypassing the unreliable synthesis system. This requires overriding the `event()` method on positioning controller or creating custom `TouchButton` widgets that emit existing `pressed()`/`released()` signals from touch events.

The database traceability requirement is straightforward: add four fields (kesim_id, makine_id, serit_id, malzeme_cinsi) to ml_predictions and three fields (makine_id, serit_id, malzeme_cinsi) to anomaly_events tables. SQLite's `ALTER TABLE ADD COLUMN` handles this without data loss. The critical risk is Qt's touch event propagation breaking existing button functionality—if a parent widget accepts `TouchBegin`, child buttons won't receive synthesized mouse events. Testing on actual touchscreen hardware is mandatory, as mouse simulation doesn't expose multi-touch issues or synthesis failures.

## Key Findings

### Recommended Stack

**No new dependencies needed.** PySide6 (already in requirements.txt) includes complete touch event infrastructure. SQLite (Python stdlib) supports adding columns to existing tables without migration frameworks.

**Core technologies:**
- **PySide6 >=6.4.0**: Qt6 Python bindings with QTouchEvent, QEvent, touch event attributes — already installed
- **SQLite with ALTER TABLE**: Schema migration using PRAGMA user_version tracking — built into Python stdlib
- **aiosqlite >=0.19.0**: Async database access for schema migrations — already installed

**What NOT to add:**
- Touch event libraries (pyqt-touch-scroll) — Qt has built-in touch support
- Migration frameworks (Alembic, Flask-Migrate) — overkill for 2-3 column additions
- Gesture libraries — Qt gesture framework already included in PySide6

**Key stack decision:** Use Qt's built-in event system rather than external touch libraries. The issue is implementation pattern (how to handle events), not missing functionality. External libraries add maintenance burden without solving the core problem.

### Expected Features

**Must have (table stakes):**
- Touch long press works like mouse long press — Core functionality fix, safety requirement for industrial machinery
- Touch release stops action immediately — Safety requirement, must reliably detect TouchEnd
- Visual feedback during press — QPushButton provides via `:pressed` stylesheet state
- Traceability fields in all database records — kesim_id, makine_id, serit_id, malzeme_cinsi for audit compliance
- Timestamp and user identification in logs — Basic auditability for multi-operator environments

**Should have (competitive):**
- Configurable long press threshold — Use QStyleHints.mousePressAndHoldInterval() for platform-appropriate timing
- Touch target size validation — 44×44px (9mm) minimum for industrial gloves, current 120x62px buttons exceed this
- Audit trail with success/failure status — Helps diagnose system issues during debugging

**Defer (v2+):**
- Haptic feedback on touch — Requires hardware investigation, high effort for uncertain value
- Multi-touch support — Not needed for current single-button-at-a-time jog operations
- Immutable audit storage — Not required unless regulatory compliance demands it
- Retention policy automation — Handle when storage becomes a concern

**Anti-features (explicitly avoid):**
- Right-click context menu on long press — Confuses industrial operators, interferes with hold-to-jog pattern
- Relying solely on WA_AcceptTouchEvents on parent widget — Breaks QPushButton pressed/released signals
- Synchronous database writes for every touch event — Floods database with TouchUpdate events
- Fixed long press threshold — Use platform-appropriate value from QStyleHints

### Architecture Approach

Two independent architectural changes: touch event handling and database schema migration. No circular dependencies between them.

**Touch event integration:** Qt's default touch-to-mouse synthesis has ~1 second delay (OS-level behavior to distinguish taps from long-presses). Two options: (1) Application-level configuration using Qt.AA_SynthesizeMouseForUnhandledTouchEvents, or (2) Custom TouchButton widget that handles QTouchEvent directly and emits existing pressed/released signals. Option 2 recommended for low-latency industrial HMI. Integration point: positioning_controller.py buttons, reusing existing _on_hold_button() handler.

**Database migration architecture:** Current SQLiteService uses backup-and-recreate on schema errors (acceptable for ephemeral logs, not for ML/anomaly data). Add migration framework using PRAGMA user_version for tracking. Migrations defined in schemas.py, applied during database initialization. ALTER TABLE ADD COLUMN is O(1) metadata-only operation, safe for production without downtime.

**Major components:**
1. **TouchButton widget** (new) — Extends QPushButton, handles QTouchEvent, emits existing signals
2. **SQLiteService migration engine** (enhance) — Applies versioned migrations using PRAGMA user_version
3. **Schema migration definitions** (new) — MIGRATIONS_ML_DB and MIGRATIONS_ANOMALY_DB in schemas.py

### Critical Pitfalls

Research identified 10 pitfalls ranging from critical to minor. Top 5 critical/moderate pitfalls:

1. **Event Synthesis Blocking (Critical)** — Setting Qt.WA_AcceptTouchEvents on parent widget causes child buttons to stop receiving touch events entirely. Qt's touch-to-mouse synthesis only happens if touch events are NOT accepted by parent. Silent failure, works with mouse but not touch. **Prevention:** Accept touch only at specific widgets, call event.ignore() for unhandled touch, test all buttons with touch after implementation.

2. **Long Press → Right Click Conversion (Critical)** — Qt converts touchscreen long-press into right-button mouse event on some platforms (Windows). Context menus appear instead of intended action. **Prevention:** Handle touch events explicitly before they become mouse events, filter right-click events using QMouseEvent.source() to detect synthesis.

3. **TouchBegin Propagation Stops Future Events (Critical)** — If TouchBegin is ignored (not accepted), Qt sends NO TouchUpdate or TouchEnd events. Touch gesture never completes, widget stuck in "touch active" state. **Prevention:** Accept TouchBegin if you need TouchUpdate/TouchEnd, use TouchUpdate to validate gesture, always handle TouchEnd/TouchCancel for cleanup.

4. **Intermittent Touch Event Synthesis Failure (Moderate)** — Qt's mouse synthesis system has documented failures where it stops working after arbitrary runtime. Production HMI becomes unusable mid-shift. **Prevention:** Implement explicit touch handlers instead of relying on synthesis, add watchdog to detect synthesis failure and prompt restart.

5. **Event Loop Recursion with Touch Events (Moderate)** — Calling QDialog.exec() from touch event handler causes freezes/crashes due to multi-touch event delivery during nested event loop. **Prevention:** Use non-blocking dialogs (dialog.show()) or QTimer.singleShot(0, ...) to defer dialog opening until after event handling completes.

## Implications for Roadmap

Based on research, suggested phase structure with clear dependency ordering:

### Phase 1: Touch Event Infrastructure
**Rationale:** Independent of database changes, can be tested immediately. Foundation for remaining touch UX work.
**Delivers:** TouchButton widget or application-level touch configuration, touch event handling without synthesis delay
**Addresses:** Must-have table stakes feature (touch long press works like mouse)
**Avoids:** Pitfall #1 (synthesis blocking) by implementing explicit touch handlers
**Stack:** PySide6 QTouchEvent, QEvent.TouchBegin/TouchUpdate/TouchEnd
**Complexity:** MEDIUM — 50-100 lines of code, requires actual touchscreen for testing
**Research needs:** Standard Qt pattern, no additional research needed

### Phase 2: Database Migration Framework
**Rationale:** Foundation for schema changes, independent of touch events. Needed before adding traceability fields.
**Delivers:** Migration infrastructure in SQLiteService using PRAGMA user_version tracking
**Addresses:** Infrastructure for must-have traceability fields
**Avoids:** Data loss during schema updates, migration re-application errors
**Stack:** SQLite ALTER TABLE, PRAGMA user_version, Python shutil for backups
**Complexity:** LOW — 10-20 lines of migration engine code
**Research needs:** Standard database migration pattern, no additional research needed

### Phase 3: ML Database Traceability Fields
**Rationale:** Apply migration framework to ML database. Separate from anomaly DB to isolate risk.
**Delivers:** kesim_id, makine_id, serit_id, malzeme_cinsi fields in ml_predictions table
**Addresses:** Must-have traceability requirement for ML data audit compliance
**Uses:** Migration framework from Phase 2
**Stack:** ALTER TABLE ADD COLUMN, aiosqlite for async migration
**Complexity:** LOW — Schema definition + migration script
**Research needs:** May need investigation of ML DB None values (mentioned in PROJECT.md, not researched here)

### Phase 4: Anomaly Database Traceability Fields
**Rationale:** Same pattern as Phase 3, separate database to reduce scope per phase
**Delivers:** makine_id, serit_id, malzeme_cinsi fields in anomaly_events table
**Addresses:** Must-have traceability requirement for anomaly data audit compliance
**Uses:** Migration framework from Phase 2
**Stack:** ALTER TABLE ADD COLUMN
**Complexity:** LOW — Repeat Phase 3 pattern for anomaly database
**Research needs:** Standard pattern, no additional research needed

### Phase 5: Integration & Verification
**Rationale:** Validate all changes work together, test on production-like environment with actual hardware
**Delivers:** End-to-end testing on industrial touchscreen, 8+ hour stability test
**Addresses:** Must-have safety requirements (touch release stops immediately)
**Avoids:** Pitfall #7 (intermittent synthesis failure), Pitfall #3 (right-click conversion on Windows)
**Testing:** Requires physical touchscreen device, multi-touch scenarios, glove testing if applicable
**Research needs:** No additional research, focus on verification testing

### Phase Ordering Rationale

**Why touch first:** Touch infrastructure is independent and can be tested immediately. Provides immediate value (fixes broken button functionality). Database work has no touch dependencies.

**Why migration framework before schema changes:** Prevents data loss. Allows incremental migrations (ML first, then anomaly). Provides rollback capability via backups.

**Why separate ML and anomaly phases:** Isolates risk—if ML migration has issues, anomaly DB unaffected. Allows testing each database migration independently. Each phase is smaller and less risky.

**Why integration last:** Can't validate touch + database interaction until both implemented. Needs actual hardware that may not be available during early development. Long-running stability tests (8+ hours) require working system.

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3 (ML Database):** May need investigation of ML DB None values mentioned in PROJECT.md active requirements ("ML DB None değerler araştırma"). This wasn't researched here and may affect schema decisions.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Touch Events):** Well-documented Qt pattern, official Qt 6.10.1 documentation covers all needed classes
- **Phase 2 (Migration Framework):** Industry-standard SQLite migration pattern using PRAGMA user_version
- **Phase 4 (Anomaly Database):** Repeat of Phase 3 pattern
- **Phase 5 (Integration):** Verification testing, no research needed

**Additional research considerations:**
- Touch hardware specifications: Capacitive vs resistive touchscreen affects glove compatibility (research during Phase 1 hardware testing)
- SQLite version in production: Assumed 3.35+ for modern features, verify during Phase 2 setup
- Glove testing requirements: If operators wear protective gloves, research palm rejection and pressure sensitivity during Phase 5

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official Qt 6.10.1 docs + PySide6 docs confirm all needed classes present. SQLite ALTER TABLE documented in official SQLite.org docs. |
| Features | HIGH | Industrial HMI best practices well-documented. Traceability requirements match ISO 9001/GS1 manufacturing standards. |
| Architecture | HIGH | Qt event system architecture verified with official docs. SQLite migration patterns are industry-standard. Multiple community sources corroborate findings. |
| Pitfalls | HIGH | 10 pitfalls verified with official Qt docs and multiple Qt Forum discussions. Touch synthesis issues confirmed by community bug reports. |

**Overall confidence:** HIGH

All critical architectural patterns verified with official documentation. Community-reported issues (touch delay, synthesis failures) corroborated by multiple independent sources. Migration patterns match industry best practices.

### Gaps to Address

**Touch event timing precision:** Community reports vary (0.8s - 4s delay for touch-to-mouse synthesis). Actual delay depends on OS, drivers, hardware. **Action:** Measure during Phase 1 testing on production touchscreen hardware.

**Multi-touch button conflicts:** Documentation says multiple buttons can receive touch simultaneously, unclear if this causes issues with hold-to-activate pattern. **Action:** Test during Phase 5 with intentional multi-touch scenarios (palm rejection testing).

**SQLite version verification:** Research assumes SQLite 3.35+ (2021) for modern ALTER TABLE features. **Action:** Check production environment during Phase 2 migration framework setup.

**ML DB None values investigation:** Mentioned in PROJECT.md as separate active requirement, not researched here. May affect schema design or migration strategy. **Action:** Research during Phase 3 planning if None values impact traceability field decisions.

**Glove compatibility:** Industrial environments may require protective gloves. Capacitive touchscreens may not work with gloves. **Action:** Research touchscreen hardware type and test with operator gloves during Phase 5.

**Traceability data sources:** Where do kesim_id, makine_id, serit_id, malzeme_cinsi values come from in existing system? Manual input, configuration file, RFID, barcode? **Action:** Identify data sources during Phase 3/4 implementation to populate new fields correctly.

## Sources

### Primary (HIGH confidence)
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html) — Official Qt6 touch event documentation, event types, propagation rules
- [PySide6.QtGui.QTouchEvent](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTouchEvent.html) — Official PySide6 Python bindings for touch events
- [ALTER TABLE | SQLite.org](https://sqlite.org/lang_altertable.html) — Official SQLite ALTER TABLE documentation, supported operations
- [Managing Database Versions and Migrations in SQLite](https://www.sqliteforum.com/p/managing-database-versions-and-migrations) — Official SQLite forum migration patterns

### Secondary (MEDIUM confidence)
- [How does Qt synthesize Mouse Events from Touch Events? | Qt Forum](https://forum.qt.io/topic/136576/how-does-qt-synthesize-mouse-events-from-touch-events) — Community explanation of synthesis mechanism
- [Touchscreen QPushButton does not emit released() | Qt Forum](https://forum.qt.io/topic/151749/touchscreen-qpushbutton-does-not-emit-released) — Bug report confirming pressed/released signal issues with touch
- [QT Widgets not responding to touch event sometimes](https://forum.qt.io/topic/96780/qt-widgets-not-responding-to-touch-event-sometimes) — Intermittent synthesis failure reports
- [Simple declarative schema migration for SQLite](https://david.rothlis.net/declarative-schema-migration-for-sqlite/) — Industry migration pattern

### Tertiary (context and validation)
- [Built to Last: Five Best Practices for Building Reliable Industrial HMIs | Qt Blog](https://www.qt.io/blog/five-best-practices-for-building-reliable-hmi) — Industrial HMI guidelines (July 2025)
- [Traceability In Manufacturing: What Is It & How You Can… | Tulip](https://tulip.co/blog/traceability-in-manufacturing/) — Manufacturing traceability standards
- [Jog Button on Touchscreen HMI in Perspective - Ignition Forum](https://forum.inductiveautomation.com/t/jog-button-on-touchscreen-hmi-in-perspective/87295) — Industrial HMI touch button patterns

---
*Research completed: 2026-01-29*
*Ready for roadmap: yes*
