# Touch Event Handling Pitfalls

**Domain:** Adding touch long-press to Qt/PySide6 industrial HMI with existing mouse handling
**Researched:** 2026-01-29
**Confidence:** HIGH (verified with official Qt documentation and community reports)

## Executive Summary

Adding touch event support to an existing Qt/PySide6 application with working mouse events is **architecturally treacherous**. Qt's event synthesis system creates subtle interactions between touch and mouse events that can break existing functionality. The industrial HMI context (fullscreen, single-interaction point) reduces multi-touch complexity but amplifies the impact of synthesis failures.

**Key insight:** Touch events have precedence over mouse events in Qt's delivery system. If a parent widget accepts a touch event, child widgets relying on mouse synthesis will not receive mouse events.

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Event Synthesis Blocking - The Parent/Child Trap

**What goes wrong:**
You add `setAttribute(Qt.WA_AcceptTouchEvents)` to a parent widget to handle touch long-press. Existing mouse-based child widgets (buttons, controls) suddenly stop responding to touch input entirely. Users can't press buttons with touch, only with mouse.

**Why it happens:**
Qt's event delivery is: Touch event propagates → if accepted, **stop** → if ignored, synthesize mouse event. When a parent widget accepts `QEvent.TouchBegin`, Qt stops propagation and **never synthesizes the mouse event** that child widgets expect.

**Consequences:**
- Buttons/controls become non-functional on touchscreen
- Works perfectly with mouse, fails completely with touch
- No error messages - silent failure
- Hard to debug because mouse testing shows everything working

**Prevention:**
1. **Never accept touch events at parent level** unless you handle all child interactions in touch handlers
2. If parent needs touch events, explicitly call `event.ignore()` for touch events you don't handle
3. Use event filters instead of accepting touch events at parent level
4. Test with `QTouchDevice` simulation, not just mouse

**Detection:**
- Buttons work with mouse but not touch
- Check if any ancestor widget has `WA_AcceptTouchEvents` set
- Add logging to `event()` override: log when `TouchBegin` is accepted

**Code smell:**
```python
# BAD - Parent accepts touch, blocks mouse synthesis for children
class ParentWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_AcceptTouchEvents)  # Blocks children!

    def event(self, event):
        if event.type() == QEvent.TouchBegin:
            # Handle touch...
            return True  # PROBLEM: Children won't get mouse events
```

**Fix pattern:**
```python
# GOOD - Parent only handles specific touch, ignores others
class ParentWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_AcceptTouchEvents)

    def event(self, event):
        if event.type() == QEvent.TouchBegin:
            # Check if this is for a specific child/region
            if self._should_handle_long_press(event):
                # Handle long press...
                return True
            else:
                event.ignore()  # Let it propagate for mouse synthesis
                return False
        return super().event(event)
```

**Phase impact:** Phase 14-01 (Touch Event Implementation) must verify button functionality doesn't regress.

**Sources:**
- [How does Qt synthesize Mouse Events from Touch Events?](https://forum.qt.io/topic/136576/how-does-qt-synthesize-mouse-events-from-touch-events)
- [Touch event synthesis conflicts](https://groups.google.com/g/qt-project-list-development/c/J8G9KkFVkCM/m/iim6Ts4itiwJ)
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html)

---

### Pitfall 2: Viewport Attribute Blindness

**What goes wrong:**
You set `setAttribute(Qt.WA_AcceptTouchEvents)` on a scroll area or container widget. Touch events never arrive. No errors, no warnings - just silence.

**Why it happens:**
For `QAbstractScrollArea`-based widgets (scroll areas, text edits, list views), the touch event attribute **must be set on the viewport**, not the widget itself. The viewport is the internal child widget that actually receives events.

**Consequences:**
- Touch events silently ignored
- Developers assume touch doesn't work and give up
- Mouse works fine, masking the problem during mouse-based testing

**Prevention:**
```python
# For ANY QAbstractScrollArea-based widget:
scroll_area.viewport().setAttribute(Qt.WA_AcceptTouchEvents)  # viewport!
# NOT: scroll_area.setAttribute(Qt.WA_AcceptTouchEvents)  # Wrong target
```

**Detection:**
- Touch events never trigger `event()` callback
- Widget inherits from `QAbstractScrollArea` (or `QTextEdit`, `QListView`, etc.)
- Check where attribute is set: widget or viewport?

**Phase impact:** Phase 14-01 must audit all widgets - any scroll areas need viewport attribute.

**Sources:**
- [QTouchEvent Class | Qt GUI 5.7](https://stuff.mit.edu/afs/athena/software/texmaker_v5.0.2/qt57/doc/qtgui/qtouchevent.html)
- [QGraphicsView and Qt::WA_AcceptTouchEvents](https://forum.qt.io/topic/150098/qgraphicsview-and-qt-wa_accepttouchevents)

---

### Pitfall 3: Long Press → Right Click Conversion

**What goes wrong:**
User performs touch long-press. Your handler never fires. Instead, Qt fires a **right-click mouse event** (`QMouseEvent` with `Qt.RightButton`). Context menus appear unexpectedly, or handlers receive wrong event type.

**Why it happens:**
Qt automatically converts touchscreen hold (long press) into a right-button press in some configurations, particularly on Windows. This is a platform-level behavior that bypasses your touch handlers.

**Consequences:**
- Context menus appear on long press instead of intended action
- Long-press handlers never trigger
- Different behavior on different platforms (Windows vs Linux)
- User confusion: "Why does holding show a menu?"

**Prevention:**
1. **Handle touch events explicitly** before they become mouse events
2. Set `Qt.AA_SynthesizeMouseForUnhandledTouchEvents = False` if you handle all touch yourself
3. Filter right-click events in mouse handlers when touch is active
4. Use `QMouseEvent.source()` or `pointingDevice()` to detect if event was synthesized from touch

**Detection:**
- Right-click menus appear on touch long-press
- Log event sources: `event.source() == Qt.MouseEventSynthesizedBySystem`
- Test on actual touchscreen hardware (not mouse simulation)

**Code pattern:**
```python
def mousePressEvent(self, event):
    # Detect synthesized touch-to-mouse conversion
    if event.source() == Qt.MouseEventSynthesizedBySystem:
        if event.button() == Qt.RightButton:
            # This is touch long-press → right-click conversion
            # Either ignore or handle as touch long-press
            event.ignore()
            return
    # Normal mouse handling
    super().mousePressEvent(event)
```

**Phase impact:** Phase 14-01 must test on Windows touchscreen hardware, not just Linux development machine.

**Sources:**
- [Touchscreen "HOLD" (long-press) event gets converted to a right-mouse-button press](https://forum.qt.io/topic/157910/touchscreen-hold-long-press-event-gets-converted-to-a-right-mouse-button-press)
- [Long press from touch screen is handled different from long mouse press](https://forum.qt.io/topic/111658/long-press-from-touch-screen-is-handled-different-from-long-mouse-press)

---

### Pitfall 4: TouchBegin Propagation Stops All Future Touch Events

**What goes wrong:**
You call `event.ignore()` on `TouchBegin` thinking it will propagate like mouse events. Instead, **all future touch events stop** - no `TouchUpdate`, no `TouchEnd`. The touch sequence is dead.

**Why it happens:**
Qt touch event propagation rules are different from mouse:
- `TouchBegin` propagates up the parent chain until accepted or filtered
- If `TouchBegin` is **not accepted and not filtered**, Qt sends **no further touch events** for that sequence
- Only the widget that accepted `TouchBegin` receives `TouchUpdate` and `TouchEnd`

**Consequences:**
- Touch gesture never completes
- No `TouchEnd` event to clean up state
- Widget stuck in "touch active" state
- Memory leaks if you allocated resources expecting `TouchEnd`

**Prevention:**
1. **Accept `TouchBegin`** if you might want `TouchUpdate`/`TouchEnd` - even if you're not sure yet
2. Use `TouchUpdate` to decide if gesture is valid, not `TouchBegin`
3. Always handle `TouchEnd` and `TouchCancel` for cleanup
4. Don't use `event.ignore()` pattern from mouse event handling

**Detection:**
- `TouchUpdate` and `TouchEnd` never fire after `TouchBegin`
- Add logging: count TouchBegin vs TouchEnd - should be equal
- Check for resource leaks (timers, allocated objects)

**Code pattern:**
```python
def event(self, event):
    if event.type() == QEvent.TouchBegin:
        # MUST accept to get future events
        self.touch_start_pos = event.touchPoints()[0].startPos()
        self.touch_timer.start()
        event.accept()  # Critical!
        return True

    elif event.type() == QEvent.TouchUpdate:
        # Now we can check if gesture is valid
        if self._is_long_press_gesture(event):
            # Continue
            event.accept()
            return True
        else:
            # Cancel our handling, but event sequence continues
            self.touch_timer.stop()
            event.ignore()
            return False

    elif event.type() in (QEvent.TouchEnd, QEvent.TouchCancel):
        # Always handle cleanup
        self.touch_timer.stop()
        event.accept()
        return True

    return super().event(event)
```

**Phase impact:** Phase 14-01 must implement full TouchBegin/Update/End cycle, not just TouchBegin.

**Sources:**
- [QTouchEvent Class | Qt 4.8](https://doc.qt.io/archives/qt-4.8/qtouchevent.html)
- [Touch event accept ignore event propagation](https://stuff.mit.edu/afs/athena/software/texmaker_v5.0.2/qt57/doc/qtgui/qtouchevent.html)
- [The 'Accepted' Flag: Understanding QEvent::accept() and ignore() in Qt](https://runebook.dev/en/docs/qt/qevent/accept)

---

## Moderate Pitfalls

Mistakes that cause delays or technical debt.

### Pitfall 5: Event Loop Recursion with Touch Events

**What goes wrong:**
You call `QDialog.exec()` or `QMenu.exec()` from within a touch event handler (e.g., show numpad on long-press). Application freezes, crashes, or exhibits undefined behavior.

**Why it happens:**
Touch events can have multiple active recipients simultaneously (multi-touch). Recursing into the event loop (via `exec()`) while touch events are active causes undefined behavior - events may be lost, delivered to wrong widgets, or cause infinite recursion.

**Consequences:**
- Application hangs or crashes
- Touch events delivered to wrong widgets after dialog closes
- Unpredictable behavior (works sometimes, fails others)

**Prevention:**
1. **Use non-blocking dialogs**: `dialog.show()` instead of `dialog.exec()`
2. Use `QTimer.singleShot(0, ...)` to defer dialog opening until after event handling completes
3. If you must use `exec()`, ensure touch event is fully completed (`TouchEnd` processed)

**Detection:**
- Crashes when showing dialogs from touch handlers
- `exec()` called from `TouchBegin` or `TouchUpdate` handler
- Inconsistent dialog behavior between mouse and touch

**Code pattern:**
```python
# BAD
def event(self, event):
    if event.type() == QEvent.TouchBegin:
        # This can cause recursion
        dialog = NumpadDialog(self)
        result = dialog.exec()  # Blocks event loop - DANGER
        return True

# GOOD
def event(self, event):
    if event.type() == QEvent.TouchBegin:
        # Defer dialog opening
        QTimer.singleShot(0, self._show_numpad_dialog)
        event.accept()
        return True

def _show_numpad_dialog(self):
    dialog = NumpadDialog(self)
    dialog.exec()  # Safe - no active touch events
```

**Phase impact:** Phase 14-01 - Numpad dialogs on long-press must be deferred.

**Sources:**
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html)
- [Mastering Touch Events in Qt: From Rookie Mistakes to Pro Techniques](https://runebook.dev/en/docs/qt/qtouchevent/QTouchEvent)

---

### Pitfall 6: Mouse Grab and Pop-up Interactions

**What goes wrong:**
User initiates touch interaction. While touch is active, a pop-up appears or mouse is grabbed by another widget. Touch events continue to original widget, mouse events go to pop-up - undefined behavior.

**Why it happens:**
`QTouchEvent` is **not affected** by mouse grabs or active pop-ups. Touch events continue to their original recipient even when modal dialogs or pop-ups should be capturing input.

**Consequences:**
- Widgets receive touch input when they shouldn't (e.g., behind modal dialog)
- State corruption - widget thinks it's being interacted with when dialog is open
- Race conditions between touch and modal UI

**Prevention:**
1. **Track modal state** - ignore touch events when modals are active
2. Call `event.ignore()` for touch events when dialogs/menus are open
3. Clear touch state when showing modal dialogs

**Detection:**
- Touch events fire on background widgets when dialog is open
- Unexpected state changes when modals are active
- Check `QApplication.activeModalWidget()` during touch events

**Code pattern:**
```python
def event(self, event):
    if event.type() in (QEvent.TouchBegin, QEvent.TouchUpdate):
        # Check if modal dialog is active
        if QApplication.activeModalWidget() is not None:
            event.ignore()
            return False
        # Normal handling
        return self._handle_touch(event)
    return super().event(event)
```

**Phase impact:** Phase 14-01 must handle modal numpad dialog interactions.

**Sources:**
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html)

---

### Pitfall 7: Intermittent Touch Event Synthesis Failure

**What goes wrong:**
Application works fine with touch for minutes/hours/days, then suddenly touch stops working. Mouse events are no longer synthesized from touch. Only app restart fixes it. Other applications continue working fine.

**Why it happens:**
Qt's mouse event synthesis system has documented intermittent failures where it stops synthesizing mouse events after arbitrary running time. Root cause is unclear - appears to be Qt internal state corruption.

**Consequences:**
- Production HMI becomes unusable mid-shift
- No error messages or warnings
- Difficult to reproduce (timing-dependent)
- User loses trust in system reliability

**Prevention:**
1. **Don't rely on mouse synthesis** - implement explicit touch handlers
2. Implement watchdog: detect when touch stops working, log error, prompt restart
3. Set `Qt.AA_SynthesizeMouseForUnhandledTouchEvents = True` explicitly
4. Consider implementing input event monitor to detect synthesis failures

**Detection:**
- Touch works, then stops after random time
- Mouse still works (if available)
- Check Qt version - may be version-specific bug
- Monitor for `TouchEvent` → `MouseEvent` ratio changes

**Mitigation (runtime):**
```python
class TouchWatchdog:
    def __init__(self):
        self.last_touch_event = None
        self.last_mouse_event = None
        self.synthesis_failure_detected = False

    def check_synthesis(self, touch_event, mouse_event):
        # If touch events happen but no mouse events synthesized
        if self.last_touch_event and not mouse_event:
            if (datetime.now() - self.last_touch_event).seconds > 5:
                logger.error("Touch synthesis failure detected!")
                self.synthesis_failure_detected = True
                # Alert user to restart
```

**Phase impact:** Phase 14-02 (Verification & Documentation) should include synthesis failure detection.

**Sources:**
- [QT Widgets not responding to touch event sometimes](https://forum.qt.io/topic/96780/qt-widgets-not-responding-to-touch-event-sometimes)
- [Cannot receive mouse event when using touch panel](https://forum.qt.io/topic/134410/cannot-receive-mouse-event-when-using-touch-panel)

---

### Pitfall 8: Long Press Timer Inconsistency

**What goes wrong:**
You implement custom long-press timer (e.g., 800ms). Behavior feels wrong - sometimes too fast, sometimes too slow. Users complain "it doesn't match other apps."

**Why it happens:**
Qt provides `QStyleHints.mousePressAndHoldInterval()` which returns the **platform-appropriate** long-press threshold. Using hardcoded values ignores platform conventions and accessibility settings.

**Consequences:**
- Inconsistent with platform UX expectations
- Breaks accessibility (users who need longer press time)
- Different behavior on Windows vs Linux vs embedded

**Prevention:**
```python
from PySide6.QtGui import QGuiApplication

# Get platform-appropriate threshold
style_hints = QGuiApplication.styleHints()
long_press_threshold_ms = style_hints.mousePressAndHoldInterval()

# Use this value for touch long-press timer
self.long_press_timer.setInterval(long_press_threshold_ms)
```

**Detection:**
- Hardcoded timer values (500, 800, 1000) in code
- User complaints about timing
- Different feel from platform apps

**Phase impact:** Phase 14-01 must use `QStyleHints.mousePressAndHoldInterval()`.

**Sources:**
- [MouseArea QML Type | Qt Quick | Qt 6.10.2](https://doc.qt.io/qt-6/qml-qtquick-mousearea.html)
- [TapHandler QML Type | Qt Quick | Qt 6.10.1](https://doc.qt.io/qt-6/qml-qtquick-taphandler.html)
- [QStyleHints (class) - Qt 5.11 Documentation](https://www.typeerror.org/docs/qt~5.11/qstylehints)

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

### Pitfall 9: Touch Point Movement Threshold Ignored

**What goes wrong:**
You implement long-press detection. User touches screen, finger drifts slightly (normal human behavior), long-press cancels unexpectedly.

**Why it happens:**
Humans can't hold finger perfectly still. Touch long-press requires movement threshold - typically 5-10 pixels of drift is acceptable.

**Consequences:**
- Long-press feels unreliable
- Users think they're doing it wrong
- Frustration with touch UI

**Prevention:**
```python
TOUCH_MOVE_THRESHOLD = 10  # pixels

def event(self, event):
    if event.type() == QEvent.TouchBegin:
        self.touch_start_pos = event.touchPoints()[0].startPos()
        self.long_press_timer.start()

    elif event.type() == QEvent.TouchUpdate:
        current_pos = event.touchPoints()[0].pos()
        distance = (current_pos - self.touch_start_pos).manhattanLength()

        if distance > TOUCH_MOVE_THRESHOLD:
            # Moved too much - cancel long press
            self.long_press_timer.stop()
```

**Detection:**
- Users report long-press "doesn't work"
- Watch finger movement during testing - even "still" touch moves 2-5 pixels
- No movement threshold in code

**Phase impact:** Phase 14-01 must implement movement threshold.

---

### Pitfall 10: Multiple Simultaneous Touch Points

**What goes wrong:**
User accidentally rests palm on screen while pressing button. Extra touch point is grouped with original, causing unexpected behavior.

**Why it happens:**
Qt groups new touch points with active ones if they're on the same widget or ancestor/descendant. All points sent in single `QTouchEvent`.

**Consequences:**
- Unexpected multi-touch handling when only single touch intended
- Palm rejection failures
- Position calculated from wrong touch point

**Prevention:**
```python
def event(self, event):
    if event.type() == QEvent.TouchBegin:
        touch_points = event.touchPoints()

        # Handle only first/primary touch point
        if len(touch_points) > 1:
            # Multi-touch - reject
            event.ignore()
            return False

        # Single touch - proceed
        primary_point = touch_points[0]
```

**Detection:**
- Unexpected behavior when palm touches screen
- `event.touchPoints()` has length > 1
- Position jumps unexpectedly

**Phase impact:** Phase 14-01 should implement single-touch-only validation.

**Sources:**
- [Handling touch events for parent and child widgets](https://www.qtcentre.org/threads/71335-Handling-touch-events-for-parent-and-child-widgets)
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| 14-01 Touch Event Implementation | Pitfall #1 (synthesis blocking) | Test all buttons with touch after implementation |
| 14-01 Touch Event Implementation | Pitfall #4 (TouchBegin propagation) | Implement full Begin/Update/End cycle |
| 14-01 Touch Event Implementation | Pitfall #8 (timer inconsistency) | Use `QStyleHints.mousePressAndHoldInterval()` |
| 14-01 Touch Event Implementation | Pitfall #9 (movement threshold) | Implement 10px movement tolerance |
| 14-02 Verification & Documentation | Pitfall #3 (right-click conversion) | Test on Windows touchscreen hardware |
| 14-02 Verification & Documentation | Pitfall #7 (synthesis failure) | Long-running test (8+ hours) |
| 14-02 Verification & Documentation | Pitfall #2 (viewport attribute) | Audit all scroll areas |

---

## Industrial HMI-Specific Considerations

### Single Interaction Point Assumption

**Context:** Industrial HMI is typically single-user, single-touch at a time.

**Implications:**
- Multi-touch complexity reduced
- But still must handle accidental palm touches
- Can assume only one active interaction

**Recommendation:** Validate single-touch assumption in code - reject multi-touch events explicitly.

---

### Glove Usage

**Context:** Industrial environments may require protective gloves.

**Implications:**
- Capacitive touch may not work well with gloves
- Users may press harder, longer
- Touch point may be less precise

**Recommendation:**
- Test with various glove types
- Consider larger hit targets (already have 120x62px buttons)
- May need resistive touchscreen hardware instead of capacitive

---

### 24/7 Operation

**Context:** Industrial HMI may run continuously without restart.

**Implications:**
- Pitfall #7 (synthesis failure) is **critical**, not moderate
- Must detect and recover from synthesis failure
- Consider implementing automatic recovery (restart touch subsystem)

**Recommendation:** Implement touch event monitoring and automatic recovery.

---

## Testing Checklist

Before deploying touch support:

- [ ] All buttons work with touch (not just mouse)
- [ ] Long-press works on target frames
- [ ] Long-press doesn't trigger on accidental touch
- [ ] Movement threshold prevents false cancellation
- [ ] Multi-touch (palm) doesn't cause issues
- [ ] Numpad dialog opens correctly on long-press
- [ ] No event loop recursion crashes
- [ ] Touch → mouse synthesis working
- [ ] Platform-appropriate timing used
- [ ] Tested on actual touchscreen hardware (Windows)
- [ ] 8+ hour stability test (synthesis failure detection)
- [ ] Works with protective gloves (if applicable)

---

## Sources Summary

**HIGH Confidence Sources:**
- Official Qt Documentation (Qt 6.10.1, Qt 5.x)
- Qt Forums (developer reports with code examples)
- Qt Development Mailing List (architectural discussions)

**Key References:**
- [QTouchEvent Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtouchevent.html) - Official documentation
- [How does Qt synthesize Mouse Events from Touch Events?](https://forum.qt.io/topic/136576/how-does-qt-synthesize-mouse-events-from-touch-events) - Synthesis explanation
- [Touch event synthesis conflicts](https://groups.google.com/g/qt-project-list-development/c/J8G9KkFVkCM/m/iim6Ts4itiwJ) - Architectural issues
- [PySide6.QtGui.QTouchEvent](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTouchEvent.html) - Python bindings
- [PySide6 Signals, Slots and Events](https://www.pythonguis.com/tutorials/pyside6-signals-slots-events/) - Tutorial
