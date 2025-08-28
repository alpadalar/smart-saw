from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from .qt_monitoring_interface import Ui_MainWindow
from typing import Dict, Callable
from datetime import datetime

class MonitoringWindow(QMainWindow):
    def __init__(self, parent=None, get_data_callback: Callable[[], Dict] = None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.parent = parent
        # Kontrol Paneli butonuna tıklanınca kontrol paneline geç
        self.ui.btnControlPanel.clicked.connect(self.open_control_panel)
        # Kamera butonuna tıklanınca kamera penceresine geç
        self.ui.btnCamera.clicked.connect(self.open_camera_window)
        # Sensör butonuna tıklanınca sensör penceresine geç
        self.ui.btnSensor.clicked.connect(self.open_sensor_window)
        # İzleme butonuna tıklanınca izleme penceresine geç (zaten açık)
        self.ui.btnTracking.clicked.connect(self.open_monitoring_window)
        self.get_data_callback = get_data_callback
        self.camera_window = None
        self.sensor_window = None

        # Timer başlat
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.periodic_update)
        self.timer.start(500)  # Her saniye güncelle
        self.periodic_update()  # İlk açılışta hemen güncelle

        self.set_active_nav("btnTracking")

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

    def set_active_nav(self, active_btn_name):
        btns = [
            (self.ui.btnControlPanel, QIcon("src/gui/images/control-panel-icon2.svg"), QIcon("src/gui/images/control-panel-icon2-active.svg")),
            (self.ui.btnPositioning, QIcon("src/gui/images/positioning-icon2.svg"), QIcon("src/gui/images/positioning-icon2-active.svg")),
            (self.ui.btnCamera, QIcon("src/gui/images/camera-icon2.svg"), QIcon("src/gui/images/camera-icon-active.svg")),
            (self.ui.btnSensor, QIcon("src/gui/images/sensor-icon2.svg"), QIcon("src/gui/images/sensor-icon2-active.svg")),
            (self.ui.btnTracking, QIcon("src/gui/images/tracking-icon2.svg"), QIcon("src/gui/images/tracking-icon2-active.svg")),
        ]
        for btn, icon_passive, icon_active in btns:
            if btn.objectName() == active_btn_name:
                btn.setIcon(icon_active)
            else:
                btn.setIcon(icon_passive)

    def open_control_panel(self):
        if self.parent:
            self.hide()
            self.parent.set_active_nav("btnControlPanel")
            self.parent.showFullScreen()

    def open_camera_window(self):
        # CameraWindow singleton örneğini parent üzerinden paylaş
        if hasattr(self.parent, 'camera_window') and self.parent.camera_window is not None:
            cam_win = self.parent.camera_window
        else:
            from .camera_controller import CameraWindow
            cam_win = CameraWindow(parent=self.parent, get_data_callback=self.get_data_callback)
            if hasattr(self.parent, 'camera_window'):
                self.parent.camera_window = cam_win
        self.hide()
        cam_win.set_active_nav("btnCamera")
        cam_win.showFullScreen()

    def open_sensor_window(self):
        if self.sensor_window is None or not self.sensor_window.isVisible():
            from .sensor_controller import SensorWindow
            self.sensor_window = SensorWindow(parent=self.parent, get_data_callback=self.get_data_callback)
        self.hide()
        self.sensor_window.set_active_nav("btnSensor")
        self.sensor_window.showFullScreen()

    def open_monitoring_window(self):
        self.set_active_nav("btnTracking")
        pass

    def _update_values(self, processed_data: Dict):
        try:
            label_map = {
                'labelMakineIDValue': 'makine_id',
                'labelSeritIDValue': 'serit_id',
                'labelSeritDisOlcusuValue': 'serit_dis_mm',
                'labelSeritTipiValue': 'serit_tip',
                'labelSeritMarkasiValue': 'serit_marka',
                'labelBandSeritMalzemesiValue': 'serit_malz',
                'labelMalzemeCinsiValue': 'malzeme_cinsi',
                'labelMalzemeSertligiValue': 'malzeme_sertlik',
                'labelKesitYapisiValue': 'kesit_yapisi',
                'labelAValue': 'a_mm',
                'labelBValue': 'b_mm',
                'labelCValue': 'c_mm',
                'labelDValue': 'd_mm',
                'labelSeritSapmasiValue': 'serit_sapmasi',
                'labelSeritGerginligiValue': 'serit_gerginligi_bar',
                'labelKafaYuksekligiValue': 'kafa_yuksekligi_mm',
                'labelTitresimXValue': 'ivme_olcer_x',
                'labelTitresimYValue': 'ivme_olcer_y',
                'labelTitresimZValue': 'ivme_olcer_z',
                'labelMengeneBasincValue': 'mengene_basinc_bar',
                'labelOrtamSicakligiValue': 'ortam_sicakligi_c',
                'labelOrtamNemValue': 'ortam_nem_percentage',
                'labelKesilenParcaAdetiValue': 'kesilen_parca_adeti',
                'labelTestereDurumValue': 'testere_durumu',
                'labelAlarmValue': 'alarm_status',
                'labelSeritMotorHizValue': 'serit_kesme_hizi',
                'labelInmeMotorHizValue': 'serit_inme_hizi',
                'labelSeritMotorAkimValue': 'serit_motor_akim_a',
                'labelInmeMotorAkimValue': 'inme_motor_akim_a',
                'labelSeritMotorTorkValue': 'serit_motor_tork_percentage',
                'labelInmeMotorTorkValue': 'inme_motor_tork_percentage',
                'labelMaxBandDeviationValue': 'serit_sapmasi',
            }
            for label_name, data_key in label_map.items():
                value = processed_data.get(data_key, '-')
                label_widget = getattr(self.ui, label_name, None)
                if label_widget:
                    label_widget.setText(str(value))
        except Exception as e:
            print(f"Monitoring _update_values hata: {e}")

    def update_ui(self, processed_data: Dict):
        self._update_values(processed_data) 