"""
Sensor page controller for Smart Band Saw.

This module provides real-time sensor monitoring with:
- Custom cutting graph with QPainter (860x450)
- Selectable X/Y axes (Time/Height, Speed/Current/Deviation/Torque)
- 9 anomaly detection frames with visual indicators
- Thread-safe data updates
- Production-ready for 1528x1080 page size
"""

from typing import Callable, Dict, Optional
from PySide6.QtCore import QTimer, QDateTime, Qt, QPoint
from PySide6.QtWidgets import QWidget, QButtonGroup, QLabel, QFrame, QPushButton
from PySide6.QtGui import QIcon, QPainter, QPen, QColor, QBrush, QPolygon
import os
from datetime import datetime, timedelta
import threading
import collections
import logging

logger = logging.getLogger(__name__)


class CuttingGraphWidget(QWidget):
    """
    Custom cutting graph widget with QPainter.

    Features:
    - Size: 860x450 pixels
    - Grid: 20 vertical, 10 horizontal lines
    - Line color: #F4F6FC (thickness 2)
    - Fill color: rgba(149, 9, 82, 30)
    - Grid color: rgba(255, 255, 255, 50)
    - Max 1000 data points
    - Red circle indicator (6px) at last point
    - Real-time updates at 10 FPS
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(860, 450)

        # Data structure: (x_value, y_value) tuples
        self.data_points = collections.deque(maxlen=1000)
        self.max_points = 1000

        # Graph settings
        self.padding = 20
        self.grid_color = QColor(255, 255, 255, 50)  # Transparent white
        self.line_color = QColor(0xF4, 0xF6, 0xFC)  # Line color (F4F6FC)
        self.fill_color = QColor(149, 9, 82, 30)  # Fill color

        # Axis information
        self.x_axis_type = "timestamp"  # Default
        self.y_axis_type = "serit_kesme_hizi"  # Default

        # Time axis labels - cut start and last point time
        self.cut_start_time: Optional[datetime] = None
        self.last_point_time: Optional[datetime] = None

        # Height axis - start and current values
        self.start_height_value: Optional[float] = None
        self.current_height_value: Optional[float] = None

        # Thread-safe data access lock
        self._data_lock = threading.Lock()

        # Timer for updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(100)  # 10 FPS

        # Widget style settings
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)

        # Create graph labels
        self._create_graph_labels()

    def set_axis_types(self, x_axis: str, y_axis: str):
        """Set X and Y axis types"""
        try:
            with self._data_lock:
                self.x_axis_type = x_axis
                self.y_axis_type = y_axis
                # Clear data when axis changes
                self.data_points.clear()
            # Update axis title labels
            self.update_axis_titles(x_axis, y_axis)
        except Exception as e:
            logger.error(f"Error setting axis types: {e}")

    def update_axis_titles(self, x_axis: str, y_axis: str):
        """Update axis title labels based on selected axis types"""
        try:
            # Y-axis title mapping (Turkish with proper characters)
            y_titles = {
                "serit_kesme_hizi": "Kesme Hızı (m/min)",
                "serit_inme_hizi": "İlerleme Hızı (mm/s)",
                "serit_motor_akim_a": "Şerit Akım (A)",
                "serit_sapmasi": "Şerit Sapması (mm)",
                "serit_motor_tork_percentage": "Şerit Tork (%)",
            }
            # X-axis title mapping (Turkish with proper characters)
            x_titles = {
                "timestamp": "Zaman (s)",
                "kafa_yuksekligi_mm": "Yükseklik (mm)",
            }
            # Update Y-axis title
            if hasattr(self, 'y_axis_title') and self.y_axis_title:
                y_text = y_titles.get(y_axis, "")
                self.y_axis_title.setText(y_text)
            # Update X-axis title
            if hasattr(self, 'x_axis_title') and self.x_axis_title:
                x_text = x_titles.get(x_axis, "")
                self.x_axis_title.setText(x_text)
        except Exception as e:
            logger.error(f"Error updating axis titles: {e}")

    def add_data_point(self, x_value: float, y_value: float):
        """Add new data point (thread-safe)"""
        try:
            with self._data_lock:
                self.data_points.append((x_value, y_value))
                # Remove old data if exceeds max
                if len(self.data_points) > self.max_points:
                    self.data_points.popleft()
                # Update last point time if using time axis
                if self.x_axis_type == "timestamp":
                    self.last_point_time = datetime.now()
        except Exception as e:
            logger.error(f"Error adding data point: {e}")

    def clear_data(self):
        """Clear all data"""
        try:
            with self._data_lock:
                self.data_points.clear()
                # Reset time info (will be set when cut starts)
                self.last_point_time = None
            # Reset labels - special format for time axis
            if self.x_axis_type == "timestamp" or self.y_axis_type == "timestamp":
                self.update_label_values(0, 0, 0, 0)
            else:
                self.update_label_values(0.0, 0.0, 0.0, 0.0)
        except Exception as e:
            logger.error(f"Error clearing data: {e}")

    def paintEvent(self, event):
        """Draw the graph"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Transparent background
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

            # If no data, just draw grid
            if not self.data_points:
                self._draw_grid(painter, self.rect().adjusted(self.padding, self.padding, -self.padding, -self.padding))
                return

            # Calculate drawing area
            draw_rect = self.rect().adjusted(self.padding, self.padding, -self.padding, -self.padding)

            # Draw grid
            self._draw_grid(painter, draw_rect)

            # Draw data
            self._draw_data(painter, draw_rect)

        except Exception as e:
            logger.error(f"Error drawing graph: {e}")

    def _draw_grid(self, painter: QPainter, rect):
        """Draw grid lines"""
        try:
            painter.setPen(QPen(self.grid_color, 1))

            # Vertical lines (20)
            for i in range(21):
                x = rect.left() + (rect.width() * i) // 20
                painter.drawLine(x, rect.top(), x, rect.bottom())

            # Horizontal lines (10)
            for i in range(11):
                y = rect.top() + (rect.height() * i) // 10
                painter.drawLine(rect.left(), y, rect.right(), y)
            
            painter.setPen(QPen(self.line_color, 2))
            painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())
            painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        except Exception as e:
            logger.error(f"Error drawing grid: {e}")

    def _draw_data(self, painter: QPainter, rect):
        """Draw data lines"""
        try:
            with self._data_lock:
                if len(self.data_points) < 2:
                    return

                # Separate X and Y values
                x_values = [point[0] for point in self.data_points]
                y_values = [point[1] for point in self.data_points]

                # Calculate value ranges
                x_min, x_max = min(x_values), max(x_values)
                y_min, y_max = min(y_values), max(y_values)

                # Expand range if too small
                if x_max - x_min < 0.1:
                    mid_val = (x_min + x_max) / 2
                    x_min = mid_val - 0.05
                    x_max = mid_val + 0.05

                if y_max - y_min < 0.1:
                    mid_val = (y_min + y_max) / 2
                    y_min = mid_val - 0.05
                    y_max = mid_val + 0.05

                # Update label values
                if self.x_axis_type == "timestamp" and self.cut_start_time and self.last_point_time:
                    # Special labels for time axis (start -> end)
                    self._update_time_axis_labels(self.cut_start_time, self.last_point_time, y_min, y_max)
                elif self.x_axis_type == "kafa_yuksekligi_mm" and self.start_height_value is not None and self.current_height_value is not None:
                    # Special labels for height axis (start -> current)
                    self._update_height_axis_labels(self.start_height_value, self.current_height_value, y_min, y_max)
                else:
                    self.update_label_values(x_min, x_max, y_min, y_max)

                # Line color
                painter.setPen(QPen(self.line_color, 2))

                # Fill color
                painter.setBrush(QBrush(self.fill_color))

                # Calculate line points (new data appears from right, indexed)
                points = []
                total_points = len(self.data_points)
                for i, (_x_value, y_value) in enumerate(self.data_points):
                    # X coordinate: 0..N-1 evenly spaced, newest on right
                    if total_points > 1:
                        x = rect.left() + (rect.width() * i) // (total_points - 1)
                    else:
                        x = rect.left() + rect.width() // 2

                    # Y coordinate (inverted - Qt y increases downward)
                    if y_max != y_min:
                        normalized_y = (y_value - y_min) / (y_max - y_min)
                    else:
                        normalized_y = 0.5
                    y = rect.bottom() - (rect.height() * normalized_y)

                    points.append((x, y))

                # Draw line
                if len(points) > 1:
                    # Main line
                    for i in range(len(points) - 1):
                        painter.drawLine(int(points[i][0]), int(points[i][1]),
                                       int(points[i+1][0]), int(points[i+1][1]))

                # Draw red circle at last point
                if points:
                    last_x, last_y = points[-1]
                    circle_size = 6
                    painter.setBrush(QBrush(QColor(255, 0, 0)))
                    painter.setPen(QPen(QColor(255, 0, 0), 1))
                    painter.drawEllipse(int(last_x - circle_size), int(last_y - circle_size),
                                      circle_size * 2, circle_size * 2)

        except Exception as e:
            logger.error(f"Error drawing data: {e}")

    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        # Update label positions if labels exist
        if hasattr(self, 'yust') and self.yust:
            self._update_label_positions()
        self.update()

    def _create_graph_labels(self):
        """Create graph axis labels"""
        from PySide6.QtWidgets import QLabel

        # Label style settings
        label_style = """
            QLabel {
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                background-color: transparent;
                border: none;
            }
        """

        # Axis title style (bold, 16px)
        axis_title_style = """
            QLabel {
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 16px;
                background-color: transparent;
                border: none;
            }
        """

        # Y-axis title label (rotated text on left side)
        self.y_axis_title = QLabel(self.parent())
        self.y_axis_title.setStyleSheet(axis_title_style)
        self.y_axis_title.setText("Kesme Hızı (m/min)")  # Default
        self.y_axis_title.setAlignment(Qt.AlignCenter)

        # Left side labels (Y axis) - in kesimGrafigiFrame
        self.yust = QLabel(self.parent())
        self.yust.setStyleSheet(label_style)
        self.yust.setText("0")
        self.yust.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.yorta = QLabel(self.parent())
        self.yorta.setStyleSheet(label_style)
        self.yorta.setText("0")
        self.yorta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.yalt = QLabel(self.parent())
        self.yalt.setStyleSheet(label_style)
        self.yalt.setText("0")
        self.yalt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Bottom labels (X axis) - in kesimGrafigiFrame
        self.xust = QLabel(self.parent())
        self.xust.setStyleSheet(label_style)
        self.xust.setText("0.00")
        self.xust.setAlignment(Qt.AlignCenter)

        self.xorta = QLabel(self.parent())
        self.xorta.setStyleSheet(label_style)
        self.xorta.setText("0.00")
        self.xorta.setAlignment(Qt.AlignCenter)

        self.xalt = QLabel(self.parent())
        self.xalt.setStyleSheet(label_style)
        self.xalt.setText("0.00")
        self.xalt.setAlignment(Qt.AlignCenter)

        # Show labels
        self.yust.show()
        self.yorta.show()
        self.yalt.show()
        self.xust.show()
        self.xorta.show()
        self.xalt.show()
        self.y_axis_title.show()

        # Update label positions
        self._update_label_positions()

    def _format_time_label(self, dt: datetime) -> str:
        """Format time labels as HH.MM"""
        try:
            return dt.strftime('%H.%M')
        except Exception:
            return "0.00"

    def _update_time_axis_labels(self, start_dt: datetime, end_dt: datetime, y_min: float, y_max: float):
        """Update X labels when time axis is selected (start, middle, end)"""
        try:
            # Y axis labels
            self.update_label_values(None, None, y_min, y_max)
            # X axis labels
            if start_dt and end_dt:
                mid_dt = start_dt + (end_dt - start_dt) / 2
                if hasattr(self, 'xust'):
                    self.xust.setText(self._format_time_label(start_dt))
                if hasattr(self, 'xorta'):
                    self.xorta.setText(self._format_time_label(mid_dt))
                if hasattr(self, 'xalt'):
                    self.xalt.setText(self._format_time_label(end_dt))
        except Exception as e:
            logger.error(f"Error updating time labels: {e}")

    def _update_height_axis_labels(self, start_height: float, current_height: float, y_min: float, y_max: float):
        """Update X labels when height X axis is selected: start | middle | current"""
        try:
            # Update Y axis labels
            self.update_label_values(None, None, y_min, y_max)
            # X axis: left is start height fixed, middle is average, right is current height
            start_val = float(start_height)
            curr_val = float(current_height)
            mid_val = (start_val + curr_val) / 2.0
            if hasattr(self, 'xust'):
                self.xust.setText(f"{start_val:.2f}")
            if hasattr(self, 'xorta'):
                self.xorta.setText(f"{mid_val:.2f}")
            if hasattr(self, 'xalt'):
                self.xalt.setText(f"{curr_val:.2f}")
        except Exception as e:
            logger.error(f"Error updating height labels: {e}")

    def _update_label_positions(self):
        """Update label positions"""
        try:
            # Graph widget position (position within kesimGrafigiFrame)
            graph_x = 72  # Graph widget x position
            graph_y = 87  # Graph widget y position
            graph_width = 860  # Graph widget width
            graph_height = 450  # Graph widget height

            # Label dimensions
            label_width = 80  # Increased width
            label_height = 30

            # Left side labels (Y axis)
            # Top
            self.yust.setGeometry(graph_x - label_width, graph_y + 20, label_width, label_height)
            # Middle
            self.yorta.setGeometry(graph_x - label_width, graph_y + (graph_height // 2) - (label_height // 2), label_width, label_height)
            # Bottom
            self.yalt.setGeometry(graph_x - label_width, graph_y + graph_height - label_height - 20, label_width, label_height)

            # Bottom labels (X axis) - below the graph
            # Left
            self.xust.setGeometry(graph_x + 20, graph_y + graph_height + 5, label_width, label_height)
            # Middle
            self.xorta.setGeometry(graph_x + (graph_width // 2) - (label_width // 2), graph_y + graph_height + 5, label_width, label_height)
            # Right
            self.xalt.setGeometry(graph_x + graph_width - label_width - 20, graph_y + graph_height + 5, label_width, label_height)

            # Y-axis title label (positioned to left of Y-axis value labels, centered vertically)
            # Using horizontal text since Qt rotation is complex
            y_title_width = 180
            y_title_height = 25
            y_title_x = graph_x - label_width - y_title_width - 10  # Left of value labels
            y_title_y = graph_y + (graph_height // 2) - (y_title_height // 2)  # Centered vertically
            if hasattr(self, 'y_axis_title') and self.y_axis_title:
                self.y_axis_title.setGeometry(y_title_x, y_title_y, y_title_width, y_title_height)

        except Exception as e:
            logger.error(f"Error updating label positions: {e}")

    def update_label_values(self, x_min=None, x_max=None, y_min=None, y_max=None):
        """Update label values"""
        try:
            # Y axis labels (left side) - 2 decimal places
            if y_min is not None and y_max is not None:
                # Special format for time axis
                if self.y_axis_type == "timestamp":
                    # Show in seconds (0-999 range)
                    y_max_val = min(int(y_max), 999)
                    y_min_val = max(int(y_min), 0)
                    y_mid_val = int((y_min_val + y_max_val) / 2)

                    self.yust.setText(f"{y_max_val}s")
                    self.yorta.setText(f"{y_mid_val}s")
                    self.yalt.setText(f"{y_min_val}s")
                else:
                    # Other axes with two decimal places
                    y_max_val = min(float(y_max), 9999.99)
                    y_min_val = max(float(y_min), -999.99)
                    y_mid_val = (y_min_val + y_max_val) / 2.0

                    self.yust.setText(f"{y_max_val:.2f}")
                    self.yorta.setText(f"{y_mid_val:.2f}")
                    self.yalt.setText(f"{y_min_val:.2f}")

            # X axis labels (bottom) - with decimal places
            if x_min is not None and x_max is not None:
                # Special format for time axis
                if self.x_axis_type == "timestamp":
                    # Show in seconds (0-999 range)
                    x_max_val = min(int(x_max), 999)
                    x_min_val = max(int(x_min), 0)
                    x_mid_val = int((x_min_val + x_max_val) / 2)

                    self.xust.setText(f"{x_min_val}s")
                    self.xorta.setText(f"{x_mid_val}s")
                    self.xalt.setText(f"{x_max_val}s")
                else:
                    # Other axes with decimal places
                    x_max_val = min(x_max, 9999.99)  # Max 4 digits + 2 decimal
                    x_min_val = max(x_min, -999.99)  # Min -999.99
                    x_mid_val = (x_min_val + x_max_val) / 2

                    self.xust.setText(f"{x_min_val:.2f}")
                    self.xorta.setText(f"{x_mid_val:.2f}")
                    self.xalt.setText(f"{x_max_val:.2f}")

        except Exception as e:
            logger.error(f"Error updating label values: {e}")


class SensorController(QWidget):
    """
    Sensor page controller - 1528x1080.

    Features:
    - Custom cutting graph widget (860x450) with QPainter
    - Axis selection buttons (Y: Speed/Current/Deviation/Torque, X: Time/Height)
    - 9 anomaly detection frames for all sensors
    - Thread-safe real-time updates
    - Production-ready with all exact positions and styling
    """

    def __init__(self, control_manager=None, data_pipeline=None, parent=None):
        """Initialize sensor controller"""
        super().__init__(parent)

        self.control_manager = control_manager
        self.data_pipeline = data_pipeline

        # Setup UI matching reference design (1528x1080 page size)
        self._setup_ui()

        # Axis selection groups (exclusive)
        self._setup_axis_button_groups()

        # Anomaly states (will be updated via callback from anomaly manager)
        self.anomaly_states = {
            'KesmeHizi': False,
            'IlerlemeHizi': False,
            'SeritAkim': False,
            'SeritTork': False,
            'SeritGerginligi': False,
            'SeritSapmasi': False,
            'TitresimX': False,
            'TitresimY': False,
            'TitresimZ': False,
        }

        # Thread-safe lock for anomaly states
        self._anomaly_lock = threading.Lock()

        # Setup anomaly manager callback
        if data_pipeline and hasattr(data_pipeline, 'anomaly_manager'):
            data_pipeline.anomaly_manager.set_update_callback(self._update_anomaly_state)
            logger.info("Anomaly manager callback registered")

        # Last cut data storage
        self.last_cut_data = []
        self.is_cutting = False
        self.cut_start_time = None

        # Buffer to store full current cut for all metrics (overflow protection)
        from collections import deque
        self.current_cut_buffer = deque(maxlen=2000)  # Max 2000 data points (~3-4 minutes cutting)

        # Thread-safety for buffer lock (MUST be before _setup_cutting_graph)
        self._buffer_lock = threading.Lock()

        # Cutting graph widget
        self.cutting_graph = None
        self._setup_cutting_graph()

        # Thread-local database connection
        self._thread_local = threading.local()
        logger.info("Thread-local database connection ready")

        # Timers (data)
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self._on_data_tick)
        self._data_timer.start(200)  # 200 ms
        self._on_data_tick()

        # Optional reset button
        if hasattr(self, 'toolButton'):
            self.toolButton.clicked.connect(self.reset_anomaly_states)

        # Initial UI
        self._set_all_frames_green()
        self._set_all_info_labels("Her şey yolunda.")

        # Trigger graph on initial load
        if self.cutting_graph:
            # Manually trigger axis change event
            self._on_x_axis_changed(None)

        logger.info("SensorController initialized")

    def _setup_ui(self):
        """Setup sensor page UI - 1528x1080 with all frames and controls"""

        # Main container frame matching reference design
        main_frame = QFrame(self)
        main_frame.setGeometry(0, 0, 1528, 1080)
        main_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)

        # ===== CUTTING GRAPH FRAME (Top) =====
        # Eski UI: (425, 127, 934, 568) -> Yeni: (33, 127, 934, 568)
        self.kesimGrafigiFrame = QFrame(main_frame)
        self.kesimGrafigiFrame.setGeometry(33, 127, 934, 568)
        self.kesimGrafigiFrame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0,
                    x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                border-radius: 20px;
            }
        """)

        # Graph title
        labelKesimGrafigi = QLabel("Kesim Grafiği", self.kesimGrafigiFrame)
        labelKesimGrafigi.setGeometry(37, 20, 220, 36)
        labelKesimGrafigi.setStyleSheet("""
            QLabel {
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 28px;
                background-color: transparent;
            }
        """)

        # ===== AXIS SELECTION BUTTONS =====
        # Button style matching control panel
        axis_btn_style = """
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #000000, stop:0.38 rgba(26, 31, 55, 200));
                border-radius: 20px;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 18px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                border: 2px solid rgba(244, 246, 252, 100);
            }
            QPushButton:checked {
                border: 2px solid #F4F6FC;
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0,
                    x2:1, y2:1,
                    stop:0 rgba(149, 9, 82, 255),
                    stop:1 rgba(26, 31, 55, 255)
                );
            }
        """

        # Frame style for containers
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

        # ===== X EKSENI FRAME (Y-axis buttons - Left Bottom) =====
        # Eski UI: (425, 724, 578, 342) -> Yeni: (33, 724, 578, 342)
        self.XEkseniFrame = QFrame(main_frame)
        self.XEkseniFrame.setGeometry(33, 724, 578, 342)
        self.XEkseniFrame.setStyleSheet(frame_style)

        labelXEkseni = QLabel("Y Ekseni", self.XEkseniFrame)
        labelXEkseni.setGeometry(34, 19, 295, 39)
        labelXEkseni.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 28px;
            }
        """)

        # Y-axis buttons (in XEkseniFrame)
        self.btnKesmeHizi = QPushButton("Kesme Hızı", self.XEkseniFrame)
        self.btnKesmeHizi.setGeometry(41, 82, 240, 69)
        self.btnKesmeHizi.setStyleSheet(axis_btn_style)
        self.btnKesmeHizi.setCheckable(True)

        self.btnIlerlemeHizi = QPushButton("İlerleme Hızı", self.XEkseniFrame)
        self.btnIlerlemeHizi.setGeometry(298, 82, 240, 69)
        self.btnIlerlemeHizi.setStyleSheet(axis_btn_style)
        self.btnIlerlemeHizi.setCheckable(True)

        self.btnSeritAkim = QPushButton("Şerit Akım", self.XEkseniFrame)
        self.btnSeritAkim.setGeometry(41, 162, 240, 69)
        self.btnSeritAkim.setStyleSheet(axis_btn_style)
        self.btnSeritAkim.setCheckable(True)

        self.btnSeritSapmasi = QPushButton("Şerit Sapması", self.XEkseniFrame)
        self.btnSeritSapmasi.setGeometry(298, 162, 240, 69)
        self.btnSeritSapmasi.setStyleSheet(axis_btn_style)
        self.btnSeritSapmasi.setCheckable(True)

        self.btnSeritTork = QPushButton("Şerit Tork", self.XEkseniFrame)
        self.btnSeritTork.setGeometry(169, 239, 240, 69)
        self.btnSeritTork.setStyleSheet(axis_btn_style)
        self.btnSeritTork.setCheckable(True)

        # ===== Y EKSENI FRAME (X-axis buttons - Center Bottom) =====
        # Eski UI: (1030, 724, 329, 342) -> Yeni: (638, 724, 329, 342)
        self.YEkseniFrame = QFrame(main_frame)
        self.YEkseniFrame.setGeometry(638, 724, 329, 342)
        self.YEkseniFrame.setStyleSheet(frame_style)

        labelYEkseni = QLabel("X Ekseni", self.YEkseniFrame)
        labelYEkseni.setGeometry(34, 19, 295, 39)
        labelYEkseni.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 28px;
            }
        """)

        # X-axis buttons (in YEkseniFrame)
        self.btnZaman = QPushButton("Zaman", self.YEkseniFrame)
        self.btnZaman.setGeometry(44, 82, 240, 69)
        self.btnZaman.setStyleSheet(axis_btn_style)
        self.btnZaman.setCheckable(True)
        self.btnZaman.setChecked(True)  # Default X axis

        self.btnYukseklik = QPushButton("Yükseklik", self.YEkseniFrame)
        self.btnYukseklik.setGeometry(44, 170, 240, 69)
        self.btnYukseklik.setStyleSheet(axis_btn_style)
        self.btnYukseklik.setCheckable(True)

        # ===== ANOMALY DURUMU FRAME (Right Side) =====
        # Eski UI: (1385, 127, 505, 941) -> Yeni: (993, 127, 505, 941)
        self.AnomaliDurumuFrame = QFrame(main_frame)
        self.AnomaliDurumuFrame.setGeometry(993, 127, 505, 941)
        self.AnomaliDurumuFrame.setStyleSheet(frame_style)

        labelAnomaliDurumu = QLabel("Anomali Durumu", self.AnomaliDurumuFrame)
        labelAnomaliDurumu.setGeometry(34, 19, 295, 39)
        labelAnomaliDurumu.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 32px;
            }
        """)

        # Motor Verileri Frame (inside AnomaliDurumuFrame)
        self.MotorVerileriFrame = QFrame(self.AnomaliDurumuFrame)
        self.MotorVerileriFrame.setGeometry(23, 77, 459, 839)
        self.MotorVerileriFrame.setStyleSheet(frame_style)

        # Green gradient (normal state)
        green_frame_style = """
            QFrame {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0,
                    x2:1, y2:1,
                    stop:0 rgba(0, 0, 0, 255),
                    stop:0.480769 rgba(9, 139, 7, 255),
                    stop:1 rgba(9, 139, 7, 255)
                );
                border-radius: 20px;
            }
        """

        # Label style for sensor names
        sensor_name_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
            }
        """

        # Info label style
        info_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 18px;
            }
        """

        # 1. Kesme Hızı Frame (inside MotorVerileriFrame)
        self.KesmeHiziFrame = QFrame(self.MotorVerileriFrame)
        self.KesmeHiziFrame.setGeometry(8, 30, 443, 60)
        self.KesmeHiziFrame.setStyleSheet(green_frame_style)

        self.labelKesmeHiziName = QLabel("Kesme Hızı", self.KesmeHiziFrame)
        self.labelKesmeHiziName.setGeometry(28, 8, 393, 20)
        self.labelKesmeHiziName.setStyleSheet(sensor_name_style)

        self.labelKesmeHiziInfo = QLabel("Her şey yolunda.", self.KesmeHiziFrame)
        self.labelKesmeHiziInfo.setGeometry(25, 33, 401, 20)
        self.labelKesmeHiziInfo.setStyleSheet(info_style)

        # 2. İlerleme Hızı Frame
        self.IlerlemeHiziFrame = QFrame(self.MotorVerileriFrame)
        self.IlerlemeHiziFrame.setGeometry(8, 110, 443, 60)
        self.IlerlemeHiziFrame.setStyleSheet(green_frame_style)

        self.labelIlerlemeHiziName = QLabel("İlerleme Hızı", self.IlerlemeHiziFrame)
        self.labelIlerlemeHiziName.setGeometry(25, 8, 393, 20)
        self.labelIlerlemeHiziName.setStyleSheet(sensor_name_style)

        self.labelIlerlemeHiziInfo = QLabel("Her şey yolunda.", self.IlerlemeHiziFrame)
        self.labelIlerlemeHiziInfo.setGeometry(25, 33, 401, 20)
        self.labelIlerlemeHiziInfo.setStyleSheet(info_style)

        # 3. Şerit Akım Frame
        self.SeritAkimFrame = QFrame(self.MotorVerileriFrame)
        self.SeritAkimFrame.setGeometry(8, 190, 443, 60)
        self.SeritAkimFrame.setStyleSheet(green_frame_style)

        self.labelSeritAkimName = QLabel("Şerit Akım", self.SeritAkimFrame)
        self.labelSeritAkimName.setGeometry(25, 8, 393, 20)
        self.labelSeritAkimName.setStyleSheet(sensor_name_style)

        self.labelSeritAkimInfo = QLabel("Her şey yolunda.", self.SeritAkimFrame)
        self.labelSeritAkimInfo.setGeometry(25, 33, 401, 20)
        self.labelSeritAkimInfo.setStyleSheet(info_style)

        # 4. Şerit Tork Frame
        self.SeritTorkFrame = QFrame(self.MotorVerileriFrame)
        self.SeritTorkFrame.setGeometry(8, 270, 443, 60)
        self.SeritTorkFrame.setStyleSheet(green_frame_style)

        self.labelSeritTorkName = QLabel("Şerit Tork", self.SeritTorkFrame)
        self.labelSeritTorkName.setGeometry(25, 8, 393, 20)
        self.labelSeritTorkName.setStyleSheet(sensor_name_style)

        self.labelSeritTorkInfo = QLabel("Her şey yolunda.", self.SeritTorkFrame)
        self.labelSeritTorkInfo.setGeometry(25, 33, 401, 20)
        self.labelSeritTorkInfo.setStyleSheet(info_style)

        # 5. Şerit Gerginliği Frame
        self.SeritGerginligiFrame = QFrame(self.MotorVerileriFrame)
        self.SeritGerginligiFrame.setGeometry(8, 350, 443, 60)
        self.SeritGerginligiFrame.setStyleSheet(green_frame_style)

        self.labelSeritGerginligiName = QLabel("Şerit Gerginliği", self.SeritGerginligiFrame)
        self.labelSeritGerginligiName.setGeometry(25, 8, 393, 20)
        self.labelSeritGerginligiName.setStyleSheet(sensor_name_style)

        self.labelSeritGerginligiInfo = QLabel("Her şey yolunda.", self.SeritGerginligiFrame)
        self.labelSeritGerginligiInfo.setGeometry(25, 33, 401, 20)
        self.labelSeritGerginligiInfo.setStyleSheet(info_style)

        # 6. Şerit Sapması Frame
        self.SeritSapmasiFrame = QFrame(self.MotorVerileriFrame)
        self.SeritSapmasiFrame.setGeometry(8, 430, 443, 60)
        self.SeritSapmasiFrame.setStyleSheet(green_frame_style)

        self.labelSeritSapmasiName = QLabel("Şerit Sapması", self.SeritSapmasiFrame)
        self.labelSeritSapmasiName.setGeometry(25, 8, 393, 20)
        self.labelSeritSapmasiName.setStyleSheet(sensor_name_style)

        self.labelSeritSapmasiInfo = QLabel("Her şey yolunda.", self.SeritSapmasiFrame)
        self.labelSeritSapmasiInfo.setGeometry(25, 33, 401, 20)
        self.labelSeritSapmasiInfo.setStyleSheet(info_style)

        # 7. Titreşim X Frame
        self.TitresimXFrame = QFrame(self.MotorVerileriFrame)
        self.TitresimXFrame.setGeometry(8, 510, 443, 60)
        self.TitresimXFrame.setStyleSheet(green_frame_style)

        self.labelTitresimXName = QLabel("Titreşim X", self.TitresimXFrame)
        self.labelTitresimXName.setGeometry(25, 8, 393, 20)
        self.labelTitresimXName.setStyleSheet(sensor_name_style)

        self.labelTitresimXInfo = QLabel("Her şey yolunda.", self.TitresimXFrame)
        self.labelTitresimXInfo.setGeometry(25, 33, 401, 20)
        self.labelTitresimXInfo.setStyleSheet(info_style)

        # 8. Titreşim Y Frame
        self.TitresimYFrame = QFrame(self.MotorVerileriFrame)
        self.TitresimYFrame.setGeometry(8, 590, 443, 60)
        self.TitresimYFrame.setStyleSheet(green_frame_style)

        self.labelTitresimYName = QLabel("Titreşim Y", self.TitresimYFrame)
        self.labelTitresimYName.setGeometry(25, 8, 393, 20)
        self.labelTitresimYName.setStyleSheet(sensor_name_style)

        self.labelTitresimYInfo = QLabel("Her şey yolunda.", self.TitresimYFrame)
        self.labelTitresimYInfo.setGeometry(25, 33, 401, 20)
        self.labelTitresimYInfo.setStyleSheet(info_style)

        # 9. Titreşim Z Frame
        self.TitresimZFrame = QFrame(self.MotorVerileriFrame)
        self.TitresimZFrame.setGeometry(8, 670, 443, 60)
        self.TitresimZFrame.setStyleSheet(green_frame_style)

        self.labelTitresimZName = QLabel("Titreşim Z", self.TitresimZFrame)
        self.labelTitresimZName.setGeometry(25, 8, 393, 20)
        self.labelTitresimZName.setStyleSheet(sensor_name_style)

        self.labelTitresimZInfo = QLabel("Her şey yolunda.", self.TitresimZFrame)
        self.labelTitresimZInfo.setGeometry(25, 33, 401, 20)
        self.labelTitresimZInfo.setStyleSheet(info_style)

        # ===== RESET BUTTON (inside MotorVerileriFrame) =====
        self.toolButton = QPushButton("Sıfırla", self.MotorVerileriFrame)
        self.toolButton.setGeometry(8, 750, 443, 60)
        self.toolButton.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #000000, stop:0.38 rgba(26, 31, 55, 200));
                border: 1px solid #F4F6FC;
                border-radius: 20px;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 19px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(20, 20, 20, 255),
                    stop:0.38 rgba(46, 51, 75, 200)
                );
            }
        """)

    def _setup_cutting_graph(self):
        """Setup cutting graph widget"""
        try:
            # Find cutting graph frame
            if hasattr(self, 'kesimGrafigiFrame'):
                self.cutting_graph = CuttingGraphWidget(self.kesimGrafigiFrame)
                self.cutting_graph.setGeometry(72, 87, 860, 450)
                self.cutting_graph.show()

                # Set default axis types (Time - Cutting Speed)
                self.cutting_graph.set_axis_types("timestamp", "serit_kesme_hizi")

                # Load last cut data
                self._load_last_cut_data()

                # Update graph widget
                self.cutting_graph.update()

                logger.info("Cutting graph widget setup successfully")
            else:
                logger.warning("kesimGrafigiFrame not found")
        except Exception as e:
            logger.error(f"Error setting up cutting graph: {e}")

    def _setup_axis_button_groups(self):
        """Setup axis button groups for exclusive selection"""
        # Y-axis buttons
        self._y_group = QButtonGroup(self)
        self._y_group.setExclusive(True)
        for name in ('btnKesmeHizi', 'btnIlerlemeHizi', 'btnSeritAkim', 'btnSeritSapmasi', 'btnSeritTork'):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.setCheckable(True)
                self._y_group.addButton(btn)

        # X-axis buttons
        self._x_group = QButtonGroup(self)
        self._x_group.setExclusive(True)
        for name in ('btnZaman', 'btnYukseklik'):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.setCheckable(True)
                self._x_group.addButton(btn)

        # Default: Kesme Hızı and Zaman selected
        if hasattr(self, 'btnKesmeHizi'):
            self.btnKesmeHizi.setChecked(True)
        if hasattr(self, 'btnZaman'):
            self.btnZaman.setChecked(True)

        # Listen to axis changes
        self._y_group.buttonClicked.connect(self._on_y_axis_changed)
        self._x_group.buttonClicked.connect(self._on_x_axis_changed)

    def _get_selected_x_axis(self) -> str:
        """Get selected X axis"""
        try:
            if hasattr(self, 'btnZaman') and self.btnZaman.isChecked():
                return "timestamp"
            elif hasattr(self, 'btnYukseklik') and self.btnYukseklik.isChecked():
                return "kafa_yuksekligi_mm"
            else:
                return "timestamp"  # Default
        except Exception as e:
            logger.error(f"Error getting X axis: {e}")
            return "timestamp"

    def _get_selected_y_axis(self) -> str:
        """Get selected Y axis"""
        try:
            if hasattr(self, 'btnKesmeHizi') and self.btnKesmeHizi.isChecked():
                return "serit_kesme_hizi"
            elif hasattr(self, 'btnIlerlemeHizi') and self.btnIlerlemeHizi.isChecked():
                return "serit_inme_hizi"
            elif hasattr(self, 'btnSeritAkim') and self.btnSeritAkim.isChecked():
                return "serit_motor_akim_a"
            elif hasattr(self, 'btnSeritSapmasi') and self.btnSeritSapmasi.isChecked():
                return "serit_sapmasi"
            elif hasattr(self, 'btnSeritTork') and self.btnSeritTork.isChecked():
                return "serit_motor_tork_percentage"
            else:
                return "serit_kesme_hizi"  # Default
        except Exception as e:
            logger.error(f"Error getting Y axis: {e}")
            return "serit_kesme_hizi"

    def _on_x_axis_changed(self, button):
        """Called when X axis changes"""
        try:
            if self.cutting_graph:
                x_axis = self._get_selected_x_axis()
                y_axis = self._get_selected_y_axis()
                self.cutting_graph.set_axis_types(x_axis, y_axis)
                # If cutting or buffer exists, rebuild from buffer
                if self.is_cutting or (self.current_cut_buffer and len(self.current_cut_buffer) > 0):
                    self._rebuild_graph_from_buffer()
                else:
                    # Load last cut data
                    self._load_last_cut_data()
                logger.info(f"X axis changed: {x_axis}")
        except Exception as e:
            logger.error(f"Error changing X axis: {e}")

    def _on_y_axis_changed(self, button):
        """Called when Y axis changes"""
        try:
            if self.cutting_graph:
                x_axis = self._get_selected_x_axis()
                y_axis = self._get_selected_y_axis()
                self.cutting_graph.set_axis_types(x_axis, y_axis)
                # If cutting or buffer exists, rebuild from buffer
                if self.is_cutting or (self.current_cut_buffer and len(self.current_cut_buffer) > 0):
                    self._rebuild_graph_from_buffer()
                else:
                    # Load last cut data
                    self._load_last_cut_data()
                logger.info(f"Y axis changed: {y_axis}")
        except Exception as e:
            logger.error(f"Error changing Y axis: {e}")

    def _set_all_frames_green(self):
        """Set all anomaly frames to green (normal state)"""
        green_style = """
            QFrame {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0,
                    x2:1, y2:1,
                    stop:0 rgba(0, 0, 0, 255),
                    stop:0.480769 rgba(9, 139, 7, 255),
                    stop:1 rgba(9, 139, 7, 255)
                );
                border-radius: 20px;
            }
        """
        for name in (
            'KesmeHiziFrame', 'IlerlemeHiziFrame', 'SeritAkimFrame', 'SeritTorkFrame', 'SeritGerginligiFrame',
            'SeritSapmasiFrame', 'TitresimXFrame', 'TitresimYFrame', 'TitresimZFrame'
        ):
            frame = getattr(self, name, None)
            if frame:
                frame.setStyleSheet(green_style)

    def _set_all_info_labels(self, text: str):
        """Set all info labels to the same text"""
        for name in (
            'labelKesmeHiziInfo', 'labelIlerlemeHiziInfo', 'labelSeritAkimInfo', 'labelSeritTorkInfo', 'labelSeritGerginligiInfo',
            'labelSeritSapmasiInfo', 'labelTitresimXInfo', 'labelTitresimYInfo', 'labelTitresimZInfo'
        ):
            lbl = getattr(self, name, None)
            if lbl:
                lbl.setText(text)

    def _update_anomaly_state(self, sensor_key: str, is_anomaly: bool):
        """
        Update anomaly state from anomaly manager callback (thread-safe).

        Called by AnomalyManager when anomaly state changes.

        Args:
            sensor_key: Anomaly state key (e.g., 'KesmeHizi', 'SeritAkim')
            is_anomaly: True if anomaly detected
        """
        try:
            with self._anomaly_lock:
                if sensor_key in self.anomaly_states:
                    self.anomaly_states[sensor_key] = is_anomaly
                    logger.debug(f"Anomaly state updated: {sensor_key} = {is_anomaly}")
        except Exception as e:
            logger.error(f"Error updating anomaly state ({sensor_key}): {e}")

    def reset_anomaly_states(self):
        """Reset all anomaly states"""
        with self._anomaly_lock:
            for key in self.anomaly_states:
                self.anomaly_states[key] = False

        self._set_all_frames_green()
        self._set_all_info_labels("Her şey yolunda.")

        # Reset anomaly tracker (persists reset time to DB)
        if self.data_pipeline and hasattr(self.data_pipeline, 'anomaly_tracker'):
            self.data_pipeline.anomaly_tracker.reset(reset_by="user")
            logger.info("Anomaly tracker reset by user")

        # Also reset anomaly manager (clears buffers)
        if self.data_pipeline and hasattr(self.data_pipeline, 'anomaly_manager'):
            self.data_pipeline.anomaly_manager.reset_anomaly_states()
            logger.info("Anomaly manager states reset")

    def _on_data_tick(self):
        """Periodic data update callback"""
        try:
            if self.data_pipeline:
                # Use get_latest_data for sensor display
                if hasattr(self.data_pipeline, 'get_latest_data'):
                    data = self.data_pipeline.get_latest_data()
                    if data and isinstance(data, dict):
                        self._update_sensor_values(data)
        except Exception as e:
            logger.error(f"Error in data tick: {e}")

    def _update_sensor_values(self, data: Dict):
        """Update sensor values and anomaly states"""
        try:
            # Safe float conversion
            def _f(val, default=0.0):
                try:
                    return float(val)
                except Exception:
                    return default

            current_time = datetime.now().strftime('%d.%m.%Y')

            # Get sensor values
            serit_akim = _f(data.get('serit_motor_akim_a', 0))
            ilerleme_hizi = _f(data.get('serit_inme_hizi', 0))
            serit_sapmasi = _f(data.get('serit_sapmasi', 0))
            vib_x = _f(data.get('ivme_olcer_x_hz', 0))
            vib_y = _f(data.get('ivme_olcer_y_hz', 0))
            vib_z = _f(data.get('ivme_olcer_z_hz', 0))
            serit_tork = _f(data.get('serit_motor_tork_percentage', 0))
            serit_gerginligi = _f(data.get('serit_gerginligi_bar', 0))
            kesme_hizi = _f(data.get('serit_kesme_hizi', 0))

            # Update value labels
            if hasattr(self, 'labelKesmeHiziValue'):
                self.labelKesmeHiziValue.setText(f"{kesme_hizi:.1f} m/min")
            if hasattr(self, 'labelIlerlemeHiziValue'):
                self.labelIlerlemeHiziValue.setText(f"{ilerleme_hizi:.1f} mm/s")
            if hasattr(self, 'labelSeritAkimValue'):
                self.labelSeritAkimValue.setText(f"{serit_akim:.1f} A")
            if hasattr(self, 'labelSeritTorkValue'):
                self.labelSeritTorkValue.setText(f"{serit_tork:.1f} %")
            if hasattr(self, 'labelSeritGerginligiValue'):
                self.labelSeritGerginligiValue.setText(f"{serit_gerginligi:.1f} bar")
            if hasattr(self, 'labelSeritSapmasiValue'):
                self.labelSeritSapmasiValue.setText(f"{serit_sapmasi:.2f} mm")
            if hasattr(self, 'labelTitresimXValue'):
                self.labelTitresimXValue.setText(f"{vib_x:.1f} Hz")
            if hasattr(self, 'labelTitresimYValue'):
                self.labelTitresimYValue.setText(f"{vib_y:.1f} Hz")
            if hasattr(self, 'labelTitresimZValue'):
                self.labelTitresimZValue.setText(f"{vib_z:.1f} Hz")

            # Update cutting graph
            self._update_cutting_graph(data)

            # Frame styles
            red_style = """
                QFrame {
                    background: qlineargradient(
                        spread:pad, x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(0, 0, 0, 255), stop:1 rgba(124, 4, 66, 255)
                    );
                    border-radius: 20px;
                }
            """
            green_style = """
                QFrame {
                    background: qlineargradient(
                        spread:pad,
                        x1:0, y1:0,
                        x2:1, y2:1,
                        stop:0 rgba(0, 0, 0, 255),
                        stop:0.480769 rgba(9, 139, 7, 255),
                        stop:1 rgba(9, 139, 7, 255)
                    );
                    border-radius: 20px;
                }
            """

            # Get anomaly summary from tracker (for time range and count display)
            anomaly_summary = {}
            if self.data_pipeline and hasattr(self.data_pipeline, 'anomaly_tracker'):
                anomaly_summary = self.data_pipeline.anomaly_tracker.get_anomaly_summary()

            def upd(frame_name: str, label_name: str, sensor_key: str, ok_text: str = "Her şey yolunda."):
                frame = getattr(self, frame_name, None)
                label = getattr(self, label_name, None)
                is_anom = sensor_key in anomaly_summary

                if frame:
                    frame.setStyleSheet(red_style if is_anom else green_style)

                if label:
                    if is_anom:
                        info = anomaly_summary[sensor_key]
                        count = info.get('count', 1)
                        first_time = info.get('first_time', '')
                        last_time = info.get('last_time', '')

                        # Format time string
                        try:
                            first_dt = datetime.fromisoformat(first_time)
                            last_dt = datetime.fromisoformat(last_time)
                            if count == 1:
                                time_str = first_dt.strftime('%H:%M:%S')
                            else:
                                time_str = f"{first_dt.strftime('%H:%M:%S')} - {last_dt.strftime('%H:%M:%S')}"
                            label.setText(f"{time_str} ({count}x anomali)")
                        except Exception:
                            label.setText(f"Anomali tespit edildi ({count}x)")
                    else:
                        label.setText(ok_text)

            # Update anomaly frames
            upd('KesmeHiziFrame', 'labelKesmeHiziInfo', 'KesmeHizi')
            upd('IlerlemeHiziFrame', 'labelIlerlemeHiziInfo', 'IlerlemeHizi')
            upd('SeritAkimFrame', 'labelSeritAkimInfo', 'SeritAkim')
            upd('SeritTorkFrame', 'labelSeritTorkInfo', 'SeritTork')
            upd('SeritGerginligiFrame', 'labelSeritGerginligiInfo', 'SeritGerginligi')
            upd('SeritSapmasiFrame', 'labelSeritSapmasiInfo', 'SeritSapmasi')
            upd('TitresimXFrame', 'labelTitresimXInfo', 'TitresimX')
            upd('TitresimYFrame', 'labelTitresimYInfo', 'TitresimY')
            upd('TitresimZFrame', 'labelTitresimZInfo', 'TitresimZ')

        except Exception as e:
            logger.error(f"Error updating sensor values: {e}")

    def _update_cutting_graph(self, data: Dict):
        """Update cutting graph (thread-safe)"""
        try:
            if not self.cutting_graph:
                return

            # Check saw state
            testere_durumu = data.get('testere_durumu', 0)

            # Thread-safe state check
            with self._buffer_lock:
                is_currently_cutting = self.is_cutting

            # Check if cutting started
            if testere_durumu == 3:  # CUTTING
                if not is_currently_cutting:
                    # Cutting started (thread-safe)
                    with self._buffer_lock:
                        self.is_cutting = True
                        self.cut_start_time = datetime.now()
                        self.last_cut_data = []
                        self.current_cut_buffer = collections.deque(maxlen=2000)

                    # Transfer start time to graph for time labels
                    self.cutting_graph.cut_start_time = self.cut_start_time
                    self.cutting_graph.last_point_time = self.cut_start_time
                    # Height start value will be set when first packet arrives
                    self.cutting_graph.start_height_value = None
                    self.cutting_graph.current_height_value = None
                    self.cutting_graph.clear_data()
                    # Restart real-time graph
                    try:
                        if self.cutting_graph and not self.cutting_graph.update_timer.isActive():
                            self.cutting_graph.update_timer.start(100)
                    except Exception:
                        pass
                    logger.info("Cutting started - graph data cleared")

                # Collect data during cutting
                self._add_cutting_data_point(data)

            elif testere_durumu != 3 and is_currently_cutting:
                # Cutting finished (thread-safe)
                with self._buffer_lock:
                    self.is_cutting = False
                # Keep start time, show last cut
                logger.info("Cutting finished")
                # Stop real-time graph (show last cut)
                try:
                    if self.cutting_graph and self.cutting_graph.update_timer.isActive():
                        self.cutting_graph.update_timer.stop()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error updating cutting graph: {e}")

    def _add_cutting_data_point(self, data: Dict):
        """Add data point during cutting (thread-safe)"""
        try:
            # Thread-safe state check
            with self._buffer_lock:
                is_cutting = self.is_cutting
                cut_start = self.cut_start_time

            if not self.cutting_graph or not is_cutting:
                return

            # Add all metrics to buffer
            now_dt = datetime.now()
            elapsed_s = (now_dt - cut_start).total_seconds() if cut_start else 0.0
            buffer_row = {
                'timestamp_dt': now_dt,
                'elapsed_s': float(elapsed_s),
                'serit_kesme_hizi': float(data.get('serit_kesme_hizi', 0.0)),
                'serit_inme_hizi': float(data.get('serit_inme_hizi', 0.0)),
                'serit_motor_akim_a': float(data.get('serit_motor_akim_a', 0.0)),
                'serit_sapmasi': float(data.get('serit_sapmasi', 0.0)),
                'serit_motor_tork_percentage': float(data.get('serit_motor_tork_percentage', 0.0)),
                'kafa_yuksekligi_mm': float(data.get('kafa_yuksekligi_mm', 0.0)),
                'ivme_olcer_x_hz': float(data.get('ivme_olcer_x_hz', 0.0)),
                'ivme_olcer_y_hz': float(data.get('ivme_olcer_y_hz', 0.0)),
                'ivme_olcer_z_hz': float(data.get('ivme_olcer_z_hz', 0.0)),
            }

            # Thread-safe buffer add
            with self._buffer_lock:
                self.current_cut_buffer.append(buffer_row)

            # Update height axis labels start/current values
            try:
                h = buffer_row['kafa_yuksekligi_mm']
                if self.cutting_graph.start_height_value is None:
                    self.cutting_graph.start_height_value = h
                self.cutting_graph.current_height_value = h
            except Exception:
                pass

            # Add last point to graph based on selected axes
            x_axis = self.cutting_graph.x_axis_type
            y_axis = self.cutting_graph.y_axis_type

            x_value = self._get_value_for_axis_from_buffer(buffer_row, x_axis)
            y_value = self._get_value_for_axis_from_buffer(buffer_row, y_axis)

            self.cutting_graph.add_data_point(float(x_value), float(y_value))

            # Save last cut data
            self.last_cut_data.append({
                'timestamp': datetime.now(),
                'x_value': x_value,
                'y_value': y_value,
                'x_axis': x_axis,
                'y_axis': y_axis
            })

        except Exception as e:
            logger.error(f"Error adding data point: {e}")

    def _get_value_for_axis_from_buffer(self, row: Dict, axis_type: str) -> float:
        """Get axis value from buffer row"""
        try:
            if axis_type == "timestamp":
                return float(row.get('elapsed_s', 0.0))
            elif axis_type == "serit_kesme_hizi":
                return float(row.get('serit_kesme_hizi', 0.0))
            elif axis_type == "serit_inme_hizi":
                return float(row.get('serit_inme_hizi', 0.0))
            elif axis_type == "serit_motor_akim_a":
                return float(row.get('serit_motor_akim_a', 0.0))
            elif axis_type == "serit_sapmasi":
                return float(row.get('serit_sapmasi', 0.0))
            elif axis_type == "serit_motor_tork_percentage":
                return float(row.get('serit_motor_tork_percentage', 0.0))
            elif axis_type == "kafa_yuksekligi_mm":
                return float(row.get('kafa_yuksekligi_mm', 0.0))
            else:
                return 0.0
        except Exception:
            return 0.0

    def _rebuild_graph_from_buffer(self):
        """Rebuild graph from buffer based on selected axes (thread-safe)"""
        try:
            # Thread-safe buffer copy
            with self._buffer_lock:
                if not self.cutting_graph or not self.current_cut_buffer:
                    return
                buffer_copy = list(self.current_cut_buffer)
                cut_start = self.cut_start_time

            # Clear graph
            self.cutting_graph.clear_data()

            x_axis = self.cutting_graph.x_axis_type
            y_axis = self.cutting_graph.y_axis_type

            # Time labels start/end
            if cut_start:
                self.cutting_graph.cut_start_time = cut_start
            first_dt = buffer_copy[0].get('timestamp_dt', None)
            last_dt = buffer_copy[-1].get('timestamp_dt', None)
            if first_dt and last_dt:
                self.cutting_graph.cut_start_time = first_dt
                self.cutting_graph.last_point_time = last_dt
            # Height start/current values from buffer
            try:
                first_h = buffer_copy[0].get('kafa_yuksekligi_mm', None)
                last_h = buffer_copy[-1].get('kafa_yuksekligi_mm', None)
                if first_h is not None and last_h is not None:
                    self.cutting_graph.start_height_value = float(first_h)
                    self.cutting_graph.current_height_value = float(last_h)
            except Exception:
                pass

            for row in buffer_copy:
                x_value = self._get_value_for_axis_from_buffer(row, x_axis)
                y_value = self._get_value_for_axis_from_buffer(row, y_axis)
                self.cutting_graph.add_data_point(float(x_value), float(y_value))

            logger.info("Graph rebuilt from buffer")
            # Redraw
            try:
                self.cutting_graph.update()
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error rebuilding graph from buffer: {e}")

    def _load_last_cut_data(self):
        """Load last cut data from database - only if not currently cutting (thread-safe)"""
        try:
            # Thread-safe state check
            with self._buffer_lock:
                is_cutting = self.is_cutting

            # If currently cutting, don't load historical data
            if is_cutting:
                logger.info("Cutting in progress, not loading historical data")
                return

            # Placeholder - implement database loading if needed
            logger.info("Last cut data loading (placeholder)")

        except Exception as e:
            logger.error(f"Error loading last cut data: {e}")

    def update_data(self, data: dict):
        """
        Update display with latest data.

        Args:
            data: Dictionary containing sensor data
        """
        try:
            self._update_sensor_values(data)
        except Exception as e:
            logger.error(f"Error updating data: {e}")

    def stop_timers(self):
        """
        Stop all QTimers in this controller.

        IMPORTANT: Must be called from the GUI thread before window closes
        to avoid segmentation fault on Linux.
        """
        try:
            if hasattr(self, '_data_timer') and self._data_timer:
                self._data_timer.stop()
            if hasattr(self, 'cutting_graph') and self.cutting_graph:
                if hasattr(self.cutting_graph, 'update_timer'):
                    self.cutting_graph.update_timer.stop()
            logger.debug("SensorController timers stopped")
        except Exception as e:
            logger.error(f"Error stopping sensor controller timers: {e}")
