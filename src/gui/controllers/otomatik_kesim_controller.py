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

import asyncio
import logging
import time
from typing import Optional

try:
    from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QLabel, QDialog
    from PySide6.QtCore import Qt, QTimer, QRect, Signal
    from PySide6.QtGui import QPainter, QColor
except ImportError:
    logging.warning("PySide6 not installed")
    QWidget = object
    QFrame = object
    QPushButton = object
    QLabel = object
    QDialog = object
    Qt = object
    QTimer = object
    QRect = object
    QPainter = object
    QColor = object

from ...domain.enums import ControlMode
from ...services.control.machine_control import MachineControl
from ..widgets.touch_button import TouchButton

try:
    from ..numpad import NumpadDialog
except ImportError:
    from PySide6.QtWidgets import QDialog as NumpadDialog  # type: ignore[misc]

logger = logging.getLogger(__name__)


class _ClickableFrame(QFrame):
    """QFrame that emits a clicked signal on mouse press."""
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        event.accept()


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
        self._x_value: str = "1"   # Paketteki adet (1-999), default 1
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
            "x1:0, y1:0, x2:0, y2:1,"
            "stop:0 rgba(6, 11, 38, 240),"
            "stop:1 rgba(26, 31, 55, 0)"
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

        # Set X default label
        self.labelXValue.setText("1")

        # Sync ML button state from current control_manager mode (D-17)
        self._sync_ml_mode()

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

        # P frame (30,127,340,160)
        self._create_param_frame(
            parent=self,
            x=30, y=127, w=340, h=160,
            title="P \u2014 Paketteki Adet",
            hint="(1 - 9999)",
            attr_prefix="P",
        )

        # X frame (380,127,340,160)
        self._create_param_frame(
            parent=self,
            x=380, y=127, w=340, h=160,
            title="X \u2014 Paket Sayısı",
            hint="(1 - 999)",
            attr_prefix="X",
        )

        # P*X total label (30,297,690,40)
        self.labelTotal = QLabel(self)
        self.labelTotal.setGeometry(30, 297, 690, 40)
        self.labelTotal.setText("Toplam: 0 adet")
        self.labelTotal.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 16px 'Plus Jakarta Sans';"
            " font-weight: 500;"
        )

        # L frame (30,352,690,140)
        self._create_param_frame(
            parent=self,
            x=30, y=352, w=690, h=140,
            title="L \u2014 Uzunluk (mm)",
            hint="(1 - 99999, ondal\u0131kl\u0131)",
            attr_prefix="L",
        )

        # C frame (30,507,690,140)
        self._create_param_frame(
            parent=self,
            x=30, y=507, w=690, h=140,
            title="C \u2014 Kesim H\u0131z\u0131 (m/dk)",
            hint="(0 - 500)",
            attr_prefix="C",
        )

        # S frame (30,662,690,140)
        self._create_param_frame(
            parent=self,
            x=30, y=662, w=690, h=140,
            title="S \u2014 \u0130lerleme H\u0131z\u0131 (mm/dk)",
            hint="(0 - 500)",
            attr_prefix="S",
        )

        # ---- RIGHT COLUMN: COUNTER FRAME (760,127,740,380) ----

        self.frameCounter = QFrame(self)
        self.frameCounter.setGeometry(760, 127, 740, 380)
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

        # ---- RIGHT COLUMN: CONTROL FRAME (760,522,740,558) ----

        self.frameControl = QFrame(self)
        self.frameControl.setGeometry(760, 522, 740, 558)
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

        # ---- LEFT COLUMN: MODE CARD (30,820,690,130) ----

        self.frameModeCard = QFrame(self)
        self.frameModeCard.setGeometry(30, 820, 690, 130)
        self.frameModeCard.setStyleSheet(self._frame_style)

        self.labelModeTitle = QLabel(self.frameModeCard)
        self.labelModeTitle.setGeometry(20, 15, 300, 30)
        self.labelModeTitle.setText("Kesim Modu")
        self.labelModeTitle.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )

        mode_button_style = """
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000000, stop:0.38 rgba(26, 31, 55, 200)
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
            QPushButton:checked {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(149, 9, 82, 255), stop:1 rgba(26, 31, 55, 255)
                );
            }
        """

        self.btnManual = QPushButton("Manuel", self.frameModeCard)
        self.btnManual.setGeometry(20, 60, 320, 55)
        self.btnManual.setCheckable(True)
        self.btnManual.setChecked(True)
        self.btnManual.setStyleSheet(mode_button_style)
        self.btnManual.setCursor(Qt.PointingHandCursor)

        self.btnAI = QPushButton("Yapay Zeka", self.frameModeCard)
        self.btnAI.setGeometry(350, 60, 320, 55)
        self.btnAI.setCheckable(True)
        self.btnAI.setChecked(False)
        self.btnAI.setStyleSheet(mode_button_style)
        self.btnAI.setCursor(Qt.PointingHandCursor)

        # Wire param frame click handlers
        self.frameP.clicked.connect(self._handle_p_frame_click)
        self.frameX.clicked.connect(self._handle_x_frame_click)
        self.frameL.clicked.connect(self._handle_l_frame_click)
        self.frameC.clicked.connect(self._handle_c_frame_click)
        self.frameS.clicked.connect(self._handle_s_frame_click)

        # Wire control button click handlers
        self.btnStart.clicked.connect(self._handle_start_click)
        self.btnIptal.clicked.connect(self._handle_iptal_click)

        # Wire RESET hold-delay (all 4 signals — Pitfall 1: touchscreen fires both
        # pressed and touch_pressed; guard in _on_reset_press prevents double-fire)
        self.btnReset.pressed.connect(self._on_reset_press)
        self.btnReset.released.connect(self._on_reset_release)
        self.btnReset.touch_pressed.connect(self._on_reset_press)
        self.btnReset.touch_released.connect(self._on_reset_release)

        # Override btnReset paintEvent for progress animation
        self._btnReset_original_paint = self.btnReset.paintEvent
        self.btnReset.paintEvent = self._paint_reset_progress

        # Wire ML mode toggle buttons
        self.btnManual.clicked.connect(lambda: self._switch_to_mode(ControlMode.MANUAL))
        self.btnAI.clicked.connect(lambda: self._switch_to_mode(ControlMode.ML))

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
        frame = _ClickableFrame(parent)
        frame.setGeometry(x, y, w, h)
        frame.setStyleSheet(self._frame_style)
        frame.setCursor(Qt.PointingHandCursor)

        title_label = QLabel(frame)
        title_label.setGeometry(20, 15, w - 40, 30)
        title_label.setText(title)
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        title_label.setStyleSheet(
            "background: transparent;"
            " color: #F4F6FC;"
            " font: 24px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )

        hint_label = QLabel(frame)
        hint_label.setGeometry(20, 45, w - 40, 25)
        hint_label.setText(hint)
        hint_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
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
        value_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
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
        self._polling_timer.timeout.connect(self._on_polling_timer)

        self._reset_tick_timer = QTimer(self)
        self._reset_tick_timer.setInterval(50)
        self._reset_tick_timer.timeout.connect(self._on_reset_tick)

        # Speed sync timer — reads PLC target speeds and updates C/S labels
        self._speed_sync_timer = QTimer(self)
        self._speed_sync_timer.setInterval(500)
        self._speed_sync_timer.timeout.connect(self._sync_speeds_from_plc)
        self._speed_sync_timer.start()

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
        if hasattr(self, '_speed_sync_timer') and self._speed_sync_timer:
            self._speed_sync_timer.stop()
        logger.debug("OtomatikKesimController timers stopped")

    # -------------------------------------------------------------------------
    # Speed Sync
    # -------------------------------------------------------------------------

    def _sync_speeds_from_plc(self):
        """Read PLC registers and update all param labels if changed externally."""
        try:
            if not self.data_pipeline or not hasattr(self.data_pipeline, 'get_latest_data'):
                return
            data = self.data_pipeline.get_latest_data()
            if not data:
                return

            # Target speeds (registers 2066 / 2041)
            cutting = data.get('kesme_hizi_hedef', 0)
            descent = data.get('inme_hizi_hedef', 0)
            cutting_str = str(int(cutting)) if cutting else "0"
            descent_str = str(int(descent)) if descent else "0"
            if self._c_value != cutting_str:
                self._c_value = cutting_str
                self.labelCValue.setText(cutting_str)
            if self._s_value != descent_str:
                self._s_value = descent_str
                self.labelSValue.setText(descent_str)

            # Read P, L, kesilmiş adet from MachineControl
            if self.machine_control:
                # P (target adet, register 2050)
                p_val = self.machine_control.read_target_adet()
                if p_val is not None and p_val > 0:
                    p_str = str(p_val)
                    if self._p_value != p_str:
                        self._p_value = p_str
                        self.labelPValue.setText(p_str)
                        self._update_total_label()

                # L (target uzunluk, register 2064-2065, doubleword /10)
                l_val = self.machine_control.read_target_uzunluk()
                if l_val is not None and l_val > 0:
                    if l_val != int(l_val):
                        l_display = f"{l_val:.1f}"
                    else:
                        l_display = str(int(l_val))
                    l_str = str(l_val)
                    if self._l_value != l_str:
                        self._l_value = l_str
                        self.labelLValue.setText(l_display)

                # Kesilmiş adet (register 2056) — update counter
                count = self.machine_control.read_kesilmis_adet()
                if count is not None:
                    target = self._get_target()
                    self.labelCounter.setText(f"{count} / {target}")
                    if target > 0:
                        progress = min(1.0, count / target)
                        complete = count >= target
                        self.progressWidget.set_progress(progress, complete)
                        self.labelComplete.setVisible(complete)

            # Sync ML mode buttons from control_manager
            if self.control_manager and hasattr(self.control_manager, 'current_mode'):
                current = self.control_manager.current_mode
                self.btnManual.setChecked(current == ControlMode.MANUAL)
                self.btnAI.setChecked(current == ControlMode.ML)
        except Exception as e:
            logger.error(f"Speed sync error: {e}")

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

    # -------------------------------------------------------------------------
    # Parameter Frame Click Handlers
    # -------------------------------------------------------------------------

    def _handle_p_frame_click(self, event=None) -> None:
        """Open NumpadDialog for P (hedef adet) parameter input."""
        if not self._params_enabled:
            return
        if event is not None:
            event.accept()
        dialog = NumpadDialog(self, initial_value=self._p_value or "")
        if dialog.exec() == QDialog.Accepted:
            value_str = dialog.get_value()
            try:
                value = int(float(value_str)) if value_str else 0
            except (ValueError, TypeError):
                value = 0
            value = max(1, min(9999, value))
            if value <= 0:
                self._p_value = ""
                self.labelPValue.setText("\u2014")
            else:
                self._p_value = str(value)
                self.labelPValue.setText(str(value))
            self._update_total_label()

    def _handle_x_frame_click(self, event=None) -> None:
        """Open NumpadDialog for X (paketteki adet) parameter input."""
        if not self._params_enabled:
            return
        if event is not None:
            event.accept()
        dialog = NumpadDialog(self, initial_value=self._x_value or "")
        if dialog.exec() == QDialog.Accepted:
            value_str = dialog.get_value()
            try:
                value = int(float(value_str)) if value_str else 0
            except (ValueError, TypeError):
                value = 0
            value = max(1, min(999, value))
            if value <= 0:
                self._x_value = ""
                self.labelXValue.setText("\u2014")
            else:
                self._x_value = str(value)
                self.labelXValue.setText(str(value))
            self._update_total_label()

    def _handle_l_frame_click(self, event=None) -> None:
        """Open NumpadDialog for L (uzunluk mm, decimal) parameter input."""
        if not self._params_enabled:
            return
        if event is not None:
            event.accept()
        dialog = NumpadDialog(self, initial_value=self._l_value or "", allow_decimal=True)
        if dialog.exec() == QDialog.Accepted:
            value_str = dialog.get_value()
            try:
                value = float(value_str) if value_str else 0.0
            except (ValueError, TypeError):
                value = 0.0
            value = round(max(1.0, min(99999.0, value)), 1)
            if value <= 0:
                self._l_value = ""
                self.labelLValue.setText("\u2014")
            else:
                display = f"{value:.1f}" if value != int(value) else str(int(value))
                self._l_value = str(value)
                self.labelLValue.setText(display)

    def _handle_c_frame_click(self, event=None) -> None:
        """Open NumpadDialog for C (kesim hizi) parameter input and write to PLC."""
        if not self._params_enabled:
            return
        if event is not None:
            event.accept()
        dialog = NumpadDialog(self, initial_value=self._c_value or "")
        if dialog.exec() == QDialog.Accepted:
            value_str = dialog.get_value()
            try:
                value = int(float(value_str)) if value_str else 0
            except (ValueError, TypeError):
                value = 0
            value = max(0, min(500, value))
            self._c_value = str(value)
            self.labelCValue.setText(str(value))
            if self.machine_control:
                self.machine_control.write_cutting_speed(value)

    def _handle_s_frame_click(self, event=None) -> None:
        """Open NumpadDialog for S (inme hizi) parameter input and write to PLC."""
        if not self._params_enabled:
            return
        if event is not None:
            event.accept()
        dialog = NumpadDialog(self, initial_value=self._s_value or "")
        if dialog.exec() == QDialog.Accepted:
            value_str = dialog.get_value()
            try:
                value = int(float(value_str)) if value_str else 0
            except (ValueError, TypeError):
                value = 0
            value = max(0, min(500, value))
            self._s_value = str(value)
            self.labelSValue.setText(str(value))
            if self.machine_control:
                self.machine_control.write_descent_speed(float(value))

    # -------------------------------------------------------------------------
    # START / IPTAL Button Handlers
    # -------------------------------------------------------------------------

    def _validate_params(self) -> Optional[str]:
        """Validate P, L, X mandatory params. Returns Turkish error string or None."""
        if not self._p_value or int(self._p_value) <= 0:
            return "P (hedef adet) girilmedi"
        if not self._l_value or float(self._l_value) <= 0:
            return "L (uzunluk) girilmedi"
        if not self._x_value or int(self._x_value) <= 0:
            return "X (paketteki adet) girilmedi"
        return None

    def _show_validation_error(self, message: str) -> None:
        """Show validation error label for 3 seconds."""
        self.labelValidationError.setText(message)
        self.labelValidationError.setVisible(True)
        QTimer.singleShot(3000, lambda: self.labelValidationError.setVisible(False))

    def _handle_start_click(self) -> None:
        """Validate params, write to PLC registers, then start auto cutting."""
        error = self._validate_params()
        if error:
            self._show_validation_error(error)
            return

        p = int(self._p_value)
        x = int(self._x_value)
        l_mm = float(self._l_value)

        if self.machine_control:
            # Write all params BEFORE starting (Pitfall 6: prevent zero/null to PLC)
            self.machine_control.write_target_adet(p, x)
            self.machine_control.write_target_uzunluk(l_mm)
            if self._c_value:
                self.machine_control.write_cutting_speed(int(self._c_value))
            if self._s_value:
                self.machine_control.write_descent_speed(float(self._s_value))
            self.machine_control.start_auto_cutting()

        # UI updates per D-10
        self.btnStart.setEnabled(False)
        self.btnStart.setText("DEVAM EDIYOR...")
        self._set_params_enabled(False)
        self._cutting_active = True

        # Start polling
        if self._polling_timer and not self._polling_timer.isActive():
            self._polling_timer.start()

    def _handle_iptal_click(self) -> None:
        """Cancel auto cutting and reset all UI state."""
        if self.machine_control:
            self.machine_control.cancel_auto_cutting()
        self._set_params_enabled(True)
        self._cutting_active = False
        self.btnStart.setEnabled(True)
        self.btnStart.setText("START")
        self.labelCounter.setText("0 / 0")
        self._previous_count = None  # reset ML detection

        # Reset progress bar
        self.progressWidget._progress = 0.0
        self.progressWidget._complete = False
        self.progressWidget.update()

        self.labelComplete.setVisible(False)

        # Stop polling
        if self._polling_timer and self._polling_timer.isActive():
            self._polling_timer.stop()

    def _get_target(self) -> int:
        """Return P * X total target, or 0 if not set."""
        try:
            return (
                int(self._p_value) * int(self._x_value)
                if self._p_value and self._x_value
                else 0
            )
        except (ValueError, TypeError):
            return 0

    # -------------------------------------------------------------------------
    # RESET Hold-Delay (D-11, T-26-06, T-26-08)
    # -------------------------------------------------------------------------

    def _on_reset_press(self) -> None:
        """Handle RESET button press (mouse or touch).

        Guard prevents double-fire when both pressed and touch_pressed fire on
        a touchscreen (Pitfall 1 / T-26-06).
        """
        if self._reset_in_progress:
            return
        self._reset_in_progress = True
        self._reset_start = time.monotonic()
        self._reset_tick_timer.start(50)

    def _on_reset_release(self) -> None:
        """Handle RESET button release (mouse or touch).

        Always calls reset_auto_cutting(False) to clear bit 20.14 regardless
        of elapsed time (T-26-08: prevents stuck bit).
        """
        if not self._reset_in_progress:
            return
        self._reset_tick_timer.stop()
        elapsed = time.monotonic() - self._reset_start
        if elapsed < 1.5 and self.machine_control:
            self.machine_control.reset_auto_cutting(False)
        self._reset_in_progress = False
        self._reset_progress = 0.0
        self.btnReset.update()

    def _on_reset_tick(self) -> None:
        """Called every 50ms while RESET is held.

        Updates progress animation and triggers reset_auto_cutting(True) when
        hold duration reaches 1500ms.
        """
        elapsed = time.monotonic() - self._reset_start
        self._reset_progress = min(1.0, elapsed / 1.5)
        self.btnReset.update()
        if elapsed >= 1.5:
            self._reset_tick_timer.stop()
            if self.machine_control:
                self.machine_control.reset_auto_cutting(True)

    def _paint_reset_progress(self, event) -> None:
        """Paint RESET button with left-to-right progress overlay."""
        self._btnReset_original_paint(event)
        if self._reset_progress > 0:
            painter = QPainter(self.btnReset)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.btnReset.rect()
            fill_width = int(rect.width() * self._reset_progress)
            painter.setBrush(QColor(149, 9, 82, 120))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(0, 0, fill_width, rect.height(), 20, 20)
            painter.end()

    # -------------------------------------------------------------------------
    # D2056 Polling Timer (D-13, D-14, D-15, D-18)
    # -------------------------------------------------------------------------

    def _on_polling_timer(self) -> None:
        """Poll D2056 for cut count, update UI, detect new-cut for ML reset."""
        if not self.machine_control:
            return

        count = self.machine_control.read_kesilmis_adet()
        if count is None:
            return  # Connection issue, skip this cycle

        target = self._get_target()

        # D-18: ML state reset detection — count decreased means PLC reset
        # counter for a new cut cycle (Pitfall 4: skip on first poll when
        # _previous_count is None to avoid spurious reset / T-26-07)
        if self._previous_count is not None and count > 0 and count < self._previous_count:
            self._trigger_ml_state_reset()
        self._previous_count = count

        # D-13: Update counter label
        self.labelCounter.setText(f"{count} / {target}")

        # Update progress bar
        progress = min(1.0, count / target) if target > 0 else 0.0
        if hasattr(self, "progressWidget"):
            self.progressWidget._progress = progress
            self.progressWidget._complete = target > 0 and count >= target
            self.progressWidget.update()

        # D-15: Completion detection
        if target > 0 and count >= target:
            self._on_cutting_complete()
            return

        # D-14: Toggle param enabled/disabled based on cutting activity
        cutting_active = count > 0
        self._set_params_enabled(not cutting_active)

        # D-10: START button state
        if cutting_active:
            self.btnStart.setEnabled(False)
            self.btnStart.setText("DEVAM EDIYOR...")
        else:
            self.btnStart.setEnabled(True)
            self.btnStart.setText("START")

    def _on_cutting_complete(self) -> None:
        """Handle cutting completion: green counter, green progress, Tamamlandi label."""
        # Counter goes green
        self.labelCounter.setStyleSheet(
            "background: transparent;"
            " color: #22C55E;"
            " font: 80px 'Plus Jakarta Sans';"
            " font-weight: bold;"
        )

        # Show completion label
        if hasattr(self, "labelComplete"):
            self.labelComplete.setVisible(True)

        # Re-enable params
        self._set_params_enabled(True)
        self._cutting_active = False

        # Re-enable START
        self.btnStart.setEnabled(True)
        self.btnStart.setText("START")

        # Stop polling
        if self._polling_timer and self._polling_timer.isActive():
            self._polling_timer.stop()

        logger.info("Auto cutting completed - target reached")

    def _trigger_ml_state_reset(self) -> None:
        """Reset ML state when new cut cycle detected (D2056 count decreased)."""
        if self.control_manager and self.event_loop:
            asyncio.run_coroutine_threadsafe(
                self.control_manager.set_mode(ControlMode.ML),
                self.event_loop,
            )
            # Sync button states
            self.btnManual.setChecked(False)
            self.btnAI.setChecked(True)
            logger.info("ML state reset triggered - new cut cycle detected")

    # -------------------------------------------------------------------------
    # ML Mode Toggle (D-16, D-17)
    # -------------------------------------------------------------------------

    def _switch_to_mode(self, mode: ControlMode) -> None:
        """Switch control mode and schedule async set_mode call (D-17)."""
        self.btnManual.setChecked(mode == ControlMode.MANUAL)
        self.btnAI.setChecked(mode == ControlMode.ML)
        if self.control_manager and self.event_loop:
            asyncio.run_coroutine_threadsafe(
                self.control_manager.set_mode(mode),
                self.event_loop,
            )
        logger.info(f"ML mode switched to: {mode.value}")

    def _sync_ml_mode(self) -> None:
        """Sync ML button states from current control_manager mode on page open (D-17)."""
        if self.control_manager and hasattr(self.control_manager, "current_mode"):
            current = self.control_manager.current_mode
            self.btnManual.setChecked(current == ControlMode.MANUAL)
            self.btnAI.setChecked(current == ControlMode.ML)
        else:
            self.btnManual.setChecked(True)
            self.btnAI.setChecked(False)
