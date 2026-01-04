"""
Positioning page controller - Complete implementation matching old GUI design.

This is a production-ready, pixel-perfect recreation of the old positioning page
with all features, thread-safe data handling, and Qt Signals/Slots.

Page size: 1528x1080 (content area)
Framework: PySide6
"""

import logging
import os
import time
from typing import Optional, Dict, Callable

try:
    from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QLabel
    from PySide6.QtCore import Qt, QTimer, Slot, Signal
    from PySide6.QtGui import QFont, QPixmap, QIcon
except ImportError:
    logging.warning("PySide6 not installed")
    QWidget = object
    QFrame = object
    QPushButton = object
    QLabel = object
    Qt = object
    QTimer = object
    Slot = lambda *args, **kwargs: (lambda f: f)
    Signal = lambda *args: None
    QFont = object
    QPixmap = object
    QIcon = object

logger = logging.getLogger(__name__)


class PositioningController(QWidget):
    """
    Positioning page controller with complete old GUI implementation.

    Features:
    - Mengene Kontrolü (Vise Control) - Toggle buttons for rear/front vise open/close
    - Malzeme Konumlandırma (Material Positioning) - Hold-to-activate buttons
    - Testere Konumlandırma (Saw Positioning) - Hold-to-activate buttons
    - Thread-safe control via control_manager
    - Complete error handling and logging
    - PySide2 compatible
    """

    def __init__(
        self,
        control_manager=None,
        data_pipeline=None,
        parent=None
    ):
        """
        Initialize positioning controller.

        Args:
            control_manager: Control manager for machine control (thread-safe)
            data_pipeline: Data pipeline instance for data access
            parent: Parent widget
        """
        super().__init__(parent)

        # Dependencies
        self.control_manager = control_manager
        self.data_pipeline = data_pipeline

        # Legacy compatibility
        self.get_data_callback = data_pipeline

        # UI suppression flag for mengene close button
        self._suppress_close_autocheck_until: float = 0.0

        # Setup UI
        self._setup_ui()

        # Setup timers
        self._setup_timers()

        logger.info("PositioningController initialized")

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

        label_title_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 28px;
            }
        """

        # Button style for vise control (checkable toggle buttons)
        vise_button_style = """
            QPushButton {
                background-color: rgba(26, 31, 55, 200);
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                text-align: center;
                border-radius: 20px;
                border: 3px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 3px solid rgba(149, 9, 82, 180);
            }
            QPushButton:pressed {
                background-color: rgba(149, 9, 82, 220);
            }
            QPushButton:checked {
                background-color: #950952;
                border: 3px solid #F4F6FC;
            }
            QPushButton:disabled {
                background-color: rgba(26, 31, 55, 100);
                color: rgba(244, 246, 252, 100);
            }
        """

        # Button style for material/saw positioning (hold-to-activate)
        positioning_button_style = """
            QPushButton {
                background-color: rgba(26, 31, 55, 200);
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                text-align: center;
                border-radius: 25px;
                border: 3px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 3px solid rgba(149, 9, 82, 180);
            }
            QPushButton:pressed, QPushButton:checked {
                background-color: rgba(149, 9, 82, 220);
                border: 3px solid rgba(149, 9, 82, 255);
            }
            QPushButton:disabled {
                background-color: rgba(26, 31, 55, 100);
                color: rgba(244, 246, 252, 100);
            }
        """

        # === MENGENE KONTROLÜ FRAME (LEFT) ===
        # Position: (0, 0, 440, 700)
        self.mengeneKontroluFrame = QFrame(self)
        self.mengeneKontroluFrame.setGeometry(0, 0, 440, 700)
        self.mengeneKontroluFrame.setStyleSheet(frame_style)

        self.labelMengeneKontrolu = QLabel("Mengene Kontrolü", self.mengeneKontroluFrame)
        self.labelMengeneKontrolu.setGeometry(30, 30, 380, 40)
        self.labelMengeneKontrolu.setStyleSheet(label_title_style)

        # Arka Mengene Aç button (top)
        self.btnArkaMengeneAc = QPushButton(self.mengeneKontroluFrame)
        self.btnArkaMengeneAc.setGeometry(118, 100, 205, 205)
        self.btnArkaMengeneAc.setStyleSheet(vise_button_style)
        self.btnArkaMengeneAc.setCheckable(True)
        self.btnArkaMengeneAc.setIcon(self._load_icon("arka-mengene-ac.svg"))
        self.btnArkaMengeneAc.setIconSize(self.btnArkaMengeneAc.size())
        self.btnArkaMengeneAc.clicked.connect(
            lambda checked: self._on_toggle_button(
                self.btnArkaMengeneAc, "arka_mengene_ac", checked
            )
        )

        # Mengene Kapat/Sıkıştır button (center)
        self.btnMengeneKapat = QPushButton(self.mengeneKontroluFrame)
        self.btnMengeneKapat.setGeometry(118, 325, 205, 205)
        self.btnMengeneKapat.setStyleSheet(vise_button_style)
        self.btnMengeneKapat.setCheckable(True)
        self.btnMengeneKapat.setIcon(self._load_icon("mengene-sikistir.svg"))
        self.btnMengeneKapat.setIconSize(self.btnMengeneKapat.size())
        self.btnMengeneKapat.clicked.connect(
            lambda checked: self._on_toggle_button(
                self.btnMengeneKapat, "mengene_kapat", checked
            )
        )

        # Ön Mengene Aç button (bottom)
        self.btnOnMengeneAc = QPushButton(self.mengeneKontroluFrame)
        self.btnOnMengeneAc.setGeometry(118, 550, 205, 205)
        self.btnOnMengeneAc.setStyleSheet(vise_button_style)
        self.btnOnMengeneAc.setCheckable(True)
        self.btnOnMengeneAc.setIcon(self._load_icon("on-mengene-ac.svg"))
        self.btnOnMengeneAc.setIconSize(self.btnOnMengeneAc.size())
        self.btnOnMengeneAc.clicked.connect(
            lambda checked: self._on_toggle_button(
                self.btnOnMengeneAc, "on_mengene_ac", checked
            )
        )

        # === MALZEME KONUMLANDIRMA FRAME (CENTER) ===
        # Position: (460, 0, 520, 700)
        self.malzemeKonumlandirmaFrame = QFrame(self)
        self.malzemeKonumlandirmaFrame.setGeometry(460, 0, 520, 700)
        self.malzemeKonumlandirmaFrame.setStyleSheet(frame_style)

        self.labelMalzemeKonumlandirma = QLabel(
            "Malzeme Konumlandırma",
            self.malzemeKonumlandirmaFrame
        )
        self.labelMalzemeKonumlandirma.setGeometry(30, 30, 460, 40)
        self.labelMalzemeKonumlandirma.setStyleSheet(label_title_style)

        # Malzeme Geri button (top)
        self.btnMalzemeGeri = QPushButton(self.malzemeKonumlandirmaFrame)
        self.btnMalzemeGeri.setGeometry(128, 100, 265, 265)
        self.btnMalzemeGeri.setStyleSheet(positioning_button_style)
        self.btnMalzemeGeri.setCheckable(True)
        self.btnMalzemeGeri.setIcon(self._load_icon("malzeme-geri-icon.png"))
        self.btnMalzemeGeri.setIconSize(self.btnMalzemeGeri.size())
        self.btnMalzemeGeri.pressed.connect(
            lambda: self._on_hold_button(self.btnMalzemeGeri, "malzeme_geri", True)
        )
        self.btnMalzemeGeri.released.connect(
            lambda: self._on_hold_button(self.btnMalzemeGeri, "malzeme_geri", False)
        )

        # Malzeme İleri button (bottom)
        self.btnMalzemeIleri = QPushButton(self.malzemeKonumlandirmaFrame)
        self.btnMalzemeIleri.setGeometry(128, 390, 265, 265)
        self.btnMalzemeIleri.setStyleSheet(positioning_button_style)
        self.btnMalzemeIleri.setCheckable(True)
        self.btnMalzemeIleri.setIcon(self._load_icon("malzeme-ileri-icon.png"))
        self.btnMalzemeIleri.setIconSize(self.btnMalzemeIleri.size())
        self.btnMalzemeIleri.pressed.connect(
            lambda: self._on_hold_button(self.btnMalzemeIleri, "malzeme_ileri", True)
        )
        self.btnMalzemeIleri.released.connect(
            lambda: self._on_hold_button(self.btnMalzemeIleri, "malzeme_ileri", False)
        )

        # === TESTERE KONUMLANDIRMA FRAME (RIGHT) ===
        # Position: (1000, 0, 528, 700)
        self.testereKonumlandirmaFrame = QFrame(self)
        self.testereKonumlandirmaFrame.setGeometry(1000, 0, 528, 700)
        self.testereKonumlandirmaFrame.setStyleSheet(frame_style)

        self.labelTestereKonumlandirma = QLabel(
            "Testere Konumlandırma",
            self.testereKonumlandirmaFrame
        )
        self.labelTestereKonumlandirma.setGeometry(30, 30, 468, 40)
        self.labelTestereKonumlandirma.setStyleSheet(label_title_style)

        # Testere Yukarı button (top)
        self.btnTestereYukari = QPushButton(self.testereKonumlandirmaFrame)
        self.btnTestereYukari.setGeometry(132, 100, 265, 265)
        self.btnTestereYukari.setStyleSheet(positioning_button_style)
        self.btnTestereYukari.setCheckable(True)
        self.btnTestereYukari.setIcon(self._load_icon("saw-up-icon.png"))
        self.btnTestereYukari.setIconSize(self.btnTestereYukari.size())
        self.btnTestereYukari.pressed.connect(
            lambda: self._on_hold_button(self.btnTestereYukari, "testere_yukari", True)
        )
        self.btnTestereYukari.released.connect(
            lambda: self._on_hold_button(self.btnTestereYukari, "testere_yukari", False)
        )

        # Testere Aşağı button (bottom)
        self.btnTestereAsagi = QPushButton(self.testereKonumlandirmaFrame)
        self.btnTestereAsagi.setGeometry(132, 390, 265, 265)
        self.btnTestereAsagi.setStyleSheet(positioning_button_style)
        self.btnTestereAsagi.setCheckable(True)
        self.btnTestereAsagi.setIcon(self._load_icon("saw-down-icon.png"))
        self.btnTestereAsagi.setIconSize(self.btnTestereAsagi.size())
        self.btnTestereAsagi.pressed.connect(
            lambda: self._on_hold_button(self.btnTestereAsagi, "testere_asagi", True)
        )
        self.btnTestereAsagi.released.connect(
            lambda: self._on_hold_button(self.btnTestereAsagi, "testere_asagi", False)
        )

    def _setup_timers(self):
        """Setup all Qt timers for periodic updates."""
        # Data update timer (if callback provided)
        if self.get_data_callback:
            self._data_timer = QTimer(self)
            self._data_timer.timeout.connect(self._on_data_tick)
            self._data_timer.start(200)  # 200ms

        # Button state sync timer
        self._button_state_timer = QTimer(self)
        self._button_state_timer.timeout.connect(self._update_button_states)
        self._button_state_timer.start(300)  # 300ms

    # ========================================================================
    # Button Event Handlers
    # ========================================================================

    def _on_toggle_button(self, button, command: str, checked: bool) -> None:
        """
        Handle toggle-type buttons (mengene controls).

        Args:
            button: Button widget that was clicked
            command: Command identifier
            checked: New checked state
        """
        try:
            # Check if control manager is available
            if self.control_manager is None:
                logger.warning(f"Control manager not available for {command}")
                # Revert button state
                button.blockSignals(True)
                button.setChecked(not checked)
                button.blockSignals(False)
                return

            state_text = "AKTIF" if checked else "PASIF"
            logger.info(f"{command} => {state_text}")

            # Handle vise controls
            if command == "arka_mengene_ac":
                if checked:
                    # Suppress close button auto-activation
                    self._suppress_close_autocheck_until = time.monotonic() + 0.6

                    # Open rear vise exclusively
                    success = self._execute_control_command(
                        "open_rear_vise_exclusive"
                    )

                    if success:
                        # Update UI immediately
                        button.blockSignals(True)
                        button.setChecked(True)
                        button.blockSignals(False)

                        # Close front vise if open (mutual exclusivity)
                        if hasattr(self, 'btnOnMengeneAc') and \
                           self.btnOnMengeneAc.isChecked():
                            self.btnOnMengeneAc.blockSignals(True)
                            self.btnOnMengeneAc.setChecked(False)
                            self.btnOnMengeneAc.blockSignals(False)

                        # Deactivate close button
                        if hasattr(self, 'btnMengeneKapat'):
                            self.btnMengeneKapat.blockSignals(True)
                            self.btnMengeneKapat.setChecked(False)
                            self.btnMengeneKapat.blockSignals(False)
                    else:
                        # Revert on failure
                        button.blockSignals(True)
                        button.setChecked(False)
                        button.blockSignals(False)
                else:
                    # Close rear vise
                    success = self._execute_control_command("close_rear_vise")
                    button.blockSignals(True)
                    button.setChecked(False if success else True)
                    button.blockSignals(False)

            elif command == "on_mengene_ac":
                if checked:
                    # Suppress close button auto-activation
                    self._suppress_close_autocheck_until = time.monotonic() + 0.6

                    # Open front vise exclusively
                    success = self._execute_control_command(
                        "open_front_vise_exclusive"
                    )

                    if success:
                        # Update UI immediately
                        button.blockSignals(True)
                        button.setChecked(True)
                        button.blockSignals(False)

                        # Close rear vise if open (mutual exclusivity)
                        if hasattr(self, 'btnArkaMengeneAc') and \
                           self.btnArkaMengeneAc.isChecked():
                            self.btnArkaMengeneAc.blockSignals(True)
                            self.btnArkaMengeneAc.setChecked(False)
                            self.btnArkaMengeneAc.blockSignals(False)

                        # Deactivate close button
                        if hasattr(self, 'btnMengeneKapat'):
                            self.btnMengeneKapat.blockSignals(True)
                            self.btnMengeneKapat.setChecked(False)
                            self.btnMengeneKapat.blockSignals(False)
                    else:
                        # Revert on failure
                        button.blockSignals(True)
                        button.setChecked(False)
                        button.blockSignals(False)
                else:
                    # Close front vise
                    success = self._execute_control_command("close_front_vise")
                    button.blockSignals(True)
                    button.setChecked(False if success else True)
                    button.blockSignals(False)

            elif command == "mengene_kapat":
                if checked:
                    # Close both vises
                    success = self._execute_control_command("close_both_vises")

                    if success:
                        # Update all mengene buttons
                        if hasattr(self, 'btnArkaMengeneAc'):
                            self.btnArkaMengeneAc.blockSignals(True)
                            self.btnArkaMengeneAc.setChecked(False)
                            self.btnArkaMengeneAc.blockSignals(False)

                        if hasattr(self, 'btnOnMengeneAc'):
                            self.btnOnMengeneAc.blockSignals(True)
                            self.btnOnMengeneAc.setChecked(False)
                            self.btnOnMengeneAc.blockSignals(False)

                        # Keep close button active
                        button.blockSignals(True)
                        button.setChecked(True)
                        button.blockSignals(False)
                    else:
                        # Revert on failure
                        button.blockSignals(True)
                        button.setChecked(False)
                        button.blockSignals(False)
                else:
                    # Deactivate close button
                    button.blockSignals(True)
                    button.setChecked(False)
                    button.blockSignals(False)

        except Exception as e:
            logger.error(f"Toggle button error ({command}): {e}")
            # Revert button state on error
            button.blockSignals(True)
            button.setChecked(not checked)
            button.blockSignals(False)

    def _on_hold_button(self, button, command: str, is_pressed: bool) -> None:
        """
        Handle hold-to-activate buttons (material/saw positioning).

        Args:
            button: Button widget
            command: Command identifier
            is_pressed: True if pressed, False if released
        """
        try:
            # Check if control manager is available
            if self.control_manager is None:
                logger.warning(f"Control manager not available for {command}")
                return

            # Update visual state
            button.setChecked(is_pressed)

            state_text = "BASILI" if is_pressed else "BOSALDI"
            logger.info(f"{command} => {state_text}")

            # Handle material positioning
            if command == "malzeme_geri":
                if is_pressed:
                    self._execute_control_command("move_material_backward")
                else:
                    self._execute_control_command("stop_material_backward")

            elif command == "malzeme_ileri":
                if is_pressed:
                    self._execute_control_command("move_material_forward")
                else:
                    self._execute_control_command("stop_material_forward")

            # Handle saw positioning
            elif command == "testere_yukari":
                if is_pressed:
                    self._execute_control_command("move_saw_up")
                else:
                    self._execute_control_command("stop_saw_up")

            elif command == "testere_asagi":
                if is_pressed:
                    self._execute_control_command("move_saw_down")
                else:
                    self._execute_control_command("stop_saw_down")

        except Exception as e:
            logger.error(f"Hold button error ({command}): {e}")
            # Reset button visual state
            button.setChecked(False)

    def _execute_control_command(self, command: str) -> bool:
        """
        Execute control command via control manager (thread-safe).

        Args:
            command: Command method name

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.control_manager is None:
                logger.error(f"Control manager not available for command: {command}")
                return False

            # Get command method
            if not hasattr(self.control_manager, command):
                logger.error(f"Control manager does not support command: {command}")
                return False

            command_method = getattr(self.control_manager, command)

            # Execute command
            result = command_method()

            # Check result (some methods may return None for success)
            if result is None:
                return True
            elif isinstance(result, bool):
                return result
            else:
                return True

        except Exception as e:
            logger.error(f"Control command execution error ({command}): {e}")
            return False

    # ========================================================================
    # Data Update Methods
    # ========================================================================

    def _on_data_tick(self):
        """Called by data timer to fetch and update data."""
        try:
            if self.get_data_callback:
                # get_data_callback is data_pipeline object, not a function
                # Get stats if available
                if hasattr(self.get_data_callback, 'get_stats'):
                    data = self.get_data_callback.get_stats()
                    if data:
                        self.update_data(data)
        except Exception as e:
            logger.error(f"Data tick error: {e}")

    def update_data(self, data: Dict):
        """
        Update display with latest data.

        Args:
            data: Dictionary containing sensor and machine data
        """
        try:
            # Currently no data displays on positioning page
            # Could add status indicators in the future
            pass
        except Exception as e:
            logger.error(f"Data update error: {e}")

    def _update_button_states(self):
        """Update button states from machine feedback."""
        try:
            # Skip if no control manager
            if self.control_manager is None:
                return

            # Check if control manager has status query methods
            # Mengene status
            if hasattr(self.control_manager, 'is_rear_vise_open'):
                rear_vise_status = self.control_manager.is_rear_vise_open()
                if rear_vise_status is not None and hasattr(self, 'btnArkaMengeneAc'):
                    self.btnArkaMengeneAc.blockSignals(True)
                    self.btnArkaMengeneAc.setChecked(rear_vise_status)
                    self.btnArkaMengeneAc.blockSignals(False)

            if hasattr(self.control_manager, 'is_front_vise_open'):
                front_vise_status = self.control_manager.is_front_vise_open()
                if front_vise_status is not None and hasattr(self, 'btnOnMengeneAc'):
                    self.btnOnMengeneAc.blockSignals(True)
                    self.btnOnMengeneAc.setChecked(front_vise_status)
                    self.btnOnMengeneAc.blockSignals(False)
            else:
                front_vise_status = None
                rear_vise_status = None

            # Mengene close button sync
            if hasattr(self, 'btnMengeneKapat') and \
               rear_vise_status is not None and front_vise_status is not None:
                # Close button active only when both vises are closed
                should_close_active = (rear_vise_status is False) and \
                                      (front_vise_status is False)

                # Check suppression window
                if time.monotonic() >= self._suppress_close_autocheck_until:
                    self.btnMengeneKapat.blockSignals(True)
                    self.btnMengeneKapat.setChecked(should_close_active)
                    self.btnMengeneKapat.blockSignals(False)

            # Material movement status
            if hasattr(self.control_manager, 'is_material_moving_backward'):
                material_backward_status = \
                    self.control_manager.is_material_moving_backward()
                if material_backward_status is not None and \
                   hasattr(self, 'btnMalzemeGeri'):
                    self.btnMalzemeGeri.blockSignals(True)
                    self.btnMalzemeGeri.setChecked(material_backward_status)
                    self.btnMalzemeGeri.blockSignals(False)

            if hasattr(self.control_manager, 'is_material_moving_forward'):
                material_forward_status = \
                    self.control_manager.is_material_moving_forward()
                if material_forward_status is not None and \
                   hasattr(self, 'btnMalzemeIleri'):
                    self.btnMalzemeIleri.blockSignals(True)
                    self.btnMalzemeIleri.setChecked(material_forward_status)
                    self.btnMalzemeIleri.blockSignals(False)

            # Saw movement status
            if hasattr(self.control_manager, 'is_saw_moving_up'):
                saw_up_status = self.control_manager.is_saw_moving_up()
                if saw_up_status is not None and hasattr(self, 'btnTestereYukari'):
                    self.btnTestereYukari.blockSignals(True)
                    self.btnTestereYukari.setChecked(saw_up_status)
                    self.btnTestereYukari.blockSignals(False)

            if hasattr(self.control_manager, 'is_saw_moving_down'):
                saw_down_status = self.control_manager.is_saw_moving_down()
                if saw_down_status is not None and hasattr(self, 'btnTestereAsagi'):
                    self.btnTestereAsagi.blockSignals(True)
                    self.btnTestereAsagi.setChecked(saw_down_status)
                    self.btnTestereAsagi.blockSignals(False)

        except Exception as e:
            logger.debug(f"Button state update error: {e}")

    # ========================================================================
    # Utility Methods
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

    # No cleanup() method needed - PySide6 handles timer cleanup automatically
    # when widget is destroyed via parent-child relationships
