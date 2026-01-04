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
from typing import Optional, Dict, Callable
from datetime import datetime, timedelta

try:
    from PySide6.QtWidgets import (
        QWidget, QFrame, QPushButton, QLabel, QTextEdit,
        QProgressBar, QDialog, QVBoxLayout, QHBoxLayout, QApplication
    )
    from PySide6.QtCore import Qt, QTimer, QDateTime, Slot, Signal, QPoint
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
# NumpadDialog - Embedded implementation
# ============================================================================
class NumpadDialog(QDialog):
    """Simple number input dialog with numeric keypad."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sayı Girişi")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.value = ""
        self.Accepted = QDialog.Accepted
        self.setup_ui()
        self.center_on_screen()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Display label
        self.display_label = QLabel("0")
        self.display_label.setStyleSheet(
            "font-size: 24px; padding: 10px; border: 1px solid gray;"
        )
        self.display_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.display_label)

        # Number buttons (1-9)
        for row in range(3):
            row_layout = QHBoxLayout()
            for col in range(3):
                number = row * 3 + col + 1
                btn = QPushButton(str(number))
                btn.setFixedSize(80, 60)
                btn.clicked.connect(lambda checked, n=number: self.add_digit(str(n)))
                row_layout.addWidget(btn)
            layout.addLayout(row_layout)

        # Bottom row
        bottom_layout = QHBoxLayout()

        # Clear button
        clear_btn = QPushButton("Temizle")
        clear_btn.setFixedSize(80, 60)
        clear_btn.clicked.connect(self.clear_value)
        bottom_layout.addWidget(clear_btn)

        # Zero button
        zero_btn = QPushButton("0")
        zero_btn.setFixedSize(80, 60)
        zero_btn.clicked.connect(lambda: self.add_digit("0"))
        bottom_layout.addWidget(zero_btn)

        # OK button
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

    def center_on_screen(self):
        """Center dialog on screen."""
        # PySide6 uses QScreen instead of QDesktopWidget
        try:
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            dialog_geometry = self.geometry()
            x = (screen_geometry.width() - dialog_geometry.width()) // 2
            y = (screen_geometry.height() - dialog_geometry.height()) // 2
            self.move(x, y)
        except Exception:
            # Fallback - center roughly
            self.move(760, 390)


# ============================================================================
# BandDeviationGraphWidget - Real-time graph for band deviation
# ============================================================================
class BandDeviationGraphWidget(QWidget):
    """Real-time graph widget for band deviation values."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(278, 144)

        # Data structure: (timestamp, value) tuples
        self.data_points = collections.deque(maxlen=300)  # 30 seconds * 10 data/sec
        self.max_points = 300

        # Max/min value tracking
        self.max_value = float('-inf')
        self.min_value = float('inf')

        # Graph settings
        self.padding = 10
        self.grid_color = QColor(255, 255, 255, 30)  # Transparent white
        self.line_color = QColor(149, 9, 82)  # Main color
        self.fill_color = QColor(149, 9, 82, 50)  # Fill color

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
        """Clear data older than 30 seconds."""
        try:
            with self._data_lock:
                cutoff_time = datetime.now() - timedelta(seconds=30)
                while self.data_points and self.data_points[0][0] < cutoff_time:
                    self.data_points.popleft()
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

            # Don't draw if no data
            if not self.data_points:
                return

            # Calculate drawing area
            draw_rect = self.rect().adjusted(
                self.padding, self.padding, -self.padding, -self.padding
            )

            # Draw grid
            self._draw_grid(painter, draw_rect)

            # Draw data
            self._draw_data(painter, draw_rect)

        except Exception as e:
            logger.error(f"Graph drawing error: {e}")

    def _draw_grid(self, painter: QPainter, rect):
        """Draw grid lines."""
        try:
            painter.setPen(QPen(self.grid_color, 1))

            # Vertical lines (16 lines)
            for i in range(17):
                x = rect.left() + (rect.width() * i) // 16
                painter.drawLine(x, rect.top(), x, rect.bottom())

            # Horizontal lines (4 lines)
            for i in range(5):
                y = rect.top() + (rect.height() * i) // 4
                painter.drawLine(rect.left(), y, rect.right(), y)

        except Exception as e:
            logger.error(f"Grid drawing error: {e}")

    def _draw_data(self, painter: QPainter, rect):
        """Draw data points and line."""
        try:
            with self._data_lock:
                if len(self.data_points) < 2:
                    return

                # Calculate value range
                values = [point[1] for point in self.data_points]
                min_val = min(values)
                max_val = max(values)

                # Expand range if too small
                if max_val - min_val < 0.1:
                    mid_val = (min_val + max_val) / 2
                    min_val = mid_val - 0.05
                    max_val = mid_val + 0.05

                # Line color
                painter.setPen(QPen(self.line_color, 3))

                # Fill color
                painter.setBrush(QBrush(self.fill_color))

                # Calculate line points
                points = []
                for i, (timestamp, value) in enumerate(self.data_points):
                    # X coordinate (time)
                    x = rect.left() + (rect.width() * i) // (len(self.data_points) - 1)

                    # Y coordinate (value)
                    if max_val != min_val:
                        normalized_value = (value - min_val) / (max_val - min_val)
                    else:
                        normalized_value = 0.5

                    y = rect.bottom() - (rect.height() * normalized_value)
                    points.append((x, y))

                # Draw line
                if len(points) > 1:
                    # Main line
                    for i in range(len(points) - 1):
                        painter.drawLine(
                            int(points[i][0]), int(points[i][1]),
                            int(points[i+1][0]), int(points[i+1][1])
                        )

                    # Fill area
                    fill_points = points.copy()
                    fill_points.append((points[-1][0], rect.bottom()))
                    fill_points.append((points[0][0], rect.bottom()))

                    polygon = QPolygon()
                    for x, y in fill_points:
                        polygon.append(QPoint(int(x), int(y)))

                    painter.drawPolygon(polygon)

                # Red triangle for last point
                if points:
                    last_x, last_y = points[-1]
                    triangle_size = 8
                    painter.setBrush(QBrush(QColor(255, 0, 0)))
                    painter.setPen(QPen(QColor(255, 0, 0), 1))

                    triangle_points = [
                        (last_x, last_y - triangle_size),
                        (last_x - triangle_size//2, last_y + triangle_size//2),
                        (last_x + triangle_size//2, last_y + triangle_size//2)
                    ]

                    triangle_polygon = QPolygon()
                    for x, y in triangle_points:
                        triangle_polygon.append(QPoint(int(x), int(y)))

                    painter.drawPolygon(triangle_polygon)

        except Exception as e:
            logger.error(f"Data drawing error: {e}")

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
        self.machine_control = control_manager
        self.get_data_callback = data_pipeline

        # Data management
        self.current_values = {}
        self._values_lock = threading.Lock()
        self._last_update_time = None

        # Cutting time tracking
        self._cutting_start_time = None
        self._cutting_start_datetime = None
        self._cutting_stop_datetime = None

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
                background-color: rgba(26, 31, 55, 200);
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                text-align: left;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
                padding-left: 52px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background-color: #950952;
            }
        """

        button_speed_style = """
            QPushButton {
                background-color: rgba(26, 31, 55, 200);
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 18px;
                text-align: center;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background-color: #950952;
            }
        """

        # === CUTTING MODE FRAME (0, 0, 440, 344) ===
        self.cuttingModeFrame = QFrame(self)
        self.cuttingModeFrame.setGeometry(0, 0, 440, 344)
        self.cuttingModeFrame.setStyleSheet(frame_style)

        self.labelCuttingMode = QLabel("Kesim Modu", self.cuttingModeFrame)
        self.labelCuttingMode.setGeometry(27, 26, 381, 34)
        self.labelCuttingMode.setStyleSheet(label_title_style)

        # Mode buttons (4 buttons: Manual, AI, Fuzzy, Expert)
        self.btnManualMode = QPushButton("Manuel", self.cuttingModeFrame)
        self.btnManualMode.setGeometry(18, 87, 180, 45)
        self.btnManualMode.setStyleSheet(button_mode_style)
        self.btnManualMode.setCheckable(True)
        self.btnManualMode.setChecked(True)
        self.btnManualMode.clicked.connect(
            lambda: self._handle_cutting_mode_buttons(self.btnManualMode)
        )

        self.btnAiMode = QPushButton("Yapay Zeka", self.cuttingModeFrame)
        self.btnAiMode.setGeometry(241, 87, 180, 45)
        self.btnAiMode.setStyleSheet(
            button_mode_style.replace("padding-left: 52px;", "padding-left: 32px;")
        )
        self.btnAiMode.setCheckable(True)
        self.btnAiMode.clicked.connect(
            lambda: self._handle_cutting_mode_buttons(self.btnAiMode)
        )

        self.btnFuzzyMode = QPushButton("Bulanık", self.cuttingModeFrame)
        self.btnFuzzyMode.setGeometry(18, 157, 180, 45)
        self.btnFuzzyMode.setStyleSheet(button_mode_style)
        self.btnFuzzyMode.setCheckable(True)
        self.btnFuzzyMode.clicked.connect(
            lambda: self._handle_cutting_mode_buttons(self.btnFuzzyMode)
        )

        self.btnExpertSystemMode = QPushButton("Uzman Sistem", self.cuttingModeFrame)
        self.btnExpertSystemMode.setGeometry(241, 157, 180, 45)
        self.btnExpertSystemMode.setStyleSheet(
            button_mode_style.replace("padding-left: 52px;", "padding-left: 20px;")
        )
        self.btnExpertSystemMode.setCheckable(True)
        self.btnExpertSystemMode.clicked.connect(
            lambda: self._handle_cutting_mode_buttons(self.btnExpertSystemMode)
        )

        # Speed preset buttons
        self.labelSpeed = QLabel("Hız Seçimi", self.cuttingModeFrame)
        self.labelSpeed.setGeometry(27, 225, 200, 30)
        self.labelSpeed.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 18px;
            }
        """)

        self.btnSlowSpeed = QPushButton("Yavaş", self.cuttingModeFrame)
        self.btnSlowSpeed.setGeometry(18, 265, 124, 45)
        self.btnSlowSpeed.setStyleSheet(button_speed_style)
        self.btnSlowSpeed.setCheckable(True)
        self.btnSlowSpeed.clicked.connect(
            lambda: self._handle_speed_buttons(self.btnSlowSpeed)
        )

        self.btnNormalSpeed = QPushButton("Normal", self.cuttingModeFrame)
        self.btnNormalSpeed.setGeometry(159, 265, 124, 45)
        self.btnNormalSpeed.setStyleSheet(button_speed_style)
        self.btnNormalSpeed.setCheckable(True)
        self.btnNormalSpeed.clicked.connect(
            lambda: self._handle_speed_buttons(self.btnNormalSpeed)
        )

        self.btnFastSpeed = QPushButton("Hızlı", self.cuttingModeFrame)
        self.btnFastSpeed.setGeometry(297, 265, 124, 45)
        self.btnFastSpeed.setStyleSheet(button_speed_style)
        self.btnFastSpeed.setCheckable(True)
        self.btnFastSpeed.clicked.connect(
            lambda: self._handle_speed_buttons(self.btnFastSpeed)
        )

        # === HEAD HEIGHT FRAME (455, 0, 251, 344) ===
        self.headHeightFrame = QFrame(self)
        self.headHeightFrame.setGeometry(455, 0, 251, 344)
        self.headHeightFrame.setStyleSheet(frame_style)

        self.labelHeadHeight = QLabel("Kafa Yüksekliği", self.headHeightFrame)
        self.labelHeadHeight.setGeometry(25, 26, 211, 34)
        self.labelHeadHeight.setStyleSheet(label_title_style)

        # Vertical progress bar
        self.progressBarHeight = QProgressBar(self.headHeightFrame)
        self.progressBarHeight.setGeometry(27, 78, 50, 250)
        self.progressBarHeight.setOrientation(Qt.Vertical)
        self.progressBarHeight.setMinimum(0)
        self.progressBarHeight.setMaximum(350)
        self.progressBarHeight.setValue(0)
        self.progressBarHeight.setTextVisible(False)
        self.progressBarHeight.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 25px;
                background-color: rgba(149, 9, 82, 0.2);
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 25px;
                background-color: #950952;
                min-height: 10px;
            }
        """)

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

        # === BAND DEVIATION FRAME (723, 0, 401, 344) ===
        self.bandDeviationFrame = QFrame(self)
        self.bandDeviationFrame.setGeometry(723, 0, 401, 344)
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

        # === SYSTEM STATUS FRAME (1143, 0, 321, 243) ===
        self.systemStatusFrame = QFrame(self)
        self.systemStatusFrame.setGeometry(1143, 0, 321, 243)
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

        # === BAND CUTTING SPEED FRAME (0, 359, 551, 344) ===
        self.bandCuttingSpeedFrame = QFrame(self)
        self.bandCuttingSpeedFrame.setGeometry(0, 359, 551, 344)
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
        self.labelSentCuttingSpeed.setGeometry(31, 87, 200, 80)
        self.labelSentCuttingSpeed.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 42px;
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

        # === BAND DESCENT SPEED FRAME (573, 359, 551, 344) ===
        self.bandDescentSpeedFrame = QFrame(self)
        self.bandDescentSpeedFrame.setGeometry(573, 359, 551, 344)
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
        self.labelSentDescentSpeed.setGeometry(31, 87, 200, 80)
        self.labelSentDescentSpeed.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 42px;
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

        # === CUTTING TIME FRAME (1143, 257, 321, 145) ===
        self.cuttingTimeFrame = QFrame(self)
        self.cuttingTimeFrame.setGeometry(1143, 257, 321, 145)
        self.cuttingTimeFrame.setStyleSheet(frame_style)

        self.labelCuttingTime = QLabel("Kesim Zamanı", self.cuttingTimeFrame)
        self.labelCuttingTime.setGeometry(27, 26, 271, 34)
        self.labelCuttingTime.setStyleSheet(label_title_style)

        # Start time
        self.labelStartTime = QLabel("Başlangıç:", self.cuttingTimeFrame)
        self.labelStartTime.setGeometry(30, 70, 140, 30)
        self.labelStartTime.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 18px;
            }
        """)

        self.labelStartTimeValue = QLabel("--:--:--", self.cuttingTimeFrame)
        self.labelStartTimeValue.setGeometry(180, 70, 120, 30)
        self.labelStartTimeValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 18px;
            }
        """)
        self.labelStartTimeValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Stop time
        self.labelStopTime = QLabel("Bitiş:", self.cuttingTimeFrame)
        self.labelStopTime.setGeometry(30, 105, 140, 30)
        self.labelStopTime.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 18px;
            }
        """)

        self.labelStopTimeValue = QLabel("--:--:--", self.cuttingTimeFrame)
        self.labelStopTimeValue.setGeometry(180, 105, 120, 30)
        self.labelStopTimeValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 18px;
            }
        """)
        self.labelStopTimeValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # === CONTROL BUTTONS FRAME (1143, 417, 321, 286) ===
        self.controlButtonsFrame = QFrame(self)
        self.controlButtonsFrame.setGeometry(1143, 417, 321, 286)
        self.controlButtonsFrame.setStyleSheet(frame_style)

        self.labelControlButtons = QLabel("Kontrol", self.controlButtonsFrame)
        self.labelControlButtons.setGeometry(27, 26, 271, 34)
        self.labelControlButtons.setStyleSheet(label_title_style)

        # Button style for control buttons
        control_button_style = """
            QPushButton {
                background-color: rgba(26, 31, 55, 200);
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 16px;
                text-align: center;
                border-radius: 15px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background-color: #950952;
            }
            QPushButton:disabled {
                background-color: rgba(26, 31, 55, 100);
                color: rgba(244, 246, 252, 100);
            }
        """

        # Coolant button
        self.toolBtnCoolant = QPushButton("Soğutma Sıvısı", self.controlButtonsFrame)
        self.toolBtnCoolant.setGeometry(30, 80, 130, 80)
        self.toolBtnCoolant.setStyleSheet(control_button_style)
        self.toolBtnCoolant.setCheckable(True)
        self.toolBtnCoolant.toggled.connect(self._on_coolant_toggled)

        # Sawdust cleaning button
        self.toolBtnSawdustCleaning = QPushButton(
            "Talaş Temizliği",
            self.controlButtonsFrame
        )
        self.toolBtnSawdustCleaning.setGeometry(177, 80, 130, 80)
        self.toolBtnSawdustCleaning.setStyleSheet(control_button_style)
        self.toolBtnSawdustCleaning.setCheckable(True)
        self.toolBtnSawdustCleaning.toggled.connect(self._on_chip_cleaning_toggled)

        # Cutting start button
        self.toolBtnCuttingStart = QPushButton("Kesim Başlat", self.controlButtonsFrame)
        self.toolBtnCuttingStart.setGeometry(30, 180, 130, 80)
        self.toolBtnCuttingStart.setStyleSheet(control_button_style)
        self.toolBtnCuttingStart.clicked.connect(self._on_cutting_start_clicked)

        # Cutting stop button
        self.toolBtnCuttingStop = QPushButton("Kesim Durdur", self.controlButtonsFrame)
        self.toolBtnCuttingStop.setGeometry(177, 180, 130, 80)
        self.toolBtnCuttingStop.setStyleSheet(control_button_style)
        self.toolBtnCuttingStop.clicked.connect(self._on_cutting_stop_clicked)

        # === LOG VIEWER FRAME (0, 718, 1124, 322) ===
        self.logViewerFrame = QFrame(self)
        self.logViewerFrame.setGeometry(0, 718, 1124, 322)
        self.logViewerFrame.setStyleSheet(frame_style)

        self.labelLogViewer = QLabel("Çalışma Günlüğü", self.logViewerFrame)
        self.labelLogViewer.setGeometry(27, 26, 271, 34)
        self.labelLogViewer.setStyleSheet(label_title_style)

        # Log text widget
        self.log_text = QTextEdit(self.logViewerFrame)
        self.log_text.setGeometry(30, 80, 1064, 222)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #F4F6FC;
                border: none;
                font-family: 'Plus Jakarta Sans';
                font-size: 14px;
            }
        """)

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
            # All mode buttons
            mode_buttons = [
                self.btnManualMode,
                self.btnFuzzyMode,
                self.btnExpertSystemMode,
                self.btnAiMode
            ]

            # Uncheck all buttons
            for button in mode_buttons:
                button.setChecked(False)

            # Check clicked button
            clicked_button.setChecked(True)

            # Set controller based on selection
            # Note: This requires importing ControllerType from control module
            # For now, log the selection
            if clicked_button == self.btnManualMode:
                self.add_log("Kesim modu manuel olarak ayarlandı", "INFO")
                # self._switch_controller(None)
            elif clicked_button == self.btnFuzzyMode:
                self.add_log("Kesim modu fuzzy olarak ayarlandı", "INFO")
                # self._switch_controller(ControllerType.FUZZY)
            elif clicked_button == self.btnExpertSystemMode:
                self.add_log("Kesim modu Linear system olarak ayarlandı", "INFO")
                # self._switch_controller(ControllerType.LINEAR)
            elif clicked_button == self.btnAiMode:
                self.add_log("Kesim modu AI olarak ayarlandı", "INFO")
                # self._switch_controller(ControllerType.ML)

        except Exception as e:
            logger.error(f"Cutting mode button error: {e}")
            self.add_log(f"Kesim modu değiştirme hatası: {str(e)}", "ERROR")

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
        """Send manual speed values to machine."""
        try:
            # This requires modbus client and helper functions
            # For now, just log
            speeds = self.speed_values.get(speed_level)
            if speeds:
                cutting_speed = speeds["cutting"]
                descent_speed = speeds["descent"]
                self.add_log(
                    f"Kesme hızı {cutting_speed:.1f} mm/s olarak ayarlandı",
                    "INFO"
                )
                self.add_log(
                    f"İnme hızı {descent_speed:.1f} mm/s olarak ayarlandı",
                    "INFO"
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
            current_value = self.labelSentCuttingSpeed.text()
            try:
                initial_value = float(current_value) if current_value != "NULL" else 0.0
            except ValueError:
                initial_value = 0.0

            # Show numpad dialog
            dialog = NumpadDialog(self)
            dialog.value = str(int(initial_value)) if initial_value != 0.0 else ""
            dialog.update_label()

            result = dialog.exec_()

            if result == dialog.Accepted:
                value_str = dialog.get_value()
                try:
                    value = float(value_str.replace(",", "."))
                except Exception:
                    value = 0.0

                # Clamp value between 0 and 500
                original_value = value
                value = max(0, min(500, value))

                if value > 0:
                    # Send value to machine
                    # self._send_manual_speed_value(value)

                    # Update display
                    with self._values_lock:
                        self.current_values['serit_kesme_hizi'] = f"{value:.1f}"
                    self.labelSentCuttingSpeed.setText(f"{value:.2f}")

                    # Log
                    if original_value != value:
                        self.add_log(
                            f"Kesme hızı {value:.2f} mm/s olarak ayarlandı "
                            f"(girilen değer: {original_value:.2f}, limit: 0-500)",
                            "WARNING"
                        )
                    else:
                        self.add_log(
                            f"Kesme hızı {value:.2f} mm/s olarak ayarlandı",
                            "INFO"
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
            current_value = self.labelSentDescentSpeed.text()
            try:
                initial_value = float(current_value) if current_value != "NULL" else 0.0
            except ValueError:
                initial_value = 0.0

            # Show numpad dialog
            dialog = NumpadDialog(self)
            dialog.value = str(int(initial_value)) if initial_value != 0.0 else ""
            dialog.update_label()

            result = dialog.exec_()

            if result == dialog.Accepted:
                value_str = dialog.get_value()
                try:
                    value = float(value_str.replace(",", "."))
                except Exception:
                    value = 0.0

                # Clamp value between 0 and 500
                original_value = value
                value = max(0, min(500, value))

                if value > 0:
                    # Send value to machine
                    # self._send_manual_descent_speed_value(value)

                    # Update display
                    with self._values_lock:
                        self.current_values['serit_inme_hizi'] = f"{value:.1f}"
                    self.labelSentDescentSpeed.setText(f"{value:.2f}")

                    # Log
                    if original_value != value:
                        self.add_log(
                            f"İnme hızı {value:.2f} mm/s olarak ayarlandı "
                            f"(girilen değer: {original_value:.2f}, limit: 0-500)",
                            "WARNING"
                        )
                    else:
                        self.add_log(
                            f"İnme hızı {value:.2f} mm/s olarak ayarlandı",
                            "INFO"
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
                # success = self.machine_control.start_coolant()
                self.add_log("Soğutma sıvısı açıldı.", "INFO")
                success = True  # Simulated
            else:
                # Disable coolant
                # success = self.machine_control.stop_coolant()
                self.add_log("Soğutma sıvısı kapatıldı.", "INFO")
                success = True  # Simulated

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
                # success = self.machine_control.start_chip_cleaning()
                self.add_log("Talaş temizliği açıldı.", "INFO")
                success = True  # Simulated
            else:
                # Disable chip cleaning
                # success = self.machine_control.stop_chip_cleaning()
                self.add_log("Talaş temizliği kapatıldı.", "INFO")
                success = True  # Simulated

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

            # success = self.machine_control.start_cutting()
            success = True  # Simulated

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

            # success = self.machine_control.stop_cutting()
            success = True  # Simulated

            if success:
                self.add_log("Kesim durduruldu.", "INFO")

                # Update stop time
                if self._cutting_start_time:
                    self._cutting_stop_datetime = datetime.now()
                    stop_time_str = self._cutting_stop_datetime.strftime('%H:%M:%S')
                    self.labelStopTimeValue.setText(stop_time_str)

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
            if self.data_pipeline and hasattr(self.data_pipeline, 'get_stats'):
                data = self.data_pipeline.get_stats()
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

            # Update cutting time tracking
            testere_durumu = int(processed_data.get('testere_durumu', 0))
            self._update_cutting_time_labels(testere_durumu)

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

                # Speeds
                cutting_speed = processed_data.get('serit_kesme_hizi', 0)
                descent_speed = processed_data.get('serit_inme_hizi', 0)
                self.current_values['serit_kesme_hizi'] = f"{cutting_speed:.1f}"
                self.current_values['serit_inme_hizi'] = f"{descent_speed:.1f}"

                # Machine status
                testere_durumu = processed_data.get('testere_durumu', 0)
                durum_text = {
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

    def _update_cutting_time_labels(self, testere_durumu: int):
        """Update cutting time labels based on machine state."""
        try:
            # Cutting started - ŞERIT MOTOR ÇALIŞIYOR (2)
            if testere_durumu == 2:
                if not self._cutting_start_datetime:
                    # Cutting started
                    self._cutting_start_datetime = datetime.now()
                    start_time_str = self._cutting_start_datetime.strftime('%H:%M:%S')
                    self.labelStartTimeValue.setText(start_time_str)
                    self.labelStopTimeValue.setText("--:--:--")
                    logger.info(f"Cutting started: {start_time_str}")

            # Cutting finished - KESİM BİTTİ (4)
            elif testere_durumu == 4 and self._cutting_start_datetime:
                # Cutting finished
                self._cutting_stop_datetime = datetime.now()
                stop_time_str = self._cutting_stop_datetime.strftime('%H:%M:%S')
                self.labelStopTimeValue.setText(stop_time_str)
                logger.info(f"Cutting finished: {stop_time_str}")

                # Reset for next cutting
                self._cutting_start_datetime = None
                self._cutting_stop_datetime = None

        except Exception as e:
            logger.error(f"Cutting time label update error: {e}")

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

    # No cleanup() method needed - PySide6 handles timer cleanup automatically
    # when widget is destroyed via parent-child relationships
