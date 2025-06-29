from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer
from .qt_camera_interface import Ui_MainWindow
from typing import Dict, Callable
from datetime import datetime

class CameraWindow(QMainWindow):
    def __init__(self, parent=None, get_data_callback: Callable[[], Dict] = None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.parent = parent
        # Kontrol Paneli butonuna tıklanınca kontrol paneline geç
        self.ui.btnControlPanel.clicked.connect(self.open_control_panel)
        # İzleme butonuna tıklanınca monitoring penceresine geç
        self.ui.btnTracking.clicked.connect(self.open_monitoring_window)
        # Sensör butonuna tıklanınca sensör penceresine geç
        self.ui.btnSensor.clicked.connect(self.open_sensor_window)
        # Kamera butonuna tıklanınca kamera penceresine geç (zaten açık)
        self.ui.btnCamera.clicked.connect(self.open_camera_window)
        self.get_data_callback = get_data_callback
        self.monitoring_window = None
        self.sensor_window = None

        # Timer başlat
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.periodic_update)
        self.timer.start(1000)  # Her saniye güncelle
        self.periodic_update()  # İlk açılışta hemen güncelle

    def periodic_update(self):
        # Saat ve tarihi güncelle
        now = datetime.now()
        self.ui.labelDate.setText(now.strftime('%d.%m.%Y %A'))
        self.ui.labelTime.setText(now.strftime('%H:%M'))
        # Verileri güncelle
        if self.get_data_callback:
            data = self.get_data_callback()
            if data:
                self.update_ui(data)

    def open_control_panel(self):
        # Monitoring veya başka bir pencereyi gizle, ana pencereyi göster
        if self.parent:
            self.hide()
            self.parent.show()

    def open_monitoring_window(self):
        # MonitoringWindow instance'ı yoksa oluştur, varsa tekrar kullan
        if self.monitoring_window is None or not self.monitoring_window.isVisible():
            from .monitoring_controller import MonitoringWindow
            self.monitoring_window = MonitoringWindow(parent=self.parent, get_data_callback=self.get_data_callback)
        self.hide()
        self.monitoring_window.show()

    def open_sensor_window(self):
        # SensorWindow instance'ı yoksa oluştur, varsa tekrar kullan
        if self.sensor_window is None or not self.sensor_window.isVisible():
            from .sensor_controller import SensorWindow
            self.sensor_window = SensorWindow(parent=self.parent, get_data_callback=self.get_data_callback)
        self.hide()
        self.sensor_window.show()

    def open_camera_window(self):
        # Kamera penceresine zaten açık olduğundan göster
        pass

    def _update_values(self, processed_data: Dict):
        try:
            # Kamera penceresinde gösterilecek değerleri güncelle
            # Bu değerler kamera ile ilgili olabilir veya genel sistem durumu
            label_map = {
                'labelTestereSagligiValue': 'testere_sagligi',  # Eğer varsa
                'labelAsinmaYuzdesiValue': 'asinma_yuzdesi',    # Eğer varsa
                'labelTestereDurumuValue': 'testere_durumu',
                'labelTespitEdilenKirikValue': 'tespit_edilen_kirik',  # Eğer varsa
                'labelTespitEdilenDisValue': 'tespit_edilen_dis',      # Eğer varsa
            }
            
            for label_name, data_key in label_map.items():
                value = processed_data.get(data_key, '-')
                label_widget = getattr(self.ui, label_name, None)
                if label_widget:
                    label_widget.setText(str(value))
                    
        except Exception as e:
            print(f"Camera _update_values hata: {e}")

    def update_ui(self, processed_data: Dict):
        self._update_values(processed_data) 