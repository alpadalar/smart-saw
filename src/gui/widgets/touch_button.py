"""
TouchButton widget with mouse and touch event handling.

This widget extends QPushButton to support both mouse and touch events,
enabling hold-to-jog functionality on touchscreen HMI systems.

Features:
- Dual mouse/touch event support
- Instant activation (0ms delay) on touch down
- Strict button bounds checking (no tolerance zone)
- Visual feedback during press
- Automatic stop when finger slides off button
- Custom signals for touch events
"""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import QPushButton
    from PySide6.QtCore import Qt, Signal, QEvent, QPointF
    from PySide6.QtGui import QTouchEvent
except ImportError:
    logging.warning("PySide6 not installed")
    QPushButton = object
    Signal = lambda *args: None
    Qt = object
    QEvent = object
    QPointF = object
    QTouchEvent = object

logger = logging.getLogger(__name__)


class TouchButton(QPushButton):
    """
    QPushButton with touch event support for industrial HMI.

    Signals:
        touch_pressed: Emitted when touch down occurs within button bounds
        touch_released: Emitted when touch is released or moves outside bounds
        pressed: Standard QPushButton signal (mouse compatibility)
        released: Standard QPushButton signal (mouse compatibility)
    """

    # Custom signals for touch events
    touch_pressed = Signal()
    touch_released = Signal()

    # Class variable to track if any positioning button is currently touched
    _active_touch_button: Optional['TouchButton'] = None

    def __init__(self, *args, **kwargs):
        """Initialize TouchButton with touch event support."""
        super().__init__(*args, **kwargs)

        # Enable touch events for this widget
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)

        # Track touch state for this button
        self._is_touch_pressed = False
        self._touch_point_id: Optional[int] = None

        logger.debug(f"TouchButton created: {self.objectName() or 'unnamed'}")

    def event(self, event: QEvent) -> bool:
        """
        Override event handler to process touch events.

        Args:
            event: Qt event object

        Returns:
            True if event was handled, False otherwise
        """
        event_type = event.type()

        # Handle touch events
        if event_type == QEvent.TouchBegin:
            return self._handle_touch_begin(event)
        elif event_type == QEvent.TouchUpdate:
            return self._handle_touch_update(event)
        elif event_type in (QEvent.TouchEnd, QEvent.TouchCancel):
            return self._handle_touch_end(event)

        # Pass all other events to base class (including mouse events)
        return super().event(event)

    def _handle_touch_begin(self, event: QTouchEvent) -> bool:
        """
        Handle touch begin event.

        Args:
            event: Touch event object

        Returns:
            True if event was handled
        """
        try:
            # Get touch points
            touch_points = event.touchPoints()
            if not touch_points:
                return False

            # Get first touch point
            touch_point = touch_points[0]
            touch_pos = touch_point.position()

            # Check if touch is within button bounds (strict bounds, no tolerance)
            if not self._is_point_in_bounds(touch_pos):
                return False

            # Check if another positioning button is already being touched
            # (first button wins for multi-touch)
            if TouchButton._active_touch_button is not None and \
               TouchButton._active_touch_button is not self:
                logger.debug(f"Touch ignored - another button already active: {self.objectName()}")
                return False

            # Mark this button as the active touch button
            TouchButton._active_touch_button = self

            # Store touch point ID for tracking
            self._touch_point_id = touch_point.id()
            self._is_touch_pressed = True

            # Update visual state
            self.setDown(True)

            # Emit custom touch signal
            self.touch_pressed.emit()

            logger.debug(f"Touch pressed: {self.objectName() or 'unnamed'}")

            # Accept the event
            event.accept()
            return True

        except Exception as e:
            logger.error(f"Touch begin error: {e}")
            return False

    def _handle_touch_update(self, event: QTouchEvent) -> bool:
        """
        Handle touch update event (finger movement).

        Args:
            event: Touch event object

        Returns:
            True if event was handled
        """
        try:
            # Only handle if this button has an active touch
            if not self._is_touch_pressed or self._touch_point_id is None:
                return False

            # Find our touch point by ID
            touch_points = event.touchPoints()
            our_touch_point = None
            for tp in touch_points:
                if tp.id() == self._touch_point_id:
                    our_touch_point = tp
                    break

            if our_touch_point is None:
                # Our touch point is gone - release
                self._release_touch()
                event.accept()
                return True

            # Check if touch point is still within button bounds
            touch_pos = our_touch_point.position()
            if not self._is_point_in_bounds(touch_pos):
                # Finger moved outside bounds - stop immediately
                logger.debug(f"Touch moved outside bounds: {self.objectName()}")
                self._release_touch()

            event.accept()
            return True

        except Exception as e:
            logger.error(f"Touch update error: {e}")
            return False

    def _handle_touch_end(self, event: QTouchEvent) -> bool:
        """
        Handle touch end/cancel event.

        Args:
            event: Touch event object

        Returns:
            True if event was handled
        """
        try:
            # Only handle if this button has an active touch
            if not self._is_touch_pressed:
                return False

            # Release touch state
            self._release_touch()

            logger.debug(f"Touch released: {self.objectName() or 'unnamed'}")

            event.accept()
            return True

        except Exception as e:
            logger.error(f"Touch end error: {e}")
            return False

    def _release_touch(self) -> None:
        """Release touch state and emit signals."""
        # Clear touch state
        self._is_touch_pressed = False
        self._touch_point_id = None

        # Clear class-level active button if it's us
        if TouchButton._active_touch_button is self:
            TouchButton._active_touch_button = None

        # Update visual state
        self.setDown(False)

        # Emit custom touch released signal
        self.touch_released.emit()

    def _is_point_in_bounds(self, point: QPointF) -> bool:
        """
        Check if a point is within button bounds.

        Args:
            point: Point to check (in local coordinates)

        Returns:
            True if point is within bounds
        """
        # Get button rect
        rect = self.rect()

        # Check if point is within bounds (strict, no tolerance)
        return rect.contains(int(point.x()), int(point.y()))
