"""
OtomatikKesimController - Auto cutting page controller.

Full-page widget for automatic cutting operations:
- 5 parameter input frames (P, X, L, C, S)
- Real-time cut counter with progress bar
- START, RESET, IPTAL control buttons
- ML mode toggle (Manuel/Yapay Zeka)

Page size: 1528x1080 (content area)
Framework: PySide6
"""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QLabel
    from PySide6.QtCore import Qt, QTimer, QRect
    from PySide6.QtGui import QPainter, QColor
except ImportError:
    logging.warning("PySide6 not installed")
    QWidget = object
    QFrame = object
    QPushButton = object
    QLabel = object
    Qt = object
    QTimer = object
    QRect = object
    QPainter = object
    QColor = object

from ...services.control.machine_control import MachineControl
from ..widgets.touch_button import TouchButton

logger = logging.getLogger(__name__)


class _ProgressBar(QWidget):
    """
    Custom horizontal progress bar drawn with QPainter.

    Attributes:
        _progress: float 0.0-1.0 representing fill amount.
        _complete: bool switches fill color to semantic-success green.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress: float = 0.0
        self._complete: bool = False

    def set_progress(self, value: float, complete: bool = False) -> None:
        """Update progress (0.0-1.0) and repaint."""
        self._progress = max(0.0, min(1.0, value))
        self._complete = complete
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint background then fill proportional to _progress."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h // 2

        # Background
        painter.setBrush(QColor(26, 31, 55, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        # Fill
        if self._progress > 0:
            fill_w = int(w * self._progress)
            if self._complete:
                painter.setBrush(QColor("#22C55E"))
            else:
                painter.setBrush(QColor("#950952"))
            painter.drawRoundedRect(0, 0, fill_w, h, radius, radius)

        painter.end()


class OtomatikKesimController(QWidget):
    """
    Auto cutting page controller.

    Features:
    - P, X, L, C, S parameter input via NumpadDialog
    - Real-time cut counter via 500ms QTimer polling D2056
    - START/RESET/IPTAL control buttons
    - ML mode toggle (Manuel/Yapay Zeka)
    - Parameter lockout during active cutting
    """

    def __init__(
        self,
        control_manager=None,
        data_pipeline=None,
        parent=None,
        event_loop=None,
    ):
        super().__init__(parent)
        self.control_manager = control_manager
        self.data_pipeline = data_pipeline
        self.event_loop = event_loop

        # MachineControl singleton
        self.machine_control: Optional[MachineControl] = None
        self._initialize_machine_control()

        # Parameter state
        self._p_value: str = ""    # Hedef adet (1-9999)
        self._x_value: str = ""    # Paketteki adet (1-999)
        self._l_value: str = ""    # Uzunluk mm (1-99999, decimal)
        self._c_value: str = ""    # Kesim hizi m/dk (0-500)
        self._s_value: str = ""    # Inme hizi m/dk (0-500)

        # Control state
        self._params_enabled: bool = True
        self._cutting_active: bool = False
        self._previous_count: Optional[int] = None  # None = first poll (Pitfall 4)

        # RESET hold state
        self._reset_in_progress: bool = False
        self._reset_start: float = 0.0
        self._reset_progress: float = 0.0

        # Timers (initialized in _setup_timers)
        self._polling_timer: Optional[QTimer] = None
        self._reset_tick_timer: Optional[QTimer] = None

        # Styles stored as instance attributes for reuse
        self._frame_style = (
            "background: qlineargradient("
            "x1:0,y1:1,x2:0.5,y2:0,"
            "stop:0 rgba(6,11,38,240),"
            "stop:1 rgba(26,31,55,0)"
            "); border-radius: 20px;"
        )
        self._frame_disabled_style = (
            "background: rgba(26,31,55,100); border-radius: 20px;"
        )
        self._button_default_style = """
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:1, x2:0, y2:0,
                    stop:0 #000000, stop:0.38 rgba(26,31,55,200)
                );
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                background-color: rgba(26, 31, 55, 100);
                color: rgba(244, 246, 252, 100);
                border: 2px solid rgba(244, 246, 252, 100);
            }
        """
        self._button_checked_style = """
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(149,9,82,255), stop:1 rgba(26,31,55,255)
                );
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
        """
        self._button_destructive_style = """
            QPushButton {
                background-color: #DC2626;
                color: #FFFFFF;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                border-radius: 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
            QPushButton:pressed {
                background-color: #991B1B;
            }
        """
        self._button_start_style = """
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:1, x2:0.5, y2:0,
                    stop:0 rgba(6,11,38,240), stop:1 rgba(26,31,55,0)
                );
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                background-color: rgba(26, 31, 55, 100);
                color: rgba(244, 246, 252, 100);
                border: 2px solid rgba(244, 246, 252, 100);
            }
        """
        self._reset_button_style = """
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:1, x2:0, y2:0,
                    stop:0 #000000, stop:0.38 rgba(26,31,55,200)
                );
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """

        # Setup
        self._setup_ui()
        self._setup_timers()

        logger.info("OtomatikKesimController initialized")

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def _initialize_machine_control(self) -> None:
        """Initialize MachineControl singleton (uses its own Modbus connection)."""
        try:
            self.machine_control = MachineControl()
            logger.info("MachineControl initialized for OtomatikKesimController")
        except Exception as e:
            logger.error(f"Failed to initialize MachineControl: {e}")
            self.machine_control = None

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the complete two-column absolute-coordinate layout."""
        self.setMinimumSize(1528, 1080)
        self.setStyleSheet("background-color: transparent;")

        # ---- LEFT COLUMN: PARAM FRAMES -----

        # P frame (30,30,340,160)
        self._create_param_frame(
            parent=self,
            x=30, y=30, w=340, h=160,
            title="P \u2014 Hedef Adet",
            hint="(1 - 9999)",
            attr_prefix="P",
        )

        # X frame (380,30,340,160)
        self._create_param_frame(
            parent=self,
            x=380, y=30, w=340, h=160,
            title="X \u2014 Paketteki Adet",
            hint="(1 - 999)",
            attr_prefix="X",
        )

        # P*X total label (30,200,690,40)
        self.labelTotal = QLabel(self)
        self.labelTotal.setGeometry(30, 200, 690, 40)
        self.labelTotal.setText("Toplam: 0 adet")
        self.labelTotal.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 16px 'Plus Jakarta Sans';"
            " font-weight: 500;"
        )

        # L frame (30,255,690,140)
        self._create_param_frame(
            parent=self,
            x=30, y=255, w=690, h=140,
            title="L \u2014 Uzunluk (mm)",
            hint="(1 - 99999, ondal\u0131kl\u0131)",
            attr_prefix="L",
        )

        # C frame (30,410,690,140)
        self._create_param_frame(
            parent=self,
            x=30, y=410, w=690, h=140,
            title="C \u2014 Kesim H\u0131z\u0131 (m/dk)",
            hint="(0 - 500)",
            attr_prefix="C",
        )

        # S frame (30,565,690,140)
        self._create_param_frame(
            parent=self,
            x=30, y=565, w=690, h=140,
            title="S \u2014 \u0130nme H\u0131z\u0131 (m/dk)",
            hint="(0 - 500)",
            attr_prefix="S",
        )

        # ---- RIGHT COLUMN: COUNTER FRAME (760,30,740,380) ----

        self.frameCounter = QFrame(self)
        self.frameCounter.setGeometry(760, 30, 740, 380)
        self.frameCounter.setStyleSheet(self._frame_style)

        self.labelCounterTitle = QLabel(self.frameCounter)
        self.labelCounterTitle.setGeometry(20, 15, 700, 35)
        self.labelCounterTitle.setText("Saya\u00e7")
        self.labelCounterTitle.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )

        self.labelCounter = QLabel(self.frameCounter)
        self.labelCounter.setGeometry(20, 55, 700, 110)
        self.labelCounter.setText("0 / 0")
        self.labelCounter.setAlignment(Qt.AlignCenter)
        self.labelCounter.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 80px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )

        # Progress bar (custom painted widget)
        self.progressWidget = _ProgressBar(self.frameCounter)
        self.progressWidget.setGeometry(20, 175, 700, 24)

        # Completion overlay label (hidden until complete)
        self.labelComplete = QLabel(self.frameCounter)
        self.labelComplete.setGeometry(20, 210, 700, 40)
        self.labelComplete.setText("Tamamland\u0131!")
        self.labelComplete.setAlignment(Qt.AlignCenter)
        self.labelComplete.setStyleSheet(
            "background: transparent;"
            " color: #22C55E;"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )
        self.labelComplete.hide()

        # ---- RIGHT COLUMN: CONTROL FRAME (760,425,740,625) ----

        self.frameControl = QFrame(self)
        self.frameControl.setGeometry(760, 425, 740, 625)
        self.frameControl.setStyleSheet(self._frame_style)

        # Validation error label below START (hidden by default)
        self.labelValidationError = QLabel(self.frameControl)
        self.labelValidationError.setGeometry(30, 115, 680, 30)
        self.labelValidationError.setText("")
        self.labelValidationError.setStyleSheet(
            "background: transparent;"
            " color: #DC2626;"
            " font: 20px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )
        self.labelValidationError.hide()

        # START button (30,30,680,80)
        self.btnStart = QPushButton("START", self.frameControl)
        self.btnStart.setGeometry(30, 30, 680, 80)
        self.btnStart.setStyleSheet(self._button_start_style)
        self.btnStart.setCursor(Qt.PointingHandCursor)

        # RESET button as TouchButton (30,130,680,80)
        self.btnReset = TouchButton(self.frameControl)
        self.btnReset.setGeometry(30, 130, 680, 80)
        self.btnReset.setText("RESET")
        self.btnReset.setStyleSheet(self._reset_button_style)
        self.btnReset.setCursor(Qt.PointingHandCursor)

        # IPTAL button (30,230,680,80)
        self.btnIptal = QPushButton("\u0130PTAL", self.frameControl)
        self.btnIptal.setGeometry(30, 230, 680, 80)
        self.btnIptal.setStyleSheet(self._button_destructive_style)
        self.btnIptal.setCursor(Qt.PointingHandCursor)

        # ML mode toggle buttons (30,360,320,55) and (360,360,320,55)
        self.btnManual = QPushButton("Manuel", self.frameControl)
        self.btnManual.setGeometry(30, 360, 320, 55)
        self.btnManual.setCheckable(True)
        self.btnManual.setChecked(True)
        self.btnManual.setStyleSheet(self._button_checked_style)
        self.btnManual.setCursor(Qt.PointingHandCursor)

        self.btnAI = QPushButton("Yapay Zeka", self.frameControl)
        self.btnAI.setGeometry(360, 360, 320, 55)
        self.btnAI.setCheckable(True)
        self.btnAI.setChecked(False)
        self.btnAI.setStyleSheet(self._button_default_style)
        self.btnAI.setCursor(Qt.PointingHandCursor)

    def _create_param_frame(
        self,
        parent,
        x: int,
        y: int,
        w: int,
        h: int,
        title: str,
        hint: str,
        attr_prefix: str,
    ) -> QFrame:
        """
        Create a parameter input frame with title, hint, and value labels.

        Stores frame and labels as instance attributes using attr_prefix.
        """
        frame = QFrame(parent)
        frame.setGeometry(x, y, w, h)
        frame.setStyleSheet(self._frame_style)
        frame.setCursor(Qt.PointingHandCursor)

        title_label = QLabel(frame)
        title_label.setGeometry(20, 15, w - 40, 30)
        title_label.setText(title)
        title_label.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )

        hint_label = QLabel(frame)
        hint_label.setGeometry(20, 45, w - 40, 25)
        hint_label.setText(hint)
        hint_label.setStyleSheet(
            "background: transparent;"
            " color: rgba(244,246,252,150);"
            " font: 16px 'Plus Jakarta Sans';"
            " font-weight: 500;"
        )

        value_label = QLabel(frame)
        value_label.setGeometry(20, 75, w - 40, h - 90)
        value_label.setText("\u2014")  # em dash — indicates no value entered
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )

        setattr(self, f"frame{attr_prefix}", frame)
        setattr(self, f"label{attr_prefix}Title", title_label)
        setattr(self, f"label{attr_prefix}Hint", hint_label)
        setattr(self, f"label{attr_prefix}Value", value_label)
        return frame

    # -------------------------------------------------------------------------
    # Timer Setup
    # -------------------------------------------------------------------------

    def _setup_timers(self) -> None:
        """Create timers but do NOT start them (behavior wired in Plan 02/03)."""
        self._polling_timer = QTimer(self)
        self._polling_timer.setInterval(500)
        # timeout connection wired in Plan 03

        self._reset_tick_timer = QTimer(self)
        self._reset_tick_timer.setInterval(50)
        # timeout connection wired in Plan 03

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def stop_timers(self) -> None:
        """
        Stop all QTimers.

        Must be called from the GUI thread before window closes to prevent
        segmentation faults on Linux.
        """
        if hasattr(self, '_polling_timer') and self._polling_timer:
            self._polling_timer.stop()
        if hasattr(self, '_reset_tick_timer') and self._reset_tick_timer:
            self._reset_tick_timer.stop()
        logger.debug("OtomatikKesimController timers stopped")

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _set_params_enabled(self, enabled: bool) -> None:
        """Enable or disable all parameter input frames."""
        self._params_enabled = enabled
        frames = [self.frameP, self.frameX, self.frameL, self.frameC, self.frameS]
        for frame in frames:
            frame.setEnabled(enabled)
            if enabled:
                frame.setStyleSheet(self._frame_style)
                frame.setCursor(Qt.PointingHandCursor)
            else:
                frame.setStyleSheet(self._frame_disabled_style)
                frame.setCursor(Qt.ArrowCursor)

        # Update value label colors to reflect enabled/disabled state
        labels = [
            self.labelPValue,
            self.labelXValue,
            self.labelLValue,
            self.labelCValue,
            self.labelSValue,
        ]
        value_style_enabled = (
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )
        value_style_disabled = (
            "background: transparent;"
            " color: rgba(244,246,252,100);"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )
        for label in labels:
            label.setStyleSheet(
                value_style_enabled if enabled else value_style_disabled
            )

    def _update_total_label(self) -> None:
        """Compute P * X and update the Toplam label."""
        try:
            p = int(self._p_value) if self._p_value else 0
            x = int(self._x_value) if self._x_value else 0
            total = p * x
            self.labelTotal.setText(f"Toplam: {total} adet")
        except (ValueError, TypeError):
            self.labelTotal.setText("Toplam: 0 adet")
