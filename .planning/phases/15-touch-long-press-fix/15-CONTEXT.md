# Phase 15: Touch Long Press Fix - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix touch event handling on positioning buttons so long press works correctly with touch input. Users can long press to jog, release to stop, with proper visual feedback. Mouse input must continue working without regression.

</domain>

<decisions>
## Implementation Decisions

### Touch activation timing
- Instant activation (0ms) — jog starts immediately on touch down, no delay
- Quick tap triggers single jog pulse, sustained press triggers continuous jog
- No haptic/vibration feedback — visual only
- Strict button bounds — no touch tolerance zone, must touch exactly within button area

### Visual feedback style
- Match existing mouse press behavior — same visual feedback for touch
- Button pressed state is sufficient — no additional animation while jogging
- Silent fail on edge cases — no error feedback if touch fails to register
- Visual state maintained while finger on button — slight movement doesn't cancel pressed state

### Touch release behavior
- Immediate stop on touch release — no debounce delay
- Stop immediately if finger slides off button bounds
- Stop immediately on app focus loss or screen lock
- No timeout safety — instead, show emergency stop button on screen during jog
- Emergency stop button appears in empty area of screen while jog is active

### Multi-touch handling
- First button wins — ignore second positioning button touch
- Off-button touches ignored — jog continues, only button release matters
- Emergency stop button responds to any finger, including second touch
- 3+ simultaneous fingers: ignore extras, handle first touch normally

### Claude's Discretion
- Qt touch event implementation details
- Emergency stop button positioning and styling
- Exact event handling architecture

</decisions>

<specifics>
## Specific Ideas

- Emergency stop button should appear somewhere on screen during active jog — acts as safety release if touch event is missed
- Behavior should feel identical to mouse for users who use both input methods

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 15-touch-long-press-fix*
*Context gathered: 2026-01-29*
