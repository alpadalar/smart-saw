from PyQt5.QtWidgets import QMainWindow
from .qt_monitoring_interface import Ui_MainWindow

class MonitoringWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Kontrol Paneli butonuna tıklanınca kontrol paneline geç
        self.ui.btnControlPanel.clicked.connect(self.open_control_panel)

    def open_control_panel(self):
        from .qt_controller import SimpleGUI
        self.control_panel = SimpleGUI()
        self.control_panel.show()
        self.close() 