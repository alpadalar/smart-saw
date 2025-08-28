import sys
import threading
from typing import Dict, Optional

from PySide6.QtWidgets import QApplication

# New controllers live under project-root/controllers
from gui.controllers.pyside_control_panel import ControlPanelWindow


class SimpleGUI:
    """Adapter to integrate the new PySide6 UI with the existing SmartSaw lifecycle.
    Exposes .start(), .update_data(), .gui_ready and .threads_ready similar to the old API.
    """

    def __init__(self, controller_factory=None):
        self.controller_factory = controller_factory

        # Events used by SmartSaw.start()
        self.gui_ready = threading.Event()
        self.threads_ready = threading.Event()

        # Store latest processed data for pages to pull via callback
        self._latest_data: Optional[Dict] = None
        self._data_lock = threading.Lock()

        # Ensure single QApplication
        self._app = QApplication.instance() or QApplication(sys.argv)

        # Build main window; pass a callback so pages can read data on their timers
        self._window = ControlPanelWindow(
            controller_factory=self.controller_factory,
            get_data_callback=self._get_latest_data,
        )

    def _get_latest_data(self) -> Optional[Dict]:
        with self._data_lock:
            return self._latest_data

    def start(self) -> None:
        """Show window; the event loop must be started on the main thread via exec()."""
        self._window.showFullScreen()
        self.gui_ready.set()

    def exec(self) -> int:
        """Run Qt event loop on the main thread."""
        return self._app.exec()

    # SmartSaw will call this from its data loop
    def update_data(self, processed_data: Dict) -> None:
        with self._data_lock:
            self._latest_data = processed_data 