"""
Main window controller - 1920x1080 fullscreen with sidebar navigation.

PySide6 implementation with proper Qt lifecycle management.
"""

import logging
import os
from typing import Optional
from datetime import datetime

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QFrame, QPushButton, QStackedWidget, QLabel
    )
    from PySide6.QtCore import QTimer, Signal, Slot, Qt, QSize
    from PySide6.QtGui import QFont, QIcon, QKeyEvent
except ImportError:
    logging.warning("PySide6 not installed")
    QMainWindow = object
    Signal = lambda *args, **kwargs: None
    Slot = lambda *args, **kwargs: (lambda f: f)

from .control_panel_controller import ControlPanelController
from .monitoring_controller import MonitoringController
from .positioning_controller import PositioningController
from .sensor_controller import SensorController

logger = logging.getLogger(__name__)


class MainController(QMainWindow):
    """
    Main window - 1920x1080 fullscreen with sidebar navigation.

    Layout:
    - Sidebar (392x1080) - left navigation with gradient background
    - Notification bar (top) - date/time display
    - Content area (stacked pages) - page switching

    PySide6 handles all Qt object cleanup automatically.
    """

    data_updated = Signal(dict)

    def __init__(self, control_manager, data_pipeline):
        """Initialize main controller."""
        super().__init__()

        self.control_manager = control_manager
        self.data_pipeline = data_pipeline

        # Setup UI
        self._setup_ui()

        # Timers - parent is self, Qt will handle cleanup automatically
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._on_timer_update)
        self._update_timer.start(200)  # 5 Hz

        self._datetime_timer = QTimer(self)
        self._datetime_timer.timeout.connect(self._update_datetime)
        self._datetime_timer.start(1000)  # 1 Hz

        self.data_updated.connect(self._on_data_updated)

        logger.info("MainController initialized (1920x1080)")

    def _icon(self, name: str) -> QIcon:
        """Load icon from images folder."""
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
        return QIcon(os.path.join(base, name))

    def _setup_ui(self):
        """Setup main window UI - 1920x1080 fullscreen."""
        # Window properties
        self.setWindowTitle("Smart Band Saw Control System")
        self.setFixedSize(1920, 1080)

        # Central widget with background
        central_widget = QWidget(self)
        central_widget.setObjectName("centralwidget")
        central_widget.setStyleSheet("""
            QWidget#centralwidget {
                background-image: url("src/gui/images/background.png");
                background-repeat: no-repeat;
                background-position: center;
            }
        """)
        self.setCentralWidget(central_widget)

        # ===== SIDEBAR FRAME (392x1080) =====
        self.sidebarFrame = QFrame(central_widget)
        self.sidebarFrame.setGeometry(0, 0, 392, 1080)
        self.sidebarFrame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                border-radius: 20px;
            }
        """)

        # Logo "SMART"
        self.labelSmart = QLabel("SMART", self.sidebarFrame)
        self.labelSmart.setGeometry(31, 32, 330, 73)
        self.labelSmart.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 58px;
            }
        """)

        # Logo "SAW"
        self.labelSaw = QLabel("SAW", self.sidebarFrame)
        self.labelSaw.setGeometry(230, 32, 150, 73)
        self.labelSaw.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: 100;
                font-size: 58px;
            }
        """)

        # Separator line
        self.lineSmartSaw = QFrame(self.sidebarFrame)
        self.lineSmartSaw.setGeometry(30, 110, 332, 3)
        self.lineSmartSaw.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255,255,255,0),
                    stop:0.5 rgba(255,255,255,100),
                    stop:1 rgba(255,255,255,0)
                );
            }
        """)

        # Navigation button style
        nav_btn_style = """
            QPushButton {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: 600;
                font-size: 32px;
                text-align: left;
                padding: 12px 10px 12px 25px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            QPushButton:checked {
                background-color: rgba(26, 31, 55, 128);
            }
        """

        # Navigation buttons
        self.btnControlPanel = QPushButton("  Kontrol Paneli", self.sidebarFrame)
        self.btnControlPanel.setGeometry(26, 165, 355, 110)
        self.btnControlPanel.setIcon(self._icon("control-panel-icon2.svg"))
        self.btnControlPanel.setIconSize(QSize(70, 70))
        self.btnControlPanel.setStyleSheet(nav_btn_style)
        self.btnControlPanel.setCheckable(True)
        self.btnControlPanel.setChecked(True)
        self.btnControlPanel.clicked.connect(lambda: self._switch_page(0))

        self.btnPositioning = QPushButton("  Konumlandırma", self.sidebarFrame)
        self.btnPositioning.setGeometry(26, 286, 355, 110)
        self.btnPositioning.setIcon(self._icon("positioning-icon2.svg"))
        self.btnPositioning.setIconSize(QSize(80, 80))
        self.btnPositioning.setStyleSheet(nav_btn_style)
        self.btnPositioning.setCheckable(True)
        self.btnPositioning.clicked.connect(lambda: self._switch_page(1))

        self.btnSensor = QPushButton("  Sensör Verileri", self.sidebarFrame)
        self.btnSensor.setGeometry(26, 407, 355, 110)
        self.btnSensor.setIcon(self._icon("sensor-icon2.svg"))
        self.btnSensor.setIconSize(QSize(80, 80))
        self.btnSensor.setStyleSheet(nav_btn_style)
        self.btnSensor.setCheckable(True)
        self.btnSensor.clicked.connect(lambda: self._switch_page(2))

        self.btnTracking = QPushButton("  İzleme", self.sidebarFrame)
        self.btnTracking.setGeometry(27, 528, 355, 110)
        self.btnTracking.setIcon(self._icon("tracking-icon2.svg"))
        self.btnTracking.setIconSize(QSize(80, 80))
        self.btnTracking.setStyleSheet(nav_btn_style)
        self.btnTracking.setCheckable(True)
        self.btnTracking.clicked.connect(lambda: self._switch_page(3))

        # Store navigation buttons
        self.nav_buttons = [
            self.btnControlPanel,
            self.btnPositioning,
            self.btnSensor,
            self.btnTracking
        ]

        # ===== NOTIFICATION FRAME (Top Bar) =====
        self.notificationFrame = QFrame(central_widget)
        self.notificationFrame.setGeometry(425, 38, 1465, 60)
        self.notificationFrame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 31, 55, 77);
                border-radius: 30px;
            }
        """)

        # Date label
        self.labelDate = QLabel(self.notificationFrame)
        self.labelDate.setGeometry(55, 13, 300, 34)
        self.labelDate.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: 300;
                font-size: 24px;
            }
        """)

        # Time label
        self.labelTime = QLabel(self.notificationFrame)
        self.labelTime.setGeometry(1348, 13, 62, 34)
        self.labelTime.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: 300;
                font-size: 24px;
            }
        """)

        # ===== CONTENT AREA (Stacked Pages) =====
        self.stackedWidget = QStackedWidget(central_widget)
        self.stackedWidget.setGeometry(392, 0, 1528, 1080)
        self.stackedWidget.setStyleSheet("background-color: transparent;")

        # Create pages - all have self.stackedWidget as parent
        # Qt will handle cleanup automatically
        self.control_panel_page = ControlPanelController(
            self.control_manager,
            self.data_pipeline,
            parent=self.stackedWidget
        )
        self.positioning_page = PositioningController(
            self.control_manager,
            self.data_pipeline,
            parent=self.stackedWidget
        )
        self.sensor_page = SensorController(
            self.control_manager,
            self.data_pipeline,
            parent=self.stackedWidget
        )
        self.monitoring_page = MonitoringController(
            self.control_manager,
            self.data_pipeline,
            parent=self.stackedWidget
        )

        # Add pages to stack
        self.stackedWidget.addWidget(self.control_panel_page)  # Index 0
        self.stackedWidget.addWidget(self.positioning_page)    # Index 1
        self.stackedWidget.addWidget(self.sensor_page)         # Index 2
        self.stackedWidget.addWidget(self.monitoring_page)     # Index 3

        # Update date/time
        self._update_datetime()

    def _switch_page(self, index: int):
        """Switch to page by index."""
        try:
            # Uncheck all navigation buttons
            for btn in self.nav_buttons:
                btn.setChecked(False)

            # Check clicked button
            self.nav_buttons[index].setChecked(True)

            # Switch page
            self.stackedWidget.setCurrentIndex(index)

            logger.debug(f"Switched to page {index}")

        except Exception as e:
            logger.error(f"Error switching page: {e}")

    def _update_datetime(self):
        """Update date and time labels."""
        try:
            now = datetime.now()

            # Turkish day names
            day_names_tr = {
                0: "Pazartesi",
                1: "Salı",
                2: "Çarşamba",
                3: "Perşembe",
                4: "Cuma",
                5: "Cumartesi",
                6: "Pazar"
            }

            day_name = day_names_tr.get(now.weekday(), "")
            date_str = now.strftime(f"%d.%m.%Y {day_name}")
            time_str = now.strftime("%H:%M")

            self.labelDate.setText(date_str)
            self.labelTime.setText(time_str)

        except Exception as e:
            logger.error(f"Error updating datetime: {e}")

    def _on_timer_update(self):
        """Timer callback for periodic updates."""
        try:
            if self.data_pipeline:
                # Get latest data from pipeline
                stats = self.data_pipeline.get_stats()
                # Emit signal for thread-safe update
                # self.data_updated.emit(stats)

        except Exception as e:
            logger.error(f"Error in timer update: {e}")

    @Slot(dict)
    def _on_data_updated(self, data: dict):
        """Handle data updates (thread-safe)."""
        try:
            # Update current page
            current_page = self.stackedWidget.currentWidget()
            if hasattr(current_page, 'update_data'):
                current_page.update_data(data)

        except Exception as e:
            logger.error(f"Error updating data: {e}")

    def update_data(self, data: dict):
        """External data update (can be called from any thread)."""
        self.data_updated.emit(data)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        try:
            if event.key() == Qt.Key_Q:
                logger.info("Q key pressed - closing application")
                self.close()
            else:
                super().keyPressEvent(event)
        except Exception as e:
            logger.error(f"Error in keyPressEvent: {e}")

    def closeEvent(self, event):
        """
        Handle window close event.

        PySide6 automatically handles:
        - QTimer cleanup (no manual stop/deleteLater needed)
        - Child widget cleanup (parent-child relationship)
        - Signal/Slot disconnection

        We just need to accept the event.
        """
        logger.info("Main window closing - PySide6 handles cleanup automatically")
        event.accept()
