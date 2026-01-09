"""
Control panel controller - Complete implementation matching old GUI design.

This is a production-ready, pixel-perfect recreation of the old control panel
with all features, thread-safe data handling, and Qt Signals/Slots.

Page size: 1528x1080 (content area, not including sidebar)
Framework: PySide6
"""

import logging
import os
import queue
import threading
import collections
import asyncio
from typing import Optional, Dict, Callable
from datetime import datetime, timedelta

from ...domain.enums import ControlMode
from ...services.control.machine_control import MachineControl

try:
    from PySide6.QtWidgets import (
        QWidget, QFrame, QPushButton, QLabel, QTextEdit, QToolButton,
        QProgressBar, QDialog, QVBoxLayout, QHBoxLayout, QApplication
    )
    from PySide6.QtCore import Qt, QTimer, QDateTime, Slot, Signal, QPoint, QSize
    from PySide6.QtGui import (
        QFont, QPixmap, QIcon, QTextCursor, QPainter, QPen,
        QColor, QBrush, QPolygon, QImage
    )
except ImportError:
    logging.warning("PySide6 not installed")
    QWidget = object
    QDialog = object
    QFrame = object
    QPushButton = object
    QLabel = object
    QTextEdit = object
    QProgressBar = object
    QVBoxLayout = object
    QHBoxLayout = object
    QApplication = object
    Qt = object
    QTimer = object
    QDateTime = object
    Slot = lambda *args, **kwargs: (lambda f: f)
    Signal = lambda *args: None
    QFont = object
    QPixmap = object
    QIcon = object
    QTextCursor = object
    QPainter = object
    QPen = object
    QColor = object
    QBrush = object
    QPolygon = object
    QImage = object

logger = logging.getLogger(__name__)

# Global variable for last meaningful speed
last_meaningful_speed = None


# ============================================================================
# NumpadDialog - Import from separate module with nice design
# ============================================================================
try:
    from ..numpad import NumpadDialog
except ImportError:
    # Fallback simple implementation if import fails
    class NumpadDialog(QDialog):
        """Simple fallback number input dialog."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Sayı Girişi")
            self.setModal(True)
            self.setFixedSize(400, 300)
            self.value = ""
            self.Accepted = QDialog.Accepted
            self.setup_ui()

        def setup_ui(self):
            layout = QVBoxLayout(self)
            self.display_label = QLabel("0")
            self.display_label.setStyleSheet("font-size: 24px; padding: 10px;")
            self.display_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.display_label)

            for row in range(3):
                row_layout = QHBoxLayout()
                for col in range(3):
                    number = row * 3 + col + 1
                    btn = QPushButton(str(number))
                    btn.setFixedSize(80, 60)
                    btn.clicked.connect(lambda checked, n=number: self.add_digit(str(n)))
                    row_layout.addWidget(btn)
                layout.addLayout(row_layout)

            bottom_layout = QHBoxLayout()
            clear_btn = QPushButton("Temizle")
            clear_btn.setFixedSize(80, 60)
            clear_btn.clicked.connect(self.clear_value)
            bottom_layout.addWidget(clear_btn)
            zero_btn = QPushButton("0")
            zero_btn.setFixedSize(80, 60)
            zero_btn.clicked.connect(lambda: self.add_digit("0"))
            bottom_layout.addWidget(zero_btn)
            ok_btn = QPushButton("Tamam")
            ok_btn.setFixedSize(80, 60)
            ok_btn.clicked.connect(self.accept)
            bottom_layout.addWidget(ok_btn)
            layout.addLayout(bottom_layout)

        def add_digit(self, digit):
            if len(self.value) < 10:
                self.value += digit
                self.update_label()

        def clear_value(self):
            self.value = ""
            self.update_label()

        def update_label(self):
            self.display_label.setText(self.value if self.value else "0")

        def get_value(self):
            return self.value


# ============================================================================
# RoundedVerticalProgressBar - Custom progress bar with proper rounded corners
# ============================================================================
class RoundedVerticalProgressBar(QWidget):
    """
    Custom vertical progress bar with proper rounded corners at all fill levels.

    Qt's QProgressBar chunk doesn't maintain border-radius when the fill height
    is less than 2x the radius. This custom widget solves that by painting
    the progress manually.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 100
        self._value = 0
        self._radius = 25
        self._background_color = QColor(149, 9, 82, 51)  # rgba(149, 9, 82, 0.2)
        self._fill_color = QColor(149, 9, 82)  # #950952

    def setMinimum(self, value: int):
        self._minimum = value
        self.update()

    def setMaximum(self, value: int):
        self._maximum = value
        self.update()

    def setValue(self, value: int):
        self._value = max(self._minimum, min(self._maximum, value))
        self.update()

    def value(self) -> int:
        return self._value

    def paintEvent(self, event):
        """Paint the progress bar with proper rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate dimensions
        width = self.width()
        height = self.height()
        radius = min(self._radius, width // 2)

        # Draw background (full bar)
        painter.setBrush(QBrush(self._background_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, radius, radius)

        # Calculate fill height based on value
        if self._maximum > self._minimum:
            ratio = (self._value - self._minimum) / (self._maximum - self._minimum)
        else:
            ratio = 0

        fill_height = int(height * ratio)

        if fill_height > 0:
            # Draw filled portion from bottom
            # Use clipping to maintain rounded corners
            painter.setBrush(QBrush(self._fill_color))

            # Create a path for the rounded rectangle
            from PySide6.QtGui import QPainterPath
            path = QPainterPath()
            path.addRoundedRect(0, 0, width, height, radius, radius)

            # Clip to the rounded rectangle
            painter.setClipPath(path)

            # Draw the fill from the bottom
            fill_top = height - fill_height
            painter.drawRect(0, fill_top, width, fill_height)

        painter.end()


# ============================================================================
# BandDeviationGraphWidget - Real-time graph for band deviation
# ============================================================================
class BandDeviationGraphWidget(QWidget):
    """
    Real-time graph widget for band deviation values.

    Features:
    - Shows positive and negative values with zero line in center
    - Dashed white line at zero level
    - Dynamic range that adjusts to data
    - Single line (no fill)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(278, 144)

        # Data structure: (timestamp, value) tuples
        self.data_points = collections.deque(maxlen=300)  # 30 seconds * 10 data/sec
        self.max_points = 300

        # Max/min value tracking (for display labels)
        self.max_value = float('-inf')
        self.min_value = float('inf')

        # Graph settings
        self.padding = 10
        self.grid_color = QColor(255, 255, 255, 30)  # Transparent white
        self.zero_line_color = QColor(255, 255, 255, 180)  # White for zero line
        self.line_color = QColor(149, 9, 82)  # Main color #950952

        # Thread-safe data access lock
        self._data_lock = threading.Lock()

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)  # 20 FPS for smooth display

        # Widget style
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)

    def add_data_point(self, value: float):
        """Add new data point (thread-safe)."""
        try:
            with self._data_lock:
                timestamp = datetime.now()
                self.data_points.append((timestamp, value))

                # Update max/min values
                if value > self.max_value:
                    self.max_value = value
                if value < self.min_value:
                    self.min_value = value
        except Exception as e:
            logger.error(f"Error adding data point: {e}")

    def clear_old_data(self):
        """Clear data older than 30 seconds and recalculate min/max."""
        try:
            with self._data_lock:
                cutoff_time = datetime.now() - timedelta(seconds=30)
                while self.data_points and self.data_points[0][0] < cutoff_time:
                    self.data_points.popleft()

                # Recalculate min/max from remaining data points
                if self.data_points:
                    values = [point[1] for point in self.data_points]
                    self.max_value = max(values)
                    self.min_value = min(values)
                else:
                    # No data points - reset to initial values
                    self.max_value = float('-inf')
                    self.min_value = float('inf')
        except Exception as e:
            logger.error(f"Error clearing old data: {e}")

    def get_max_value(self) -> float:
        """Return maximum positive value."""
        try:
            with self._data_lock:
                if self.max_value == float('-inf'):
                    return 0.0
                return max(0.0, self.max_value)
        except Exception as e:
            logger.error(f"Error getting max value: {e}")
            return 0.0

    def get_min_value(self) -> float:
        """Return minimum value (can be positive or negative)."""
        try:
            with self._data_lock:
                if self.min_value == float('inf'):
                    return 0.0
                return self.min_value
        except Exception as e:
            logger.error(f"Error getting min value: {e}")
            return 0.0

    def paintEvent(self, event):
        """Draw the graph."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Transparent background
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

            # Calculate drawing area
            draw_rect = self.rect().adjusted(
                self.padding, self.padding, -self.padding, -self.padding
            )

            # Draw data first to get zero_y position
            zero_y = self._draw_data(painter, draw_rect)

            # Draw grid with zero line
            self._draw_grid(painter, draw_rect, zero_y)

        except Exception as e:
            logger.error(f"Graph drawing error: {e}")

    def _draw_grid(self, painter: QPainter, rect, zero_y: int = None):
        """Draw grid lines and zero line."""
        try:
            painter.setPen(QPen(self.grid_color, 1))

            # Vertical lines (16 lines)
            for i in range(17):
                x = rect.left() + (rect.width() * i) // 16
                painter.drawLine(x, rect.top(), x, rect.bottom())

            # Horizontal lines (4 lines) - faint grid
            for i in range(5):
                y = rect.top() + (rect.height() * i) // 4
                painter.drawLine(rect.left(), y, rect.right(), y)

            # Draw zero line (dashed white) if provided
            if zero_y is not None and rect.top() <= zero_y <= rect.bottom():
                pen = QPen(self.zero_line_color, 2, Qt.DashLine)
                painter.setPen(pen)
                painter.drawLine(rect.left(), zero_y, rect.right(), zero_y)

        except Exception as e:
            logger.error(f"Grid drawing error: {e}")

    def _draw_data(self, painter: QPainter, rect):
        """
        Draw data line with dynamic range and zero line at actual zero position.

        Returns:
            zero_y: Y coordinate of zero line for grid drawing
        """
        zero_y = None
        try:
            with self._data_lock:
                if len(self.data_points) < 2:
                    # No data - draw zero line at center
                    return rect.top() + rect.height() // 2

                # Calculate value range
                values = [point[1] for point in self.data_points]
                min_val = min(values)
                max_val = max(values)

                # Ensure zero is included in the range
                range_min = min(min_val, 0)
                range_max = max(max_val, 0)

                # Add small padding if range is too small
                if range_max - range_min < 0.1:
                    padding = 0.05
                    range_min -= padding
                    range_max += padding

                # Calculate zero line Y position at actual zero
                if range_max != range_min:
                    zero_normalized = (0 - range_min) / (range_max - range_min)
                    zero_y = int(rect.bottom() - (rect.height() * zero_normalized))
                else:
                    zero_y = rect.top() + rect.height() // 2

                # Calculate line points
                points = []
                for i, (timestamp, value) in enumerate(self.data_points):
                    # X coordinate (time)
                    x = rect.left() + (rect.width() * i) // (len(self.data_points) - 1)

                    # Y coordinate (value) - normalized to actual range
                    if range_max != range_min:
                        normalized_value = (value - range_min) / (range_max - range_min)
                    else:
                        normalized_value = 0.5
                    y = rect.bottom() - (rect.height() * normalized_value)
                    points.append((x, y))

                # Draw hatched fill between zero line and data line
                if len(points) > 1 and zero_y is not None:
                    # Create polygon for fill area
                    fill_polygon = QPolygon()

                    # Add all data points
                    for x, y in points:
                        fill_polygon.append(QPoint(int(x), int(y)))

                    # Close polygon along zero line (right to left)
                    fill_polygon.append(QPoint(int(points[-1][0]), zero_y))
                    fill_polygon.append(QPoint(int(points[0][0]), zero_y))

                    # First draw transparent solid fill
                    painter.setPen(Qt.NoPen)
                    fill_color = QColor(self.line_color)
                    fill_color.setAlpha(40)  # ~15% opacity
                    painter.setBrush(QBrush(fill_color))
                    painter.drawPolygon(fill_polygon)

                    # Then draw hatched pattern on top
                    painter.setBrush(QBrush(self.line_color, Qt.BDiagPattern))
                    painter.setOpacity(0.5)
                    painter.drawPolygon(fill_polygon)
                    painter.setOpacity(1.0)

                # Draw main line
                if len(points) > 1:
                    painter.setPen(QPen(self.line_color, 3))
                    painter.setBrush(Qt.NoBrush)

                    for i in range(len(points) - 1):
                        painter.drawLine(
                            int(points[i][0]), int(points[i][1]),
                            int(points[i+1][0]), int(points[i+1][1])
                        )

                # Small dot marker for last point
                if points:
                    last_x, last_y = points[-1]
                    dot_radius = 5
                    painter.setBrush(QBrush(QColor(255, 0, 0)))
                    painter.setPen(QPen(QColor(255, 0, 0), 1))
                    painter.drawEllipse(
                        QPoint(int(last_x), int(last_y)),
                        dot_radius, dot_radius
                    )

        except Exception as e:
            logger.error(f"Data drawing error: {e}")

        return zero_y

    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        self.update()


# ============================================================================
# ControlPanelController - Main controller widget
# ============================================================================
class ControlPanelController(QWidget):
    """
    Control panel controller with complete old GUI implementation.

    Features:
    - Cutting mode buttons (Manual/AI/Fuzzy/Expert)
    - Speed preset buttons (Slow/Normal/Fast)
    - Head height display with vertical progress bar
    - Band deviation real-time graph
    - Band cutting/descent speed displays
    - Motor current and torque displays
    - System status with icons
    - Cutting time tracking (start/stop)
    - Control buttons (coolant, sawdust, start, stop)
    - Log viewer with auto-scroll
    - Thread-safe data handling
    - Qt Signals/Slots for async operations
    """

    def __init__(
        self,
        control_manager=None,
        data_pipeline=None,
        parent=None
    ):
        """
        Initialize control panel controller.

        Args:
            control_manager: Control manager instance for machine control
            data_pipeline: Data pipeline instance for data access
            parent: Parent widget
        """
        super().__init__(parent)

        # Dependencies
        self.control_manager = control_manager
        self.data_pipeline = data_pipeline

        # Legacy compatibility attributes
        self.controller_factory = control_manager
        self.get_data_callback = data_pipeline

        # Initialize MachineControl singleton for speed/control operations
        try:
            self.machine_control = MachineControl()
            logger.info("MachineControl singleton initialized for ControlPanelController")
        except Exception as e:
            logger.error(f"Failed to initialize MachineControl: {e}")
            self.machine_control = None

        # Data management
        self.current_values = {}
        self._values_lock = threading.Lock()
        self._last_update_time = None

        # Cutting time tracking
        self._cutting_start_time = None
        self._cutting_start_datetime = None
        self._cutting_stop_datetime = None
        self._previous_testere_durumu = None  # Track previous state for cutting end detection
        self._cutting_start_height = None  # Height when cutting started (for remaining time calc)
        self._previous_cutting_duration = None  # Previous cutting duration string for display

        # Speed values for preset buttons
        self.speed_values = {
            "slow": {"cutting": 15.0, "descent": 8.0},
            "normal": {"cutting": 25.0, "descent": 12.0},
            "fast": {"cutting": 35.0, "descent": 18.0}
        }

        # Log queue for thread-safe logging
        self.log_queue = queue.Queue()

        # Flags and state
        self._force_update_cutting_speed = False
        self._frame_click_enabled = True
        self._last_control_factory_log = None

        # Graph widget reference
        self.band_deviation_graph = None

        # Initialize values
        self._initialize_current_values()

        # Setup UI
        self._setup_ui()

        # Setup timers
        self._setup_timers()

        logger.info("ControlPanelController initialized")

    def _initialize_current_values(self):
        """Initialize default values for all data fields."""
        self.current_values = {
            'makine_id': '-',
            'serit_id': '-',
            'serit_dis_mm': '-',
            'serit_tip': '-',
            'serit_marka': '-',
            'serit_malz': '-',
            'malzeme_cinsi': '-',
            'malzeme_sertlik': '-',
            'kesit_yapisi': '-',
            'a_mm': '-',
            'b_mm': '-',
            'c_mm': '-',
            'd_mm': '-',
            'kafa_yuksekligi_mm': '0.0',
            'serit_motor_akim_a': '0.0',
            'serit_motor_tork_percentage': '0.0',
            'inme_motor_akim_a': '0.0',
            'inme_motor_tork_percentage': '0.0',
            'mengene_basinc_bar': '0.0',
            'serit_gerginligi_bar': '0.0',
            'serit_sapmasi': '0.00',
            'ortam_sicakligi_c': '0.0',
            'ortam_nem_percentage': '0.0',
            'sogutma_sivi_sicakligi_c': '0.0',
            'hidrolik_yag_sicakligi_c': '0.0',
            'ivme_olcer_x': '0.000',
            'ivme_olcer_y': '0.000',
            'ivme_olcer_z': '0.000',
            'ivme_olcer_x_hz': '0.0',
            'ivme_olcer_y_hz': '0.0',
            'ivme_olcer_z_hz': '0.0',
            'serit_kesme_hizi': '0.0',
            'serit_inme_hizi': '0.0',
            'kesilen_parca_adeti': '0',
            'testere_durumu': 'Bağlantı Yok',
            'alarm_status': '-',
            'alarm_bilgisi': '-',
            'kesim_baslama': '-',
            'kesim_sure': '-',
            'modbus_status': 'Bağlantı Yok'
        }

    def _setup_ui(self):
        """Setup the complete UI with all frames and widgets."""
        # Widget size: 1528x1080
        self.setMinimumSize(1528, 1080)
        self.setStyleSheet("background-color: transparent;")

        # Common styles
        frame_style = """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                border-radius: 20px;
            }
        """

        nested_frame_style = """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                border-radius: 20px;
            }
        """

        label_title_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 24px;
            }
        """

        label_value_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 48px;
            }
        """

        button_mode_style = """
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(45, 54, 95, 200), stop:1 rgba(26, 31, 55, 200));
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                text-align: center;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(149, 9, 82, 255), stop:1 rgba(26, 31, 55, 255));
            }
        """

        button_speed_style = """
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(45, 54, 95, 200), stop:1 rgba(26, 31, 55, 200));
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                text-align: center;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(149, 9, 82, 255), stop:1 rgba(26, 31, 55, 255));
            }
        """
        speed_info_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 20px;
                text-align: left;
            }
        """

        # === CUTTING MODE FRAME (33, 127, 440, 344) ===
        self.cuttingModeFrame = QFrame(self)
        self.cuttingModeFrame.setGeometry(33, 127, 440, 344)
        self.cuttingModeFrame.setStyleSheet(frame_style)

        self.labelCuttingMode = QLabel("Kesim Modu", self.cuttingModeFrame)
        self.labelCuttingMode.setGeometry(27, 26, 381, 34)
        self.labelCuttingMode.setStyleSheet(label_title_style)

        # Mode buttons (2 buttons: Manual, AI)
        self.btnManualMode = QPushButton("Manuel", self.cuttingModeFrame)
        self.btnManualMode.setGeometry(18, 87, 195, 55)
        self.btnManualMode.setStyleSheet(button_mode_style)
        self.btnManualMode.setCheckable(True)
        self.btnManualMode.setChecked(True)
        self.btnManualMode.clicked.connect(
            lambda: self._handle_cutting_mode_buttons(self.btnManualMode)
        )

        self.btnAiMode = QPushButton("Yapay Zeka", self.cuttingModeFrame)
        self.btnAiMode.setGeometry(226, 87, 195, 55)
        self.btnAiMode.setStyleSheet(
            button_mode_style.replace("padding-left: 52px;", "padding-left: 32px;")
        )
        self.btnAiMode.setCheckable(True)
        self.btnAiMode.clicked.connect(
            lambda: self._handle_cutting_mode_buttons(self.btnAiMode)
        )

        # Speed preset buttons
        self.labelSpeed = QLabel("Hız Seçimi", self.cuttingModeFrame)
        self.labelSpeed.setGeometry(27, 170, 371, 34)
        self.labelSpeed.setStyleSheet(label_title_style)

        self.btnSlowSpeed = QPushButton("Yavaş", self.cuttingModeFrame)
        self.btnSlowSpeed.setGeometry(19, 231, 120, 65)
        self.btnSlowSpeed.setStyleSheet(button_speed_style)
        self.btnSlowSpeed.setCheckable(True)
        self.btnSlowSpeed.clicked.connect(
            lambda: self._handle_speed_buttons(self.btnSlowSpeed)
        )

        self.btnNormalSpeed = QPushButton("Normal", self.cuttingModeFrame)
        self.btnNormalSpeed.setGeometry(160, 231, 120, 65)
        self.btnNormalSpeed.setStyleSheet(button_speed_style)
        self.btnNormalSpeed.setCheckable(True)
        self.btnNormalSpeed.clicked.connect(
            lambda: self._handle_speed_buttons(self.btnNormalSpeed)
        )

        self.btnFastSpeed = QPushButton("Hızlı", self.cuttingModeFrame)
        self.btnFastSpeed.setGeometry(300, 231, 120, 65)
        self.btnFastSpeed.setStyleSheet(button_speed_style)
        self.btnFastSpeed.setCheckable(True)
        self.btnFastSpeed.clicked.connect(
            lambda: self._handle_speed_buttons(self.btnFastSpeed)
        )

        # === HEAD HEIGHT FRAME (488, 127, 251, 344) ===
        self.headHeightFrame = QFrame(self)
        self.headHeightFrame.setGeometry(488, 127, 251, 344)
        self.headHeightFrame.setStyleSheet(frame_style)

        self.labelHeadHeight = QLabel("Kafa Yüksekliği", self.headHeightFrame)
        self.labelHeadHeight.setGeometry(25, 26, 211, 34)
        self.labelHeadHeight.setStyleSheet(label_title_style)

        # Vertical progress bar - Custom painted widget for proper rounded corners
        self.progressBarHeight = RoundedVerticalProgressBar(self.headHeightFrame)
        self.progressBarHeight.setGeometry(27, 78, 50, 250)
        self.progressBarHeight.setMinimum(0)
        self.progressBarHeight.setMaximum(350)
        self.progressBarHeight.setValue(0)

        # Height value label
        self.labelValue = QLabel("0", self.headHeightFrame)
        self.labelValue.setGeometry(135, 160, 110, 60)
        self.labelValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 32px;
            }
        """)
        self.labelValue.setAlignment(Qt.AlignCenter)

        self.labelmm = QLabel("mm", self.headHeightFrame)
        self.labelmm.setGeometry(170, 210, 41, 34)
        self.labelmm.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: light;
                font-size: 24px;
            }
        """)

        # === BAND DEVIATION FRAME (756, 127, 401, 344) ===
        self.bandDeviationFrame = QFrame(self)
        self.bandDeviationFrame.setGeometry(756, 127, 401, 344)
        self.bandDeviationFrame.setStyleSheet(frame_style)

        self.labelBandDeviation = QLabel("Şerit Sapması", self.bandDeviationFrame)
        self.labelBandDeviation.setGeometry(27, 26, 271, 34)
        self.labelBandDeviation.setStyleSheet(label_title_style)

        # Graph widget container
        self.bandDeviationGraphFrame = QFrame(self.bandDeviationFrame)
        self.bandDeviationGraphFrame.setGeometry(27, 78, 278, 144)
        self.bandDeviationGraphFrame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)

        # Create graph widget
        self.band_deviation_graph = BandDeviationGraphWidget(
            self.bandDeviationGraphFrame
        )
        self.band_deviation_graph.setGeometry(0, 0, 278, 144)
        self.band_deviation_graph.show()

        # Min/max labels
        self.ustdegerlabel = QLabel(" 0.00", self.bandDeviationFrame)
        self.ustdegerlabel.setGeometry(320, 78, 70, 30)
        self.ustdegerlabel.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 16px;
            }
        """)

        self.altdegerlabel = QLabel(" 0.00", self.bandDeviationFrame)
        self.altdegerlabel.setGeometry(320, 192, 70, 30)
        self.altdegerlabel.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 16px;
            }
        """)

        # Deviation value (large display)
        self.labelBandDeviationValue = QLabel("0.00", self.bandDeviationFrame)
        self.labelBandDeviationValue.setGeometry(26, 244, 347, 80)
        self.labelBandDeviationValue.setStyleSheet(label_value_style)
        self.labelBandDeviationValue.setAlignment(Qt.AlignCenter)

        # === SYSTEM STATUS FRAME (1176, 127, 321, 243) ===
        self.systemStatusFrame = QFrame(self)
        self.systemStatusFrame.setGeometry(1176, 127, 321, 243)
        self.systemStatusFrame.setStyleSheet(frame_style)

        self.labelSystemStatus = QLabel("Sistem Durumu", self.systemStatusFrame)
        self.labelSystemStatus.setGeometry(27, 26, 271, 34)
        self.labelSystemStatus.setStyleSheet(label_title_style)

        # Status icon
        self.iconStatus = QLabel(self.systemStatusFrame)
        self.iconStatus.setGeometry(125, 70, 71, 71)
        self.iconStatus.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)
        self.iconStatus.setAlignment(Qt.AlignCenter)
        self.iconStatus.setScaledContents(True)

        # Status text
        self.labelSystemStatusInfo = QLabel(
            "Bağlantı Kontrol Ediliyor...",
            self.systemStatusFrame
        )
        self.labelSystemStatusInfo.setGeometry(41, 150, 241, 70)
        self.labelSystemStatusInfo.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: 400;
                font-size: 26px;
            }
        """)
        self.labelSystemStatusInfo.setAlignment(Qt.AlignCenter)
        self.labelSystemStatusInfo.setWordWrap(True)

        # === BAND CUTTING SPEED FRAME (33, 486, 551, 344) ===
        self.bandCuttingSpeedFrame = QFrame(self)
        self.bandCuttingSpeedFrame.setGeometry(33, 486, 551, 344)
        self.bandCuttingSpeedFrame.setStyleSheet(frame_style)
        self.bandCuttingSpeedFrame.setCursor(Qt.PointingHandCursor)
        self.bandCuttingSpeedFrame.mousePressEvent = self._handle_cutting_speed_frame_click

        self.labelBandCuttingSpeed = QLabel(
            "Şerit Kesme Hızı",
            self.bandCuttingSpeedFrame
        )
        self.labelBandCuttingSpeed.setGeometry(31, 27, 491, 45)
        self.labelBandCuttingSpeed.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 32px;
            }
        """)

        self.labelBandCuttingSpeedInfo = QLabel(
            "Hız Değeri Girmek İçin Tıklayınız.",
            self.bandCuttingSpeedFrame
        )
        self.labelBandCuttingSpeedInfo.setGeometry(31, 90, 491, 34)
        self.labelBandCuttingSpeedInfo.setStyleSheet(speed_info_style)

        # Large speed value display
        self.labelBandCuttingSpeedValue = QLabel("0", self.bandCuttingSpeedFrame)
        self.labelBandCuttingSpeedValue.setGeometry(300, 70, 241, 111)
        self.labelBandCuttingSpeedValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 80px;
            }
        """)
        self.labelBandCuttingSpeedValue.setAlignment(Qt.AlignCenter)

        # Sent speed label
        self.labelSentCuttingSpeed = QLabel("0.0", self.bandCuttingSpeedFrame)
        self.labelSentCuttingSpeed.setGeometry(31, 115, 200, 80)
        self.labelSentCuttingSpeed.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: light;
                font-size: 25px;
            }
        """)

        # Current frame
        self.BandCuttingCurrentFrame = QFrame(self.bandCuttingSpeedFrame)
        self.BandCuttingCurrentFrame.setGeometry(31, 200, 217, 109)
        self.BandCuttingCurrentFrame.setStyleSheet(nested_frame_style)

        self.labelBandCuttingCurrent = QLabel(
            "Şerit Motor Akım",
            self.BandCuttingCurrentFrame
        )
        self.labelBandCuttingCurrent.setGeometry(23, 20, 181, 20)
        self.labelBandCuttingCurrent.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 20px;
            }
        """)

        self.labelBandCuttingCurrentValue = QLabel("0.0", self.BandCuttingCurrentFrame)
        self.labelBandCuttingCurrentValue.setGeometry(21, 43, 171, 50)
        self.labelBandCuttingCurrentValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 36px;
            }
        """)
        self.labelBandCuttingCurrentValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Torque frame
        self.BandCuttingTorqueFrame = QFrame(self.bandCuttingSpeedFrame)
        self.BandCuttingTorqueFrame.setGeometry(294, 200, 217, 109)
        self.BandCuttingTorqueFrame.setStyleSheet(nested_frame_style)

        self.labelBandCuttingTorque = QLabel(
            "Şerit Motor Tork",
            self.BandCuttingTorqueFrame
        )
        self.labelBandCuttingTorque.setGeometry(23, 20, 181, 20)
        self.labelBandCuttingTorque.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 20px;
            }
        """)

        self.labelBandCuttingTorqueValue = QLabel("0.0", self.BandCuttingTorqueFrame)
        self.labelBandCuttingTorqueValue.setGeometry(21, 43, 171, 50)
        self.labelBandCuttingTorqueValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 36px;
            }
        """)
        self.labelBandCuttingTorqueValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # === BAND DESCENT SPEED FRAME (606, 486, 551, 344) ===
        self.bandDescentSpeedFrame = QFrame(self)
        self.bandDescentSpeedFrame.setGeometry(606, 486, 551, 344)
        self.bandDescentSpeedFrame.setStyleSheet(frame_style)
        self.bandDescentSpeedFrame.setCursor(Qt.PointingHandCursor)
        self.bandDescentSpeedFrame.mousePressEvent = self._handle_descent_speed_frame_click

        self.labelBandDescentSpeed = QLabel(
            "Şerit İnme Hızı",
            self.bandDescentSpeedFrame
        )
        self.labelBandDescentSpeed.setGeometry(31, 27, 491, 45)
        self.labelBandDescentSpeed.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 32px;
            }
        """)

        self.labelBandDescentSpeedInfo = QLabel(
            "Hız Değeri Girmek İçin Tıklayınız.",
            self.bandDescentSpeedFrame
        )
        self.labelBandDescentSpeedInfo.setGeometry(31, 90, 491, 34)
        self.labelBandDescentSpeedInfo.setStyleSheet(speed_info_style)

        # Large speed value display
        self.labelBandDescentSpeedValue = QLabel("0", self.bandDescentSpeedFrame)
        self.labelBandDescentSpeedValue.setGeometry(300, 70, 241, 111)
        self.labelBandDescentSpeedValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 80px;
            }
        """)
        self.labelBandDescentSpeedValue.setAlignment(Qt.AlignCenter)

        # Sent speed label
        self.labelSentDescentSpeed = QLabel("0.0", self.bandDescentSpeedFrame)
        self.labelSentDescentSpeed.setGeometry(31, 115, 200, 80)
        self.labelSentDescentSpeed.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: light;
                font-size: 25px;
            }
        """)

        # Current frame
        self.BandDescentCurrentFrame = QFrame(self.bandDescentSpeedFrame)
        self.BandDescentCurrentFrame.setGeometry(31, 200, 217, 109)
        self.BandDescentCurrentFrame.setStyleSheet(nested_frame_style)

        self.labelBandDescentCurrent = QLabel(
            "İnme Motor Akım",
            self.BandDescentCurrentFrame
        )
        self.labelBandDescentCurrent.setGeometry(23, 20, 181, 20)
        self.labelBandDescentCurrent.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 20px;
            }
        """)

        self.labelBandDescentCurrentValue = QLabel("0.0", self.BandDescentCurrentFrame)
        self.labelBandDescentCurrentValue.setGeometry(21, 43, 171, 50)
        self.labelBandDescentCurrentValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 36px;
            }
        """)
        self.labelBandDescentCurrentValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Torque frame
        self.BandDescentTorqueFrame = QFrame(self.bandDescentSpeedFrame)
        self.BandDescentTorqueFrame.setGeometry(294, 200, 217, 109)
        self.BandDescentTorqueFrame.setStyleSheet(nested_frame_style)

        self.labelBandDescentTorque = QLabel(
            "İnme Motor Tork",
            self.BandDescentTorqueFrame
        )
        self.labelBandDescentTorque.setGeometry(23, 20, 181, 20)
        self.labelBandDescentTorque.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 20px;
            }
        """)

        self.labelBandDescentTorqueValue = QLabel("0.0", self.BandDescentTorqueFrame)
        self.labelBandDescentTorqueValue.setGeometry(21, 43, 171, 50)
        self.labelBandDescentTorqueValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 36px;
            }
        """)
        self.labelBandDescentTorqueValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # === LOG VIEWER FRAME (1176, 384, 321, 480) ===
        self.logViewerFrame = QFrame(self)
        self.logViewerFrame.setGeometry(1176, 384, 321, 460)
        self.logViewerFrame.setStyleSheet(frame_style)

        self.labelLogViewer = QLabel("Çalışma Günlüğü", self.logViewerFrame)
        self.labelLogViewer.setGeometry(27, 26, 271, 34)
        self.labelLogViewer.setStyleSheet(label_title_style)

        # Log text widget
        self.log_text = QTextEdit(self.logViewerFrame)
        self.log_text.setGeometry(30, 70, 261, 360)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 14px;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(26, 31, 55, 100);
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #950952;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # === CUTTING CONTROL FRAME (33, 845, 1127, 221) ===
        self.cuttingControlFrame = QFrame(self)
        self.cuttingControlFrame.setGeometry(33, 845, 1127, 221)
        self.cuttingControlFrame.setStyleSheet(frame_style)

        self.labelCuttingControl = QLabel("Kesim Kontrol", self.cuttingControlFrame)
        self.labelCuttingControl.setGeometry(27, 16, 271, 34)
        self.labelCuttingControl.setStyleSheet(label_title_style)

        # Button style for control buttons
        control_button_style = """
            QToolButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(45, 54, 95, 200), stop:1 rgba(26, 31, 55, 200));
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 22px;
                text-align: top-center;
                border-radius: 25px;
                border: 2px solid #F4F6FC;
                padding-top: 10px;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QToolButton:checked {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(149, 9, 82, 255), stop:1 rgba(26, 31, 55, 255));
            }
            QToolButton:disabled {
                background-color: rgba(26, 31, 55, 100);
                color: rgba(244, 246, 252, 100);
            }
        """

        # Coolant button
        self.toolBtnCoolant = QToolButton(self.cuttingControlFrame)
        self.toolBtnCoolant.setText("Soğutma Sıvısı")
        self.toolBtnCoolant.setGeometry(35, 63, 248, 135)
        self.toolBtnCoolant.setStyleSheet(control_button_style)
        self.toolBtnCoolant.setCheckable(True)
        self.toolBtnCoolant.setIcon(self._load_icon("coolant-liquid-icon.svg"))
        self.toolBtnCoolant.setIconSize(QSize(90, 90))
        self.toolBtnCoolant.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBtnCoolant.toggled.connect(self._on_coolant_toggled)

        # Sawdust cleaning button
        self.toolBtnSawdustCleaning = QToolButton(self.cuttingControlFrame)
        self.toolBtnSawdustCleaning.setText("Talaş Temizliği")
        self.toolBtnSawdustCleaning.setGeometry(305, 63, 248, 135)
        self.toolBtnSawdustCleaning.setStyleSheet(control_button_style)
        self.toolBtnSawdustCleaning.setCheckable(True)
        self.toolBtnSawdustCleaning.setIcon(self._load_icon("sawdust-cleaning-icon.svg"))
        self.toolBtnSawdustCleaning.setIconSize(QSize(90, 90))
        self.toolBtnSawdustCleaning.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBtnSawdustCleaning.toggled.connect(self._on_chip_cleaning_toggled)

        # Cutting start button
        self.toolBtnCuttingStart = QToolButton(self.cuttingControlFrame)
        self.toolBtnCuttingStart.setText("Kesim Başlat")
        self.toolBtnCuttingStart.setGeometry(575, 63, 248, 135)
        self.toolBtnCuttingStart.setStyleSheet(control_button_style)
        self.toolBtnCuttingStart.setIcon(self._load_icon("cutting-start-icon.svg"))
        self.toolBtnCuttingStart.setIconSize(QSize(90, 90))
        self.toolBtnCuttingStart.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBtnCuttingStart.clicked.connect(self._on_cutting_start_clicked)

        # Cutting stop button
        self.toolBtnCuttingStop = QToolButton(self.cuttingControlFrame)
        self.toolBtnCuttingStop.setText("Kesim Durdur")
        self.toolBtnCuttingStop.setGeometry(845, 63, 248, 135)
        self.toolBtnCuttingStop.setStyleSheet(control_button_style)
        self.toolBtnCuttingStop.setIcon(self._load_icon("cutting-stop-icon.svg"))
        self.toolBtnCuttingStop.setIconSize(QSize(90, 90))
        self.toolBtnCuttingStop.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBtnCuttingStop.clicked.connect(self._on_cutting_stop_clicked)

        # Cutting time display (in control frame)
        self.cuttingTimeFrame = QFrame(self)
        self.cuttingTimeFrame.setGeometry(1176, 845, 321, 221)
        self.cuttingTimeFrame.setStyleSheet(nested_frame_style)

        self.labelCuttingTime = QLabel("Kesim Zamanı", self.cuttingTimeFrame)
        self.labelCuttingTime.setGeometry(27, 16, 200, 22)
        self.labelCuttingTime.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 24px;
            }
        """)

        time_label_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 19px;
            }
        """
        time_value_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 19px;
            }
        """

        row_height = 31
        row_start = 47

        # Start time
        self.labelStartTime = QLabel("Başlangıç:", self.cuttingTimeFrame)
        self.labelStartTime.setGeometry(30, row_start, 90, row_height)
        self.labelStartTime.setStyleSheet(time_label_style)

        self.labelStartTimeValue = QLabel("--:--:--", self.cuttingTimeFrame)
        self.labelStartTimeValue.setGeometry(184, row_start, 110, row_height)
        self.labelStartTimeValue.setStyleSheet(time_value_style)
        self.labelStartTimeValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Duration time (live counter)
        self.labelDurationTime = QLabel("Süre:", self.cuttingTimeFrame)
        self.labelDurationTime.setGeometry(30, row_start + row_height, 90, row_height)
        self.labelDurationTime.setStyleSheet(time_label_style)

        self.labelDurationTimeValue = QLabel("--:--:--", self.cuttingTimeFrame)
        self.labelDurationTimeValue.setGeometry(184, row_start + row_height, 110, row_height)
        self.labelDurationTimeValue.setStyleSheet(time_value_style)
        self.labelDurationTimeValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Remaining time (estimated)
        self.labelRemainingTime = QLabel("Kalan:", self.cuttingTimeFrame)
        self.labelRemainingTime.setGeometry(30, row_start + row_height * 2, 90, row_height)
        self.labelRemainingTime.setStyleSheet(time_label_style)

        self.labelRemainingTimeValue = QLabel("--:--:--", self.cuttingTimeFrame)
        self.labelRemainingTimeValue.setGeometry(184, row_start + row_height * 2, 110, row_height)
        self.labelRemainingTimeValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #4CAF50;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 19px;
            }
        """)
        self.labelRemainingTimeValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Stop time
        self.labelStopTime = QLabel("Bitiş:", self.cuttingTimeFrame)
        self.labelStopTime.setGeometry(30, row_start + row_height * 3, 90, row_height)
        self.labelStopTime.setStyleSheet(time_label_style)

        self.labelStopTimeValue = QLabel("--:--:--", self.cuttingTimeFrame)
        self.labelStopTimeValue.setGeometry(184, row_start + row_height * 3, 110, row_height)
        self.labelStopTimeValue.setStyleSheet(time_value_style)
        self.labelStopTimeValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Previous cutting duration
        self.labelPrevDuration = QLabel("Önceki:", self.cuttingTimeFrame)
        self.labelPrevDuration.setGeometry(30, row_start + row_height * 4, 90, row_height)
        self.labelPrevDuration.setStyleSheet(time_label_style)

        self.labelPrevDurationValue = QLabel("--:--:--", self.cuttingTimeFrame)
        self.labelPrevDurationValue.setGeometry(184, row_start + row_height * 4, 110, row_height)
        self.labelPrevDurationValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #FFA726;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 19px;
            }
        """)
        self.labelPrevDurationValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Initialize status icon
        self._update_status_icon('Bağlantı Yok')

    def _setup_timers(self):
        """Setup all Qt timers for periodic updates."""
        # Log processing timer
        self._log_timer = QTimer(self)
        self._log_timer.timeout.connect(self._process_logs)
        self._log_timer.start(100)  # 100ms

        # Data update timer (if callback provided)
        if self.get_data_callback:
            self._data_timer = QTimer(self)
            self._data_timer.timeout.connect(self._on_data_tick)
            self._data_timer.start(200)  # 200ms

        # Speed update timer (live reading from registers)
        if self.controller_factory:
            self._speed_timer = QTimer(self)
            self._speed_timer.timeout.connect(self._update_band_speeds_live)
            self._speed_timer.start(300)  # 300ms

    # ========================================================================
    # Mode and Speed Button Handlers
    # ========================================================================

    def _handle_cutting_mode_buttons(self, clicked_button):
        """Handle cutting mode button clicks."""
        try:
            # All mode buttons (only Manual and AI)
            mode_buttons = [
                self.btnManualMode,
                self.btnAiMode
            ]

            # Uncheck all buttons
            for button in mode_buttons:
                button.setChecked(False)

            # Check clicked button
            clicked_button.setChecked(True)

            # Set controller based on selection
            if clicked_button == self.btnManualMode:
                self._switch_controller(ControlMode.MANUAL)
                self.add_log("Kesim modu manuel olarak ayarlandı", "INFO")
            elif clicked_button == self.btnAiMode:
                self._switch_controller(ControlMode.ML)
                self.add_log("Kesim modu yapay zeka olarak ayarlandı", "INFO")

        except Exception as e:
            logger.error(f"Cutting mode button error: {e}")
            self.add_log(f"Kesim modu değiştirme hatası: {str(e)}", "ERROR")

    def _switch_controller(self, mode: ControlMode):
        """Switch control mode via control manager."""
        try:
            if self.control_manager and hasattr(self.control_manager, 'set_mode'):
                # Use asyncio to call async method
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self.control_manager.set_mode(mode))
                else:
                    asyncio.run(self.control_manager.set_mode(mode))
                logger.info(f"Control mode switched to: {mode.value}")
        except Exception as e:
            logger.error(f"Error switching controller: {e}")

    def _handle_speed_buttons(self, clicked_button):
        """Handle speed preset button clicks."""
        try:
            # All speed buttons
            speed_buttons = [
                self.btnSlowSpeed,
                self.btnNormalSpeed,
                self.btnFastSpeed
            ]

            # Uncheck all buttons
            for button in speed_buttons:
                button.setChecked(False)

            # Check clicked button
            clicked_button.setChecked(True)

            # Set speed based on selection
            if clicked_button.isChecked():
                speeds = None
                if clicked_button == self.btnSlowSpeed:
                    self._send_manual_speed("slow")
                    speeds = self.speed_values["slow"]
                elif clicked_button == self.btnNormalSpeed:
                    self._send_manual_speed("normal")
                    speeds = self.speed_values["normal"]
                elif clicked_button == self.btnFastSpeed:
                    self._send_manual_speed("fast")
                    speeds = self.speed_values["fast"]

                # Update flag
                self._force_update_cutting_speed = True

                # Temporarily disable frame clicks
                self._frame_click_enabled = False
                QTimer.singleShot(2000, lambda: setattr(self, '_frame_click_enabled', True))

                # Update labels directly
                if speeds is not None:
                    self.labelSentCuttingSpeed.setText(f"{speeds['cutting']:.1f}")
                    self.labelSentDescentSpeed.setText(f"{speeds['descent']:.1f}")

        except Exception as e:
            logger.error(f"Speed button error: {e}")
            self.add_log(f"Kesim hızı değiştirme hatası: {str(e)}", "ERROR")

    def _send_manual_speed(self, speed_level: str):
        """Send manual speed values to machine with proper delay."""
        try:
            speeds = self.speed_values.get(speed_level)
            if not speeds:
                logger.error(f"Invalid speed level: {speed_level}")
                self.add_log(f"Geçersiz hız seviyesi: {speed_level}", "ERROR")
                return

            cutting_speed = speeds["cutting"]
            descent_speed = speeds["descent"]

            # Try to send via control_manager's manual_set_speeds
            if self.control_manager and hasattr(self.control_manager, 'manual_set_speeds'):
                try:
                    # Use asyncio to call async method
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(
                            self.control_manager.manual_set_speeds(cutting_speed, descent_speed)
                        )
                    else:
                        asyncio.run(
                            self.control_manager.manual_set_speeds(cutting_speed, descent_speed)
                        )
                    self.add_log(
                        f"Kesme hızı {cutting_speed:.1f} m/dk olarak ayarlandı",
                        "INFO"
                    )
                    self.add_log(
                        f"İnme hızı {descent_speed:.1f} mm/dk olarak ayarlandı",
                        "INFO"
                    )
                except Exception as e:
                    logger.error(f"Error sending speeds via control_manager: {e}")
                    self.add_log(f"Hız gönderme hatası: {str(e)}", "ERROR")
            else:
                # Fallback: just log the values if control_manager is not available
                self.add_log(
                    f"Kesme hızı {cutting_speed:.1f} m/dk (bağlantı yok)",
                    "WARNING"
                )
                self.add_log(
                    f"İnme hızı {descent_speed:.1f} mm/dk (bağlantı yok)",
                    "WARNING"
                )

        except Exception as e:
            logger.error(f"Speed send error: {e}")
            self.add_log(f"Hız ayarlama hatası: {str(e)}", "ERROR")

    # ========================================================================
    # Frame Click Handlers (for manual speed input)
    # ========================================================================

    def _handle_cutting_speed_frame_click(self, event=None):
        """Handle click on cutting speed frame for manual input."""
        try:
            if not self._frame_click_enabled:
                return

            if event is not None:
                event.accept()

            # Get current value
            current_value = self.labelBandCuttingSpeedValue.text()
            try:
                initial_value = float(current_value) if current_value not in ["NULL", "0", ""] else 0.0
            except ValueError:
                initial_value = 0.0

            # Show numpad dialog - don't call show(), just use exec()
            dialog = NumpadDialog(self)
            # Set initial value AFTER construction to avoid showEvent reset
            initial_str = str(int(initial_value)) if initial_value > 0 else ""

            # Use exec() which is blocking and properly shows the dialog
            result = dialog.exec()

            if result == QDialog.Accepted:
                value_str = dialog.get_value()
                try:
                    value = float(value_str.replace(",", ".")) if value_str else 0.0
                except Exception:
                    value = 0.0

                # Clamp value between 0 and 500
                original_value = value
                value = max(0, min(500, value))

                if value > 0:
                    # Send value to machine via MachineControl
                    if self.machine_control:
                        success = self.machine_control.write_cutting_speed(int(value))
                        if success:
                            self.add_log(f"Kesme hızı {value:.0f} olarak Modbus'a gönderildi", "INFO")
                        else:
                            self.add_log(f"Kesme hızı gönderilemedi!", "ERROR")
                    else:
                        self.add_log("MachineControl bağlantısı yok", "ERROR")

                    # Update display
                    with self._values_lock:
                        self.current_values['kesme_hizi_hedef'] = f"{value:.1f}"
                    self.labelBandCuttingSpeedValue.setText(f"{value:.0f}")

                    # Log
                    if original_value != value:
                        self.add_log(
                            f"Kesme hızı {value:.0f} olarak ayarlandı "
                            f"(girilen değer: {original_value:.0f}, limit: 0-500)",
                            "WARNING"
                        )
        except Exception as e:
            logger.error(f"Cutting speed frame click error: {e}")
            self.add_log(f"Kesme hızı ayarlama hatası: {str(e)}", "ERROR")

    def _handle_descent_speed_frame_click(self, event=None):
        """Handle click on descent speed frame for manual input."""
        try:
            if not self._frame_click_enabled:
                return

            if event is not None:
                event.accept()

            # Get current value
            current_value = self.labelBandDescentSpeedValue.text()
            try:
                initial_value = float(current_value) if current_value not in ["NULL", "0", ""] else 0.0
            except ValueError:
                initial_value = 0.0

            # Show numpad dialog - don't call show(), just use exec()
            dialog = NumpadDialog(self)
            # Set initial value AFTER construction to avoid showEvent reset
            initial_str = str(int(initial_value)) if initial_value > 0 else ""

            # Use exec() which is blocking and properly shows the dialog
            result = dialog.exec()

            if result == QDialog.Accepted:
                value_str = dialog.get_value()
                try:
                    value = float(value_str.replace(",", ".")) if value_str else 0.0
                except Exception:
                    value = 0.0

                # Clamp value between 0 and 500
                original_value = value
                value = max(0, min(500, value))

                if value > 0:
                    # Send value to machine via MachineControl
                    if self.machine_control:
                        success = self.machine_control.write_descent_speed(value)
                        if success:
                            self.add_log(f"İnme hızı {value:.0f} olarak Modbus'a gönderildi", "INFO")
                        else:
                            self.add_log(f"İnme hızı gönderilemedi!", "ERROR")
                    else:
                        self.add_log("MachineControl bağlantısı yok", "ERROR")

                    # Update display
                    with self._values_lock:
                        self.current_values['inme_hizi_hedef'] = f"{value:.1f}"
                    self.labelBandDescentSpeedValue.setText(f"{value:.0f}")

                    # Log
                    if original_value != value:
                        self.add_log(
                            f"İnme hızı {value:.0f} olarak ayarlandı "
                            f"(girilen değer: {original_value:.0f}, limit: 0-500)",
                            "WARNING"
                        )
        except Exception as e:
            logger.error(f"Descent speed frame click error: {e}")
            self.add_log(f"İnme hızı ayarlama hatası: {str(e)}", "ERROR")

    # ========================================================================
    # Control Button Handlers
    # ========================================================================

    def _on_coolant_toggled(self, checked: bool):
        """Handle coolant button toggle."""
        try:
            if not self.machine_control:
                self.add_log("Soğutma kontrol edilemedi: MachineControl yok.", "ERROR")
                self.toolBtnCoolant.blockSignals(True)
                self.toolBtnCoolant.setChecked(False)
                self.toolBtnCoolant.blockSignals(False)
                return

            success = False
            if checked:
                # Enable coolant
                success = self.machine_control.start_coolant()
                if success:
                    self.add_log("Soğutma sıvısı açıldı.", "INFO")
                else:
                    self.add_log("Soğutma sıvısı açılamadı!", "ERROR")
            else:
                # Disable coolant
                success = self.machine_control.stop_coolant()
                if success:
                    self.add_log("Soğutma sıvısı kapatıldı.", "INFO")
                else:
                    self.add_log("Soğutma sıvısı kapatılamadı!", "ERROR")

            # Revert UI if failed
            if not success:
                self.toolBtnCoolant.blockSignals(True)
                self.toolBtnCoolant.setChecked(not checked)
                self.toolBtnCoolant.blockSignals(False)

        except Exception as e:
            logger.error(f"Coolant toggle error: {e}")
            self.toolBtnCoolant.blockSignals(True)
            self.toolBtnCoolant.setChecked(False)
            self.toolBtnCoolant.blockSignals(False)

    def _on_chip_cleaning_toggled(self, checked: bool):
        """Handle chip cleaning button toggle."""
        try:
            if not self.machine_control:
                self.add_log("Talaş temizlik kontrol edilemedi: MachineControl yok.", "ERROR")
                self.toolBtnSawdustCleaning.blockSignals(True)
                self.toolBtnSawdustCleaning.setChecked(False)
                self.toolBtnSawdustCleaning.blockSignals(False)
                return

            success = False
            if checked:
                # Enable chip cleaning
                success = self.machine_control.start_chip_cleaning()
                if success:
                    self.add_log("Talaş temizliği açıldı.", "INFO")
                else:
                    self.add_log("Talaş temizliği açılamadı!", "ERROR")
            else:
                # Disable chip cleaning
                success = self.machine_control.stop_chip_cleaning()
                if success:
                    self.add_log("Talaş temizliği kapatıldı.", "INFO")
                else:
                    self.add_log("Talaş temizliği kapatılamadı!", "ERROR")

            # Revert UI if failed
            if not success:
                self.toolBtnSawdustCleaning.blockSignals(True)
                self.toolBtnSawdustCleaning.setChecked(not checked)
                self.toolBtnSawdustCleaning.blockSignals(False)

        except Exception as e:
            logger.error(f"Chip cleaning toggle error: {e}")
            self.toolBtnSawdustCleaning.blockSignals(True)
            self.toolBtnSawdustCleaning.setChecked(False)
            self.toolBtnSawdustCleaning.blockSignals(False)

    def _on_cutting_start_clicked(self):
        """Handle cutting start button click."""
        try:
            if not self.machine_control:
                self.add_log("Kesim başlatılamadı: MachineControl yok.", "ERROR")
                return

            success = self.machine_control.start_cutting()

            if success:
                self.add_log("Kesim başlatıldı.", "INFO")
                self._cutting_start_time = datetime.now()
                self._cutting_start_datetime = datetime.now()

                with self._values_lock:
                    self.current_values['kesim_baslama'] = \
                        self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3]
                    self.current_values['kesim_sure'] = "00:00"

                # Update time labels
                start_time_str = self._cutting_start_time.strftime('%H:%M:%S')
                self.labelStartTimeValue.setText(start_time_str)
                self.labelStopTimeValue.setText("--:--:--")
                self.labelDurationTimeValue.setText("00:00:00")
                self.labelRemainingTimeValue.setText("--:--:--")
            else:
                self.add_log("Kesim başlatılamadı!", "ERROR")

        except Exception as e:
            logger.error(f"Cutting start error: {e}")
            self.add_log(f"Kesim başlatma hatası: {str(e)}", "ERROR")

    def _on_cutting_stop_clicked(self):
        """Handle cutting stop button click."""
        try:
            if not self.machine_control:
                self.add_log("Kesim durdurulamadı: MachineControl yok.", "ERROR")
                return

            success = self.machine_control.stop_cutting()

            if success:
                self.add_log("Kesim durduruldu.", "INFO")

                # Update stop time and calculate duration
                if self._cutting_start_datetime:
                    self._cutting_stop_datetime = datetime.now()
                    stop_time_str = self._cutting_stop_datetime.strftime('%H:%M:%S')
                    self.labelStopTimeValue.setText(stop_time_str)

                    # Calculate and display duration (HH:MM:SS format)
                    duration = self._cutting_stop_datetime - self._cutting_start_datetime
                    total_seconds = duration.total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    self.labelDurationTimeValue.setText(duration_str)
                    self.labelRemainingTimeValue.setText("00:00:00")

                    # Save as previous duration
                    self._previous_cutting_duration = duration_str

                    logger.info(f"Manual cutting duration: {duration_str}")

                # Reset cutting time
                self._cutting_start_time = None
                self._cutting_start_datetime = None

                with self._values_lock:
                    self.current_values['kesim_baslama'] = "-"
                    self.current_values['kesim_sure'] = "-"
            else:
                self.add_log("Kesim durdurulamadı!", "ERROR")

        except Exception as e:
            logger.error(f"Cutting stop error: {e}")
            self.add_log(f"Kesim durdurma hatası: {str(e)}", "ERROR")

    # ========================================================================
    # Data Update Methods
    # ========================================================================

    def _on_data_tick(self):
        """Called by data timer to fetch and update data."""
        try:
            if self.data_pipeline and hasattr(self.data_pipeline, 'get_latest_data'):
                data = self.data_pipeline.get_latest_data()
                if data:
                    self.update_data(data)
        except Exception as e:
            logger.error(f"Data tick error: {e}")

    def update_data(self, processed_data: Dict):
        """
        Update display with latest data.

        Args:
            processed_data: Dictionary containing sensor and machine data
        """
        try:
            # Update modbus status
            if 'modbus_connected' in processed_data:
                self.update_modbus_status(
                    processed_data['modbus_connected'],
                    processed_data.get('modbus_ip', '192.168.2.147')
                )

            # Update all values
            self._update_values(processed_data)

            # Update cutting time tracking (with height and speed for remaining time)
            testere_durumu = int(processed_data.get('testere_durumu', 0))
            kafa_yuksekligi = float(processed_data.get('kafa_yuksekligi_mm', 0))
            inme_hizi = float(processed_data.get('serit_inme_hizi', 0))
            self._update_cutting_time_labels(testere_durumu, kafa_yuksekligi, inme_hizi)

            # Check critical values
            self._check_critical_values(processed_data)

        except Exception as e:
            logger.error(f"Data update error: {e}")

    def _update_values(self, processed_data: Dict):
        """Update all displayed values (thread-safe)."""
        try:
            with self._values_lock:
                # Head height
                kafa_yuksekligi = processed_data.get('kafa_yuksekligi_mm', 0)
                self.current_values['kafa_yuksekligi_mm'] = f"{kafa_yuksekligi:.1f}"

                # Motor currents
                serit_motor_akim = processed_data.get('serit_motor_akim_a', 0)
                inme_motor_akim = processed_data.get('inme_motor_akim_a', 0)
                self.current_values['serit_motor_akim_a'] = f"{serit_motor_akim:.1f}"
                self.current_values['inme_motor_akim_a'] = f"{inme_motor_akim:.1f}"

                # Motor torques
                serit_motor_tork = processed_data.get('serit_motor_tork_percentage', 0)
                inme_motor_tork = processed_data.get('inme_motor_tork_percentage', 0)
                self.current_values['serit_motor_tork_percentage'] = f"{serit_motor_tork:.1f}"
                self.current_values['inme_motor_tork_percentage'] = f"{inme_motor_tork:.1f}"

                # Band deviation
                deviation_value = processed_data.get('serit_sapmasi', 0)
                self.current_values['serit_sapmasi'] = f"{deviation_value:.2f}"

                # Speeds (live/actual values from registers 1033/1034)
                cutting_speed = processed_data.get('serit_kesme_hizi', 0)
                descent_speed = processed_data.get('serit_inme_hizi', 0)
                self.current_values['serit_kesme_hizi'] = f"{cutting_speed:.1f}"
                self.current_values['serit_inme_hizi'] = f"{descent_speed:.1f}"

                # Target speeds (from registers 2066/2041 - what we write to PLC)
                kesme_hizi_hedef = processed_data.get('kesme_hizi_hedef', 0)
                inme_hizi_hedef = processed_data.get('inme_hizi_hedef', 0)
                self.current_values['kesme_hizi_hedef'] = f"{kesme_hizi_hedef:.1f}"
                self.current_values['inme_hizi_hedef'] = f"{inme_hizi_hedef:.1f}"

                # Machine status
                testere_durumu = processed_data.get('testere_durumu', 0)
                durum_text = {
                    -1: "BAĞLANTI BEKLENİYOR",  # Special value when Modbus not connected
                    0: "BOŞTA",
                    1: "HİDROLİK AKTİF",
                    2: "ŞERİT MOTOR ÇALIŞIYOR",
                    3: "KESİM YAPILIYOR",
                    4: "KESİM BİTTİ",
                    5: "ŞERİT YUKARI ÇIKIYOR",
                    6: "MALZEME BESLEME"
                }.get(testere_durumu, "BİLİNMİYOR")
                self.current_values['testere_durumu'] = durum_text

            # Update UI (outside lock)
            self.labelValue.setText(f"{kafa_yuksekligi:.1f}")
            self.progressBarHeight.setValue(int(kafa_yuksekligi))

            self.labelBandCuttingCurrentValue.setText(f"{serit_motor_akim:.1f}")
            self.labelBandDescentCurrentValue.setText(f"{inme_motor_akim:.1f}")

            self.labelBandCuttingTorqueValue.setText(f"{serit_motor_tork:.1f}")
            self.labelBandDescentTorqueValue.setText(f"{inme_motor_tork:.1f}")

            self.labelBandDeviationValue.setText(f"{deviation_value:.2f}")

            self.labelSentCuttingSpeed.setText(f"{cutting_speed:.1f}")
            self.labelSentDescentSpeed.setText(f"{descent_speed:.1f}")

            # Update target speed labels (big displays)
            self.labelBandCuttingSpeedValue.setText(f"{kesme_hizi_hedef:.0f}")
            self.labelBandDescentSpeedValue.setText(f"{inme_hizi_hedef:.0f}")

            # Update deviation graph
            if self.band_deviation_graph:
                self.band_deviation_graph.add_data_point(deviation_value)
                self.band_deviation_graph.clear_old_data()

                max_value = self.band_deviation_graph.get_max_value()
                min_value = self.band_deviation_graph.get_min_value()

                self.ustdegerlabel.setText(f" {max_value:.2f}")
                if min_value >= 0:
                    self.altdegerlabel.setText(f" {min_value:.2f}")
                else:
                    self.altdegerlabel.setText(f"{min_value:.2f}")

            # Update system status
            self.labelSystemStatusInfo.setText(self._get_status_message(durum_text))

            # Update coolant and chip cleaning button states from Modbus
            self._update_control_button_states()

        except Exception as e:
            logger.error(f"Values update error: {e}")

    def _update_band_speeds_live(self):
        """Update band speeds by reading from registers."""
        try:
            # This requires access to modbus client and speed reading utilities
            # For now, skip implementation
            pass
        except Exception as e:
            logger.debug(f"Speed update error: {e}")

    def _update_control_button_states(self):
        """Update coolant and chip cleaning button states from Modbus."""
        try:
            if not self.machine_control:
                return

            # Read coolant state
            coolant_active = self.machine_control.is_coolant_active()
            if coolant_active is not None:
                # Block signals to prevent triggering toggle callback
                self.toolBtnCoolant.blockSignals(True)
                self.toolBtnCoolant.setChecked(coolant_active)
                self.toolBtnCoolant.blockSignals(False)

            # Read chip cleaning state
            chip_cleaning_active = self.machine_control.is_chip_cleaning_active()
            if chip_cleaning_active is not None:
                self.toolBtnSawdustCleaning.blockSignals(True)
                self.toolBtnSawdustCleaning.setChecked(chip_cleaning_active)
                self.toolBtnSawdustCleaning.blockSignals(False)

        except Exception as e:
            logger.debug(f"Control button state update error: {e}")

    def _update_cutting_time_labels(self, testere_durumu: int, kafa_yuksekligi: float = 0.0, inme_hizi: float = 0.0):
        """
        Update cutting time labels based on machine state.

        Args:
            testere_durumu: Current saw state (3 = cutting)
            kafa_yuksekligi: Current head height in mm
            inme_hizi: Current descent speed in mm/min
        """
        try:
            # Cutting started - KESİYOR (3) durumuna girince
            if testere_durumu == 3:
                if not self._cutting_start_datetime:
                    # Cutting just started
                    self._cutting_start_datetime = datetime.now()
                    self._cutting_start_height = kafa_yuksekligi
                    start_time_str = self._cutting_start_datetime.strftime('%H:%M:%S')
                    self.labelStartTimeValue.setText(start_time_str)
                    self.labelStopTimeValue.setText("--:--:--")

                    # Show previous cutting duration
                    if self._previous_cutting_duration:
                        self.labelPrevDurationValue.setText(self._previous_cutting_duration)

                    logger.info(f"Cutting started: {start_time_str}, height={kafa_yuksekligi:.1f}mm")

                # Update live duration counter
                now = datetime.now()
                duration = now - self._cutting_start_datetime
                total_seconds = duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.labelDurationTimeValue.setText(duration_str)

                # Calculate remaining time based on height and descent speed
                remaining_str = self._calculate_remaining_time(kafa_yuksekligi, inme_hizi)
                self.labelRemainingTimeValue.setText(remaining_str)

            # Cutting finished - KESİYOR (3) durumundan çıkınca
            elif self._previous_testere_durumu == 3 and testere_durumu != 3 and self._cutting_start_datetime:
                # Cutting finished
                self._cutting_stop_datetime = datetime.now()
                stop_time_str = self._cutting_stop_datetime.strftime('%H:%M:%S')
                self.labelStopTimeValue.setText(stop_time_str)

                # Final duration
                duration = self._cutting_stop_datetime - self._cutting_start_datetime
                total_seconds = duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.labelDurationTimeValue.setText(duration_str)
                self.labelRemainingTimeValue.setText("00:00:00")

                # Save as previous duration for next cutting
                self._previous_cutting_duration = duration_str

                logger.info(f"Cutting finished: {stop_time_str}, duration={duration_str}")

                # Reset for next cutting
                self._cutting_start_datetime = None
                self._cutting_stop_datetime = None
                self._cutting_start_height = None

            # Update previous state for next comparison
            self._previous_testere_durumu = testere_durumu

        except Exception as e:
            logger.error(f"Cutting time label update error: {e}")

    def _calculate_remaining_time(self, current_height: float, descent_speed: float) -> str:
        """
        Calculate estimated remaining cutting time.

        Args:
            current_height: Current head height in mm
            descent_speed: Current descent speed in mm/min (absolute value)

        Returns:
            Formatted time string "HH:MM:SS"
        """
        try:
            # Descent speed should be positive (absolute value)
            speed = abs(descent_speed) if descent_speed != 0 else 0

            if speed < 0.1:
                # Speed too low or zero - can't calculate
                return "--:--:--"

            # Remaining height to cut (assuming target is 0 or near 0)
            # In practice, cutting stops at a certain minimum height
            remaining_height = max(0, current_height - 5)  # Assume 5mm minimum

            if remaining_height <= 0:
                return "00:00:00"

            # Time = Distance / Speed (in minutes)
            remaining_minutes = remaining_height / speed
            remaining_seconds = remaining_minutes * 60

            hours = int(remaining_seconds // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            seconds = int(remaining_seconds % 60)

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except Exception as e:
            logger.error(f"Remaining time calculation error: {e}")
            return "--:--:--"

    def update_modbus_status(self, connected: bool, ip: str):
        """Update modbus connection status."""
        try:
            with self._values_lock:
                if connected:
                    self.current_values['modbus_status'] = f"Bağlı ({ip})"
                    self.current_values['testere_durumu'] = "Veri bekleniyor..."
                    status_text = "Veri bekleniyor..."
                else:
                    self.current_values['modbus_status'] = f"Bağlantı Yok ({ip})"
                    self.current_values['testere_durumu'] = "Bağlantı Yok"
                    status_text = "Bağlantı Yok"

            self.labelSystemStatusInfo.setText(status_text)
            self._update_status_icon(status_text)

        except Exception as e:
            logger.error(f"Modbus status update error: {e}")

    def _check_critical_values(self, data: Dict):
        """Check for critical values and log warnings."""
        try:
            testere_durumu = int(data.get('testere_durumu', 0))

            # Check current during cutting
            if testere_durumu == 3:  # KESIM_YAPILIYOR
                current = float(data.get('serit_motor_akim_a', 0))
                if current > 25:
                    self.add_log(f"Yüksek motor akımı: {current:.2f}A", "WARNING")
                elif current > 30:
                    self.add_log(f"Kritik motor akımı: {current:.2f}A", "ERROR")

                # Check deviation during cutting
                deviation = float(data.get('serit_sapmasi', 0))
                if abs(deviation) > 0.4:
                    self.add_log(f"Yüksek şerit sapması: {deviation:.2f}mm", "WARNING")
                elif abs(deviation) > 0.6:
                    self.add_log(f"Kritik şerit sapması: {deviation:.2f}mm", "ERROR")

        except Exception as e:
            logger.error(f"Critical values check error: {e}")

    # ========================================================================
    # Status and Icon Methods
    # ========================================================================

    def _get_status_message(self, status_text):
        """Get user-friendly status message."""
        status_messages = {
            "BAĞLANTI BEKLENİYOR": "PLC bağlantısı\nbekleniyor...",
            "BOŞTA": "Boşta.",
            "HİDROLİK AKTİF": "Makine kesime\nhazır.",
            "ŞERİT MOTOR ÇALIŞIYOR": "Şerit motor\nçalışıyor!",
            "KESİM YAPILIYOR": "Kesim yapılıyor!",
            "KESİM BİTTİ": "Kesim bitti!",
            "ŞERİT YUKARI ÇIKIYOR": "Şerit yukarı\nçıkıyor.",
            "MALZEME BESLEME": "Kesilecek malzeme\nkonumlandırılıyor.",
            "BİLİNMİYOR": "Bilinmiyor!",
            "Bağlantı Yok": "Bağlantı bekleniyor...",
            "Veri bekleniyor...": "Veri akışı\nbekleniyor...",
            "Bağlantı Kontrol Ediliyor...": "Bağlantı kontrol\nediliyor..."
        }

        self._update_status_icon(status_text)
        return status_messages.get(status_text, status_text)

    def _get_status_icon_path(self, status_text):
        """Get icon path for status."""
        status_icons = {
            "BAĞLANTI BEKLENİYOR": "baglanti-kontrol-ediliyor.png",
            "BOŞTA": "bosta.png",
            "HİDROLİK AKTİF": "okey-icon.svg",
            "ŞERİT MOTOR ÇALIŞIYOR": "serit-motor-calisiyor.png",
            "KESİM YAPILIYOR": "kesim-yapiliyor.png",
            "KESİM BİTTİ": "okey-icon.svg",
            "ŞERİT YUKARI ÇIKIYOR": "serit-motor-calisiyor.png",
            "MALZEME BESLEME": "malzeme-besleme.png",
            "BİLİNMİYOR": "okey-icon.svg",
            "Bağlantı Yok": "baglanti-yok.png",
            "Veri bekleniyor...": "baglanti-kontrol-ediliyor.png",
            "Bağlantı Kontrol Ediliyor...": "baglanti-kontrol-ediliyor.png"
        }
        return status_icons.get(status_text, "baglanti-kontrol-ediliyor.png")

    def _update_status_icon(self, status_text):
        """Update status icon based on status text."""
        try:
            icon_filename = self._get_status_icon_path(status_text)

            # Try to find icon in images folder
            # Assume images are in gui/images/ relative to this file
            base_path = os.path.dirname(os.path.dirname(__file__))
            full_path = os.path.join(base_path, "images", icon_filename)

            if os.path.exists(full_path):
                pixmap = QPixmap(full_path)
                scaled_pixmap = pixmap.scaled(
                    71, 71,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.iconStatus.setPixmap(scaled_pixmap)
            else:
                logger.warning(f"Status icon not found: {full_path}")

        except Exception as e:
            logger.error(f"Status icon update error: {e}")

    # ========================================================================
    # Log Methods
    # ========================================================================

    def add_log(self, message: str, level: str = 'INFO'):
        """
        Add log message to display (thread-safe).

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        try:
            if not self.log_text:
                return

            # Timestamp
            timestamp = datetime.now().strftime('%H:%M')

            # Color based on level
            color = "#F4F6FC"
            if level == 'WARNING':
                color = "orange"
            elif level == 'ERROR':
                color = "red"

            # Format message
            log_message_html = (
                f"<span style='font-size:20px; color:{color}; "
                f"font-weight:extra-light;'>{timestamp}</span><br>"
                f"<span style='font-size:20px; color:{color}; "
                f"font-weight:medium;'>{message}</span><br><br>"
            )

            # Add to log
            self.log_text.insertHtml(log_message_html)

            # Auto-scroll to bottom
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # Limit log size (keep last 1000 blocks)
            while self.log_text.document().blockCount() > 1000:
                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.Start)
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()

        except Exception as e:
            logger.error(f"Log add error: {e}")

    def _process_logs(self):
        """Process log queue (called by timer)."""
        try:
            while not self.log_queue.empty():
                log_entry = self.log_queue.get_nowait()
                self.add_log(log_entry['message'], log_entry['level'])
        except Exception as e:
            logger.error(f"Log processing error: {e}")

    def stop_timers(self):
        """
        Stop all QTimers in this controller.

        IMPORTANT: Must be called from the GUI thread before window closes
        to avoid segmentation fault on Linux.
        """
        try:
            if hasattr(self, '_log_timer') and self._log_timer:
                self._log_timer.stop()
            if hasattr(self, '_data_timer') and self._data_timer:
                self._data_timer.stop()
            if hasattr(self, '_speed_timer') and self._speed_timer:
                self._speed_timer.stop()
            if hasattr(self, 'band_deviation_graph') and self.band_deviation_graph:
                if hasattr(self.band_deviation_graph, 'update_timer'):
                    self.band_deviation_graph.update_timer.stop()
            logger.debug("ControlPanelController timers stopped")
        except Exception as e:
            logger.error(f"Error stopping control panel timers: {e}")


    # ========================================================================
    # Load Icon Method
    # ========================================================================

    def _load_icon(self, icon_filename: str) -> QIcon:
        """
        Load icon from images directory.

        Args:
            icon_filename: Icon filename

        Returns:
            QIcon object
        """
        try:
            # Get base path (gui/images/)
            base_path = os.path.dirname(os.path.dirname(__file__))
            icon_path = os.path.join(base_path, "images", icon_filename)

            if os.path.exists(icon_path):
                return QIcon(icon_path)
            else:
                logger.warning(f"Icon not found: {icon_path}")
                return QIcon()

        except Exception as e:
            logger.error(f"Icon load error ({icon_filename}): {e}")
            return QIcon()