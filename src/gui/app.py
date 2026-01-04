"""
PySide6 GUI application wrapper - Clean implementation with proper Qt lifecycle.
"""

import logging
import sys
import threading
from typing import Optional

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
except ImportError:
    logging.warning("PySide6 not installed - GUI functionality disabled")
    QApplication = None

from .controllers.main_controller import MainController

logger = logging.getLogger(__name__)


class GUIApplication:
    """
    PySide6 application wrapper.

    Runs Qt event loop in separate thread to avoid blocking asyncio loop.
    Clean implementation with proper Qt object lifecycle.
    """

    def __init__(self, control_manager, data_pipeline):
        """
        Initialize GUI application.

        Args:
            control_manager: ControlManager instance
            data_pipeline: DataProcessingPipeline instance
        """
        if QApplication is None:
            raise RuntimeError("PySide6 not installed - cannot use GUI")

        self.control_manager = control_manager
        self.data_pipeline = data_pipeline

        # Qt application (created in GUI thread)
        self._app: Optional[QApplication] = None
        self._main_window: Optional[MainController] = None

        # Thread control
        self._gui_thread: Optional[threading.Thread] = None
        self._running = False

        logger.info("GUIApplication initialized")

    def run(self):
        """
        Direct run method (called from lifecycle in separate thread).
        """
        self._run_gui()

    def start(self):
        """
        Start GUI in separate thread.
        """
        if self._running:
            logger.warning("GUI already running")
            return

        self._running = True

        # Start GUI thread
        self._gui_thread = threading.Thread(
            target=self._run_gui,
            name="GUIThread",
            daemon=False  # Non-daemon to keep app alive
        )
        self._gui_thread.start()

        logger.info("GUI started in separate thread")

    def stop(self, timeout: float = 5.0):
        """
        Stop GUI gracefully.

        Args:
            timeout: Maximum time to wait for GUI thread
        """
        if not self._running:
            return

        self._running = False

        # Qt will handle cleanup automatically with PySide6
        if self._app:
            self._app.quit()

        # Wait for thread
        if self._gui_thread and self._gui_thread.is_alive():
            self._gui_thread.join(timeout=timeout)

        logger.info("GUI stopped")

    def _run_gui(self):
        """
        GUI thread entry point.

        PySide6 properly handles Qt object lifecycle and timer cleanup.
        """
        try:
            # Create Qt application
            self._app = QApplication(sys.argv)
            self._app.setApplicationName("Smart Band Saw Control")
            self._app.setOrganizationName("Smart Saw Inc")

            # Create main window
            self._main_window = MainController(
                self.control_manager,
                self.data_pipeline
            )
            self._main_window.showFullScreen()

            logger.info("Main window created and shown in fullscreen")

            # Run Qt event loop (PySide6 uses exec() not exec_())
            exit_code = self._app.exec()

            logger.info(f"GUI event loop ended: exit_code={exit_code}")

            # Explicitly clean up to ensure everything happens in GUI thread
            if self._main_window:
                self._main_window.close()
                self._main_window.deleteLater()
                self._main_window = None

            # Process remaining events to ensure cleanup
            if self._app:
                self._app.processEvents()

            logger.info("GUI cleanup completed in GUI thread")

        except Exception as e:
            logger.error(f"Error in GUI thread: {e}", exc_info=True)
