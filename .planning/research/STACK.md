# Technology Stack for Touch Long Press & Database Traceability

**Project:** Smart Saw Control System
**Milestone:** Touch event handling fix + database traceability fields
**Researched:** 2026-01-29
**Overall confidence:** HIGH

---

## Executive Summary

This research identifies the stack requirements for fixing touch long press handling on positioning page buttons and adding database traceability fields. The existing PySide6 stack is sufficient—**no new dependencies required**. The touch event issue stems from Qt's default touch-to-mouse event synthesis breaking down with multi-touch scenarios. The solution uses Qt's built-in event system without additional libraries.

**Key Finding:** Qt synthesizes mouse events from touch events by default, which works for single touches but fails when multiple buttons are touched simultaneously (common on industrial touchscreens). The `pressed()`/`released()` signals don't fire reliably with touch events.

---

## Core Stack (Already in Place)

### GUI Framework
| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| PySide6 | >=6.4.0 | Qt6 Python bindings | Already in requirements.txt |

**Why sufficient:** PySide6 includes all necessary Qt event handling classes:
- `QTouchEvent` - Touch event handling
- `QEvent` - Base event system
- `Qt.WA_AcceptTouchEvents` - Widget attribute for touch events
- Event filtering and override capabilities

### Database
| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| SQLite | Built-in | Five databases (raw, total, log, ml, anomaly) | Python stdlib |
| aiosqlite | >=0.19.0 | Async SQLite access | Already in requirements.txt |

**Why sufficient:** SQLite's `ALTER TABLE ADD COLUMN` supports adding fields to existing tables without data loss. Established patterns exist in `src/services/database/schemas.py`.

---

## What NOT to Add

### Touch Event Libraries ❌

**DO NOT add:**
- `pyqt-touch-scroll` - Not needed, Qt has built-in touch support
- `QtGestures` module separately - Already included in PySide6
- Third-party gesture libraries - Qt's gesture framework is built-in

**Why not:**
1. PySide6 already includes complete touch event infrastructure
2. The issue is implementation pattern, not missing functionality
3. Additional dependencies increase maintenance burden
4. Qt's built-in solution is industrial-grade and proven

### Migration Libraries ❌

**DO NOT add:**
- Alembic - Overkill for simple column additions
- Flask-Migrate - Flask-specific, not applicable
- Custom migration framework - Not worth complexity for 2-3 field additions

**Why not:**
1. SQLite `ALTER TABLE ADD COLUMN` is straightforward
2. Existing codebase uses direct SQL in `schemas.py`
3. Schema versioning not needed for this milestone
4. Keep it simple—match established patterns

---

## Touch Event Handling Stack

### Required Qt Classes (Built into PySide6)

| Class | Purpose | Import Path |
|-------|---------|-------------|
| `QEvent` | Base event class | `from PySide6.QtCore import QEvent` |
| `QTouchEvent` | Touch event container | `from PySide6.QtGui import QTouchEvent` |
| `Qt.WA_AcceptTouchEvents` | Widget attribute | `from PySide6.QtCore import Qt` |

### Touch Event Types

```python
from PySide6.QtCore import QEvent

QEvent.Type.TouchBegin    # Initial touch contact
QEvent.Type.TouchUpdate   # Touch point movement
QEvent.Type.TouchEnd      # Touch release
QEvent.Type.TouchCancel   # System gesture interruption
```

### Implementation Pattern

**Current implementation (positioning_controller.py):**
```python
# Lines 259-264: Mouse events only
self.btnMalzemeGeri.pressed.connect(...)
self.btnMalzemeGeri.released.connect(...)
```

**Problem:** Touch events don't trigger `pressed()`/`released()` signals reliably.

**Solution pattern:**
```python
# Override event() method to handle touch events directly
def event(self, event):
    if event.type() == QEvent.Type.TouchBegin:
        # Handle touch start
        point = event.points()[0]
        button = self._find_button_at_pos(point.position())
        if button:
            button.setDown(True)
            self._on_hold_button(button, command, True)
        return True

    elif event.type() == QEvent.Type.TouchEnd:
        # Handle touch release
        point = event.points()[0]
        button = self._find_button_at_pos(point.position())
        if button:
            button.setDown(False)
            self._on_hold_button(button, command, False)
        return True

    return super().event(event)
```

### Widget Configuration

Enable touch events on the positioning controller:
```python
def __init__(self, ...):
    super().__init__(parent)
    # Enable touch event reception
    self.setAttribute(Qt.WA_AcceptTouchEvents, True)
```

### Multi-Touch Considerations

**Industrial touchscreen reality:** Users may accidentally touch multiple buttons simultaneously. Qt's default mouse synthesis fails in this scenario.

**Design decision:** Handle each touch point independently:
- Map each `QEventPoint` to the button it's over
- Track press/release state per button
- Don't rely on Qt's mouse event synthesis

---

## Alternative: Qt Gesture Framework (Optional)

**DO NOT use for this milestone** — overkill for simple hold detection.

### When to Consider Gestures

If future milestones need:
- Pinch/zoom gestures
- Swipe navigation
- Complex multi-touch patterns

### Built-in Gesture Classes

| Class | Purpose | Default Timeout |
|-------|---------|-----------------|
| `QTapAndHoldGesture` | Long press detection | 700ms |
| `QPanGesture` | Drag/swipe | N/A |
| `QPinchGesture` | Zoom | N/A |

**Example (if needed later):**
```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGestureRecognizer

# In widget constructor:
self.grabGesture(Qt.GestureType.TapAndHoldGesture)

# In event handler:
def event(self, event):
    if event.type() == QEvent.Type.Gesture:
        gesture = event.gesture(Qt.GestureType.TapAndHoldGesture)
        if gesture.state() == Qt.GestureState.GestureFinished:
            # Long press detected
            pass
```

**Why NOT using for this milestone:**
- Existing code uses `pressed()`/`released()` pattern
- Simpler to fix at event level than refactor to gestures
- Gestures add complexity without benefit here
- Event override is more explicit and debuggable

---

## Database Traceability Stack

### Schema Modification Pattern (Established)

**Existing pattern in `src/services/database/schemas.py`:**
```python
# Lines 76-100: sensor_data table definition
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    kesim_id INTEGER,
    ...
)
```

**Migration pattern for adding columns:**
```python
# Option 1: ALTER TABLE (for existing databases)
ALTER TABLE sensor_data ADD COLUMN field_name TYPE DEFAULT value;

# Option 2: CREATE TABLE IF NOT EXISTS (for new installations)
# Update SCHEMA_TOTAL_DB constant to include new fields
```

### SQLite Column Addition Constraints

| Constraint | Allowed? | Notes |
|------------|----------|-------|
| `ADD COLUMN` | ✅ Yes | Always appended to end |
| `DEFAULT value` | ✅ Yes | Required if NOT NULL and table has rows |
| `NULL` | ✅ Yes | Default if not specified |
| `NOT NULL` | ⚠️ Conditional | Requires DEFAULT if table has rows |
| `PRIMARY KEY` | ❌ No | Cannot add via ALTER |
| `UNIQUE` | ❌ No | Cannot add via ALTER |
| `CURRENT_TIMESTAMP` | ❌ No | Cannot use as default in ALTER |

### Recommended Field Addition Pattern

```python
# For traceability fields (operator, reason, notes, etc.)
ALTER TABLE cutting_sessions ADD COLUMN operator_name TEXT DEFAULT NULL;
ALTER TABLE cutting_sessions ADD COLUMN stop_reason TEXT DEFAULT NULL;
ALTER TABLE cutting_sessions ADD COLUMN notes TEXT DEFAULT NULL;
ALTER TABLE cutting_sessions ADD COLUMN created_by TEXT DEFAULT 'system';
```

**Why this pattern:**
- `DEFAULT NULL` allows adding to existing tables
- Nullable fields don't break existing code
- Matches SQLite ALTER TABLE capabilities
- No migration framework needed

### Database Version Tracking (Optional)

**DO NOT add for this milestone** — 2-3 fields don't justify version tracking.

**When to add:**
- Breaking schema changes
- Multiple coordinated migrations
- Rollback requirements
- Multi-version production deployments

**Simple pattern (if needed later):**
```python
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);
```

---

## Integration with Existing Patterns

### Touch Event Integration Points

| File | Current Pattern | Touch Fix Location |
|------|-----------------|-------------------|
| `positioning_controller.py` | Mouse `pressed()`/`released()` signals | Override `event()` method |
| Lines 259-320 | Button signal connections | Add touch event handling |
| `_on_hold_button()` | Handler for press/release | Reuse with touch events |

**Key insight:** The existing `_on_hold_button()` method (lines 459-509) is touch-agnostic. It just needs to be called from touch events, not just mouse signals.

### Database Integration Points

| File | Current Pattern | Traceability Addition |
|------|-----------------|---------------------|
| `schemas.py` | CREATE TABLE definitions | Update schema constants |
| `src/services/database/` | Async SQLite access | Use existing aiosqlite patterns |
| `cutting_sessions` table | Lines 165-181 | Add traceability columns |

**Migration strategy:**
1. Add `ALTER TABLE` statements to schema initialization
2. Check if column exists before adding (avoid errors)
3. Use `PRAGMA table_info()` to detect existing columns

---

## Performance Considerations

### Touch Event Performance

**Industrial HMI requirement:** Touch response < 100ms perceived latency.

**Qt event system performance:**
- Touch events delivered at ~60-120Hz (touchscreen dependent)
- Event filtering adds ~1-2ms overhead
- Button hit-testing: O(n) where n = number of buttons
- For 6 buttons (positioning page): negligible

**Optimization NOT needed:**
- Spatial indexing of buttons
- Touch event throttling
- Asynchronous touch handling

**Why:** 6 buttons, simple geometry, industrial touchscreens are ~60Hz max.

### Database Performance

**Adding columns to SQLite:**
- `ALTER TABLE ADD COLUMN` is O(1) — metadata-only operation
- Does NOT rewrite table data
- Does NOT lock database for existing data
- Safe for production without downtime

**Schema check performance:**
```python
# PRAGMA table_info() performance: <1ms for typical tables
cursor.execute("PRAGMA table_info(cutting_sessions)")
columns = {row[1] for row in cursor.fetchall()}
if 'operator_name' not in columns:
    cursor.execute("ALTER TABLE cutting_sessions ADD COLUMN operator_name TEXT")
```

---

## Testing Stack Requirements

### Touch Event Testing

**Hardware needed:**
- Actual touchscreen device (industrial panel)
- Multi-touch capable screen (2+ simultaneous touches)

**Cannot test with:**
- Mouse simulation (different event path)
- Single-touch touchpad (doesn't expose multi-touch issue)

**Test scenarios:**
1. Single button press/release (should work)
2. Touch two buttons simultaneously (current bug)
3. Press button 1, then button 2 before releasing 1 (current bug)
4. Rapid touch sequences

### Database Testing

**Required:**
- Test database with existing data (raw, total, log, ml, anomaly)
- Migration script to add columns
- Verify NULL defaults don't break queries

**Test cases:**
1. Add columns to empty database
2. Add columns to populated database
3. Verify existing code handles NULL values
4. Verify new code writes to new columns

---

## Dependencies Summary

### No New Requirements

```txt
# Existing requirements.txt already contains everything needed:
PySide6>=6.4.0           # Touch events, gesture framework
aiosqlite>=0.19.0        # Async database access
# python-dotenv>=1.0.0   # Already there
```

### No System Dependencies

- Touch event handling: Pure Qt, no system libraries
- SQLite: Built into Python stdlib
- No OS-specific touch drivers needed (Qt abstracts this)

---

## Confidence Assessment

| Area | Confidence | Source | Rationale |
|------|------------|--------|-----------|
| Touch event classes | HIGH | Official Qt docs | PySide6.QtGui.QTouchEvent documented |
| Event override pattern | HIGH | Qt Forum, official examples | Common pattern, well-established |
| Multi-touch issue | HIGH | Qt Forum thread | Confirmed bug report with root cause |
| SQLite ALTER TABLE | HIGH | SQLite.org official docs | Standard SQL feature |
| No new dependencies | HIGH | PySide6 docs, existing code | All classes already available |
| Performance | MEDIUM | Qt performance docs | Theoretical, needs field validation |

---

## Known Limitations

### Touch Event Handling

1. **QTouchEvent API differences in Qt6:**
   - `touchPoints()` → `points()` (renamed in Qt6)
   - `pos()` → `position()` (renamed in Qt6)
   - Ensure PySide6 >= 6.4.0 uses Qt6 API

2. **Touch synthesized to mouse by default:**
   - Flag `Qt::AA_SynthesizeMouseForUnhandledTouchEvents` is ON by default
   - Can cause conflicts if both touch and mouse events handled
   - Solution: `event.accept()` to prevent mouse synthesis

3. **No gesture recognition needed:**
   - Current buttons are hold-to-activate (simple pattern)
   - Long press detection = measure time between TouchBegin and TouchEnd
   - Don't overcomplicate with QTapAndHoldGesture

### SQLite Schema Changes

1. **ALTER TABLE limitations:**
   - Cannot add PRIMARY KEY
   - Cannot add UNIQUE constraint
   - Cannot add computed columns
   - **Impact:** Traceability fields must be simple nullable columns

2. **No built-in migration tracking:**
   - Must manually check if column exists
   - `PRAGMA table_info()` query each time
   - **Impact:** Add defensive checks before ALTER TABLE

3. **Backward compatibility:**
   - Old code must handle NULL in new columns
   - New code must provide defaults
   - **Impact:** Test existing queries with new schema

---

## Architecture Implications

### Touch Event Handling Architecture

**Current:** Signals/slots with mouse events
```
Mouse Event → Qt Signal → Python slot → Machine control
```

**Proposed:** Event override with touch support
```
Touch Event → event() override → Find button → Python slot → Machine control
              ↓
Mouse Event → [same path] → Python slot → Machine control
```

**Design principle:** Don't break mouse events. Touch events should augment, not replace.

### Database Architecture

**Current:** Five separate SQLite databases
- `raw.db` - Raw Modbus registers
- `total.db` - Processed sensor data + cutting sessions
- `log.db` - System logs
- `ml.db` - ML predictions
- `anomaly.db` - Anomaly events + resets

**Traceability fields belong in:**
- `cutting_sessions` table (total.db)
- Possibly `system_logs` table (log.db) if operator actions logged

**Design principle:** Maintain separation of concerns. Don't merge databases.

---

## Migration Patterns from Existing Code

### Pattern 1: Schema Definition (schemas.py)

**Existing pattern (lines 165-181):**
```python
CREATE TABLE IF NOT EXISTS cutting_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_start TEXT NOT NULL,
    timestamp_end TEXT,
    ...
)
```

**For new fields:**
```python
# Update SCHEMA_TOTAL_DB constant
CREATE TABLE IF NOT EXISTS cutting_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_start TEXT NOT NULL,
    timestamp_end TEXT,
    ...
    -- NEW: Traceability fields
    operator_name TEXT,
    stop_reason TEXT,
    notes TEXT,
    created_by TEXT DEFAULT 'system'
)
```

### Pattern 2: Database Initialization

**Existing pattern:**
```python
async def initialize_database(db_path, schema):
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(schema)
        await db.commit()
```

**For migration:**
```python
async def migrate_database(db_path):
    async with aiosqlite.connect(db_path) as db:
        # Check existing columns
        cursor = await db.execute("PRAGMA table_info(cutting_sessions)")
        columns = {row[1] for row in await cursor.fetchall()}

        # Add missing columns
        if 'operator_name' not in columns:
            await db.execute(
                "ALTER TABLE cutting_sessions ADD COLUMN operator_name TEXT"
            )
        # ... repeat for other columns
        await db.commit()
```

---

## Recommendations

### For Touch Event Handling

1. **Enable touch events on PositioningController widget**
   - `setAttribute(Qt.WA_AcceptTouchEvents, True)` in `__init__`

2. **Override event() method**
   - Handle `QEvent.Type.TouchBegin`, `TouchUpdate`, `TouchEnd`
   - Map touch points to buttons using geometry
   - Call existing `_on_hold_button()` method

3. **Keep mouse event handling**
   - Don't remove `pressed.connect()` / `released.connect()`
   - Allow testing with mouse
   - Ensure `event.accept()` prevents double-triggering

4. **Test on actual touchscreen**
   - Virtual machines don't accurately simulate multi-touch
   - Test multi-touch scenarios specifically

### For Database Traceability

1. **Add columns to cutting_sessions table**
   - `operator_name TEXT` - Who performed the action
   - `stop_reason TEXT` - Why cutting stopped (if manual)
   - `notes TEXT` - Free-form operator notes
   - `created_by TEXT DEFAULT 'system'` - System vs manual entry

2. **Migration strategy**
   - Use `PRAGMA table_info()` to check existing schema
   - Add columns conditionally (idempotent)
   - Test on copy of production database first

3. **Update schema constant**
   - Modify `SCHEMA_TOTAL_DB` in `schemas.py`
   - New installations get new schema automatically
   - Existing installations use migration script

4. **Nullable vs. DEFAULT**
   - Use `DEFAULT NULL` for optional fields
   - Use `DEFAULT 'system'` for fields that should always have a value
   - Avoid `NOT NULL` without `DEFAULT` (breaks existing rows)

---

## Sources

### Qt Touch Event Documentation
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html) - Official Qt6 touch event documentation
- [PySide6.QtGui.QTouchEvent](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTouchEvent.html) - PySide6 Python bindings
- [Touchscreen QPushButton does not emit released() | Qt Forum](https://forum.qt.io/topic/151749/touchscreen-qpushbutton-does-not-emit-released) - Bug report and workaround
- [How does Qt synthesize Mouse Events from Touch Events? | Qt Forum](https://forum.qt.io/topic/136576/how-does-qt-synthesize-mouse-events-from-touch-events) - Mouse/touch synthesis explanation

### Qt Gesture Framework
- [Gestures in Widgets and Graphics View | Qt 6.10.1](https://doc.qt.io/qt-6/gestures-overview.html) - Gesture framework overview
- [QTapAndHoldGesture Class | Qt 6.10.1](https://doc.qt.io/qt-6/qtapandholdgesture.html) - Long press gesture class
- [QGestureRecognizer Class | Qt 6.10.1](https://doc.qt.io/qt-6/qgesturerecognizer.html) - Custom gesture recognizers

### Industrial HMI Best Practices
- [Built to Last: Five Best Practices for Building Reliable Industrial HMIs | Qt Blog](https://www.qt.io/blog/five-best-practices-for-building-reliable-hmi) - Qt industrial HMI guidelines (July 2025)
- [HMI development with the Qt framework - Integra Sources](https://www.integrasources.com/blog/embedded-qt-hmi-development-why-where-and-how/) - Industrial Qt development patterns

### SQLite Schema Management
- [ALTER TABLE | SQLite.org](https://sqlite.org/lang_altertable.html) - Official SQLite ALTER TABLE documentation
- [SQLite ALTER TABLE & How To Overcome Its Limitations](https://www.sqlitetutorial.net/sqlite-alter-table/) - Limitations and workarounds
- [Managing Database Versions and Migrations in SQLite](https://www.sqliteforum.com/p/managing-database-versions-and-migrations) - Migration patterns
- [SQLite ALTER TABLE ADD COLUMN IF NOT EXISTS: Workaround](https://www.w3tutorials.net/blog/alter-table-add-column-if-not-exists-in-sqlite/) - Conditional column addition

---

## Conclusion

**No new dependencies required.** PySide6 already includes all touch event handling infrastructure. SQLite supports column additions natively. The issue is implementation pattern, not missing functionality.

**Core changes needed:**
1. Enable touch events on PositioningController widget
2. Override `event()` to handle touch events directly
3. Map touch points to buttons and trigger existing handlers
4. Add database columns via `ALTER TABLE` with defensive checks

**Estimated complexity:**
- Touch event handling: LOW (50-100 lines of code)
- Database migration: LOW (10-20 lines of code + schema updates)

**Risk factors:**
- Must test on actual touchscreen (mouse doesn't reproduce issue)
- Database migration must be idempotent (run multiple times safely)
- Backward compatibility with existing data required
