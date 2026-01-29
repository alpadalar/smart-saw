# Feature Landscape: Touch Long Press & Data Traceability

**Domain:** Industrial touchscreen HMI with manufacturing data logging
**Researched:** 2026-01-29
**Context:** Smart Saw control system - adding touch long press fix and traceability fields to existing Qt PySide6 application

## Table Stakes

Features users expect. Missing = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Touch events work like mouse events | Industrial touchscreens are primary input method | Medium | Qt synthesizes mouse events from touch by default, but QPushButton pressed/released signals may not fire when parent has WA_AcceptTouchEvents set |
| Long press = continuous action while held | Standard behavior for positioning controls (jog buttons) | Medium | Requires handling TouchBegin → TouchUpdate → TouchEnd sequence manually or ensuring mouse event synthesis works |
| Touch release = action stops immediately | Safety requirement for industrial machinery | Low | Must reliably detect TouchEnd/MouseButtonRelease |
| Visual feedback during press | User needs confirmation that button is active | Low | QPushButton provides this via stylesheet `:pressed` state |
| Timestamp on all database records | Basic auditability requirement | Low | Already standard practice |
| User identification in logs | "Who did what" accountability | Low | Important for industrial environments with multiple operators |
| Machine/equipment identification | Multi-machine deployments need to distinguish data sources | Low | makine_id field standard in manufacturing systems |
| Material type tracking | Traceability requirement for manufacturing processes | Low | malzeme_cinsi (material type) needed for process optimization and quality control |
| Cut/operation identification | Link related events and measurements to specific operations | Low | kesim_id (cut ID) groups measurements from single cutting operation |
| Band/blade identification | Tool tracking for maintenance and quality correlation | Low | serit_id (band/blade ID) for consumable tracking |

## Differentiators

Features that improve usability but aren't strictly required for basic operation.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Configurable long press threshold | Adapt to operator preferences and safety requirements | Low | longPressThreshold in QML TapHandler, or QTimer interval in widgets |
| Haptic feedback on touch | Confirms action without looking at screen | High | Requires hardware support, may not be available on all industrial touchscreens |
| Multi-touch support | Simultaneous control of multiple parameters | Medium | Qt supports this via QTouchEvent, but adds UI complexity |
| Touch target size validation | Ensure buttons meet 44×44px (9mm) minimum for industrial gloves | Low | Important for industrial environments where operators may wear gloves |
| Visual progress indicator during hold | Shows time-to-action for long press gestures | Medium | Can render animation based on timeHeld property |
| Audit trail with before/after values | See what changed, not just that it changed | Medium | Capture old_value and new_value for modified fields |
| Geolocation/IP logging | Track where actions originated | Low | Useful for distributed systems or remote access scenarios |
| Success/failure status in logs | Distinguish attempted vs completed actions | Low | Helps diagnose system issues |
| Immutable/append-only audit storage | Prevent tampering with historical records | Medium | WORM (write-once-read-many) storage or cryptographic signatures |
| Correlation IDs across tables | Link ML predictions, anomalies, and raw data from same operation | Medium | kesim_id already serves this purpose |
| Retention policy automation | Auto-archive or purge old data per compliance requirements | Medium | Important for long-running systems with storage constraints |

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Right-click context menu on long press | Confuses industrial operators, interferes with hold-to-jog | Disable context menus on positioning buttons, or require explicit gesture |
| Relying solely on WA_AcceptTouchEvents on parent widget | Breaks QPushButton pressed/released signals, requires manual event handling | Set attribute only where needed, or manually emit signals from touch event handlers |
| Single global timestamp field | Insufficient granularity for traceability | Separate created_at, modified_at, deleted_at as needed |
| NULL-able traceability fields | Makes querying difficult, data incomplete | Use NOT NULL constraints with default values or require at initialization |
| Overly complex audit schema | Makes querying slow, storage expensive | Log what's required for compliance, aggregate rest |
| Logging sensitive data in plain text | Regulatory violations (GDPR, HIPAA if applicable) | Redact or hash sensitive fields, encrypt audit logs at rest |
| Synchronous database writes for every touch event | Floods database with TouchUpdate events, causes lag | Batch writes, log only meaningful state changes (press/release, not every update) |
| Storing redundant data in multiple tables | Data consistency issues, storage waste | Use foreign keys and normalization, join at query time |
| Fixed long press threshold | Too short = accidental activation, too long = frustrating | Make configurable, test with actual operators |
| Mouse-only testing | Touch behavior differs, bugs slip through | Test on actual industrial touchscreen hardware |

## Feature Dependencies

```
Touch Long Press Fix:
  Qt Touch Event Handling
    ├─→ WA_AcceptTouchEvents attribute management
    ├─→ Touch-to-mouse event synthesis understanding
    └─→ TouchBegin/TouchUpdate/TouchEnd sequence handling

  Continuous Action Logic
    ├─→ Pressed signal detection (touch or mouse)
    ├─→ Released signal detection (touch or mouse)
    └─→ Action loop during hold period

Traceability Fields:
  Database Schema Extension
    ├─→ ALTER TABLE for ml_predictions (kesim_id, makine_id, serit_id, malzeme_cinsi)
    ├─→ ALTER TABLE for anomaly_events (makine_id, serit_id, malzeme_cinsi)
    └─→ Schema version tracking

  Data Capture Integration
    ├─→ kesim_id from existing RawSensorData/ProcessedData
    ├─→ makine_id from system configuration
    ├─→ serit_id from system configuration or manual input
    └─→ malzeme_cinsi from system configuration or manual input
```

## MVP Recommendation

For v1.6 Touch UX & Data Traceability milestone, prioritize:

### Table Stakes (Must Have)
1. **Touch long press works like mouse long press** - Core functionality fix
   - Ensure QPushButton pressed/released signals fire correctly for touch events
   - Test on actual industrial touchscreen, not just mouse simulation
   - Verify immediate stop on touch release (safety requirement)

2. **Basic traceability fields** - Data completeness
   - Add kesim_id, makine_id, serit_id, malzeme_cinsi to ml_predictions table
   - Add makine_id, serit_id, malzeme_cinsi to anomaly_events table
   - Use ALTER TABLE to preserve existing data
   - Add NOT NULL constraints where appropriate

### Differentiators (Nice to Have)
3. **Audit trail enhancement** - If time permits
   - Log who made changes (if multi-user system)
   - Log success/failure status for operations
   - Consider before/after values for critical fields

### Defer to Post-MVP

- **Configurable long press threshold**: Current threshold likely sufficient, can adjust if operators report issues
- **Haptic feedback**: Requires hardware investigation, high effort for uncertain value
- **Multi-touch support**: Not needed for current single-button-at-a-time jog operations
- **Immutable audit storage**: Not required unless regulatory compliance demands it
- **Retention policy automation**: Premature optimization, handle when storage becomes concern

## Implementation Notes

### Touch Long Press: Qt-Specific Considerations

**The Core Problem:**
Qt widgets (QPushButton) rely on synthesized mouse events from touch input. When `Qt::WA_AcceptTouchEvents` is set on a parent widget, touch events are delivered as QTouchEvent (TouchBegin/TouchUpdate/TouchEnd) instead of synthesized mouse events, which breaks standard button signals (pressed/released).

**Solutions:**

1. **Don't set WA_AcceptTouchEvents on positioning button parent widgets** (Recommended)
   - Let Qt's default touch-to-mouse synthesis work
   - QPushButton pressed/released signals fire normally
   - Simplest approach, works with existing code

2. **Handle QTouchEvent manually if WA_AcceptTouchEvents is required**
   - Override event() or touchEvent() in parent widget
   - Map TouchBegin → MouseButtonPress, TouchEnd → MouseButtonRelease
   - Manually call button press/release handlers
   - More complex, only if multi-touch or other touch-specific features needed

3. **Use QML TapHandler instead of QPushButton** (Alternative)
   - TapHandler has built-in `longPressed` signal
   - `longPressThreshold` property controls duration
   - `timeHeld` property for progress animations
   - Requires QML migration, not practical for existing Qt Widgets codebase

**Recommended Approach for Smart Saw:**
Verify that positioning button parent widgets do NOT have `Qt::WA_AcceptTouchEvents` set. If touch events aren't working, the issue is likely elsewhere (driver configuration, Qt platform plugin, touch device not recognized).

**Testing Protocol:**
1. Test with actual industrial touchscreen hardware (not mouse simulation)
2. Verify pressed() signal fires on touch press
3. Verify released() signal fires on touch release
4. Test with gloved hands if operators wear gloves
5. Verify minimum touch target size (44×44px / 9mm)

### Traceability Fields: Industrial Standards

**Standard Field Categories:**

1. **Operation Identification**
   - `kesim_id` (cut ID): Links all data from a single cutting operation
   - PRIMARY: Correlation across ml_predictions, anomaly_events, raw_data

2. **Equipment Identification**
   - `makine_id` (machine ID): Which physical machine produced this data
   - REQUIRED: Multi-machine deployments, maintenance correlation
   - Source: System configuration file or hardware identifier

3. **Consumable Tracking**
   - `serit_id` (band/blade ID): Which blade was in use
   - IMPORTANT: Tool wear correlation, quality issues, maintenance scheduling
   - Source: Manual input or RFID if available

4. **Material Tracking**
   - `malzeme_cinsi` (material type): What was being cut
   - REQUIRED: Process optimization varies by material
   - Source: Manual input, barcode scan, or MES integration

**Data Types:**
- IDs: TEXT or INTEGER (TEXT preferred for flexibility with prefixes like "M001", "B042")
- Material type: TEXT (VARCHAR if using SQL with known material list)
- All should be NOT NULL for data quality (use "UNKNOWN" default if needed)

**Indexing Recommendations:**
```sql
-- Composite index for common query: "Show me all ML predictions for machine X, material Y"
CREATE INDEX idx_ml_machine_material ON ml_predictions(makine_id, malzeme_cinsi);

-- Composite index for anomaly analysis: "Anomalies for blade Z on machine X"
CREATE INDEX idx_anomaly_machine_blade ON anomaly_events(makine_id, serit_id);

-- kesim_id likely used for joins, ensure indexed
CREATE INDEX idx_ml_kesim ON ml_predictions(kesim_id);
CREATE INDEX idx_anomaly_kesim ON anomaly_events(kesim_id);
```

**Migration Strategy:**
```sql
-- Add columns with DEFAULT to avoid NULL in existing rows
ALTER TABLE ml_predictions ADD COLUMN kesim_id TEXT DEFAULT 'UNKNOWN';
ALTER TABLE ml_predictions ADD COLUMN makine_id TEXT DEFAULT 'M001';
ALTER TABLE ml_predictions ADD COLUMN serit_id TEXT DEFAULT 'UNKNOWN';
ALTER TABLE ml_predictions ADD COLUMN malzeme_cinsi TEXT DEFAULT 'UNKNOWN';

-- Remove DEFAULT after backfill if needed
-- ALTER TABLE ml_predictions ALTER COLUMN makine_id DROP DEFAULT;

-- Repeat for anomaly_events
ALTER TABLE anomaly_events ADD COLUMN makine_id TEXT DEFAULT 'M001';
ALTER TABLE anomaly_events ADD COLUMN serit_id TEXT DEFAULT 'UNKNOWN';
ALTER TABLE anomaly_events ADD COLUMN malzeme_cinsi TEXT DEFAULT 'UNKNOWN';
```

**Backward Compatibility:**
Existing rows get default values. New code should populate real values. Old code reading database sees new columns (may ignore them if SELECT * not used, or handle gracefully if using SELECT *).

## Sources

**Qt Touch Event Handling:**
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html)
- [TapHandler QML Type | Qt Quick | Qt 6.10.1](https://doc.qt.io/qt-6/qml-qtquick-taphandler.html)
- [How does Qt synthesize Mouse Events from Touch Events? | Qt Forum](https://forum.qt.io/topic/136576/how-does-qt-synthesize-mouse-events-from-touch-events)
- [Touchscreen QPushButton does not emit released() | Qt Forum](https://forum.qt.io/topic/151749/touchscreen-qpushbutton-does-not-emit-released)

**Industrial Touchscreen Best Practices:**
- [Touchscreen Software Guide 2026 | Interactive Display Solutions & Applications](https://touchwall.us/blog/touchscreen-software-complete-guide-2026/)
- [Designing for Touch: Mobile UI/UX Best Practices | by Devoq Design | Medium](https://devoq.medium.com/designing-for-touch-mobile-ui-ux-best-practices-c0c71aa615ee)
- [Jog Button on Touchscreen HMI in Perspective - Ignition - Inductive Automation Forum](https://forum.inductiveautomation.com/t/jog-button-on-touchscreen-hmi-in-perspective/87295)

**Manufacturing Traceability Standards:**
- [Traceability Requirements in Manufacturing: Best Practices for Compliance - TechnoMark](https://www.technomark-inc.com/best-practices-for-traceability-requirements/)
- [Traceability In Manufacturing: What Is It & How You Can… | Tulip](https://tulip.co/blog/traceability-in-manufacturing/)
- [What is Traceability? | Traceability Solutions | KEYENCE America](https://www.keyence.com/ss/products/marking/traceability/basic_about.jsp)

**Database Audit Trail Best Practices:**
- [Database Design for Audit Logging | Vertabelo Database Modeler](https://vertabelo.com/blog/database-design-for-audit-logging/)
- [Data Audit Trails: Best Practices for Security & Compliance](https://www.datasunrise.com/knowledge-center/data-audit-trails/)
- [Electronic Logbook (E-Logbook) for GMP Manufacturing](https://sgsystemsglobal.com/glossary/electronic-logbook-e-logbook/)
- [Audit Logging: Examples, Best Practices, and More](https://www.strongdm.com/blog/audit-logging)

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Qt touch event behavior | HIGH | Official Qt 6.10.1 documentation + recent forum discussions confirm WA_AcceptTouchEvents breaks QPushButton signals |
| Touch long press solutions | MEDIUM | Multiple approaches documented, but specific to Smart Saw codebase needs verification testing |
| Industrial touchscreen expectations | MEDIUM | General best practices found (44×44px targets, haptic feedback), but specific industrial HMI standards less detailed |
| Traceability field standards | HIGH | ISO 9001, GS1, industry-wide practices well documented for manufacturing data |
| Database audit trail design | HIGH | Well-established patterns (timestamp, user, before/after values) from 2026 sources |
| Smart Saw specific implementation | MEDIUM | Based on PROJECT.md context, but actual codebase not examined for this research |

## Gaps to Address

1. **Actual touch behavior in Smart Saw codebase**: Need to inspect whether any parent widgets have WA_AcceptTouchEvents set
2. **Current long press implementation**: How does mouse long press currently work? (QTimer? Button pressed/released signals?)
3. **Traceability data sources**: Where do kesim_id, makine_id, serit_id, malzeme_cinsi come from in the existing system?
4. **ML predictions None values**: Mentioned in PROJECT.md active requirements but not researched here (separate investigation)
5. **Touch hardware specifications**: What specific industrial touchscreen is being used? Capacitive or resistive? Multi-touch capable?

These gaps should be addressed during implementation planning or phase-specific research.
