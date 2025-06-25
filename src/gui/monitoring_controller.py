from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer
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
        self.get_data_callback = get_data_callback
        self.camera_window = None

        # Timer başlat
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.periodic_update)
        self.timer.start(500)  # Her saniye güncelle
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
        if self.parent:
            self.parent.show()
        self.hide()

    def open_camera_window(self):
        # Lazy import to avoid circular dependency
        if self.camera_window is None:
            from .camera_controller import CameraWindow
            self.camera_window = CameraWindow(parent=self, get_data_callback=self.get_data_callback)
        self.camera_window.show()
        self.hide()

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