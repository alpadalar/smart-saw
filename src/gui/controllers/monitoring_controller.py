"""
Monitoring page controller - Complete implementation for data tracking and monitoring.

This is a production-ready monitoring page displaying all sensor data in an organized layout.
All data fields are displayed with proper labels, values updated thread-safely.

Page size: 1528x1080 (content area)
Framework: PySide6
"""

import logging
import threading
from typing import Optional, Dict, Callable

try:
    from PySide6.QtWidgets import QWidget, QFrame, QLabel
    from PySide6.QtCore import Qt, QTimer, Slot, Signal
    from PySide6.QtGui import QFont
except ImportError:
    logging.warning("PySide6 not installed")
    QWidget = object
    QFrame = object
    QLabel = object
    Qt = object
    QTimer = object
    Slot = lambda *args, **kwargs: (lambda f: f)
    Signal = lambda *args: None
    QFont = object

logger = logging.getLogger(__name__)


class MonitoringController(QWidget):
    """
    Monitoring page controller showing all sensor data and machine parameters.

    Features:
    - Machine and band information display
    - Material and cutting parameters
    - Real-time sensor data (deviation, tension, height, etc.)
    - Vibration sensors (X, Y, Z axes)
    - Motor currents and torques
    - Environmental sensors (temperature, humidity)
    - System status indicators
    - Thread-safe data updates
    - Organized multi-frame layout
    """

    def __init__(
        self,
        control_manager=None,
        data_pipeline=None,
        parent=None
    ):
        """
        Initialize monitoring controller.

        Args:
            control_manager: Control manager for machine control (optional)
            data_pipeline: Data pipeline instance for data access
            parent: Parent widget
        """
        super().__init__(parent)

        # Dependencies
        self.control_manager = control_manager
        self.data_pipeline = data_pipeline

        # Legacy compatibility
        self.get_data_callback = data_pipeline

        # Data management
        self.current_values = {}
        self._values_lock = threading.Lock()

        # Initialize default values
        self._initialize_current_values()

        # Setup UI
        self._setup_ui()

        # Setup timers
        self._setup_timers()

        logger.info("MonitoringController initialized")

    def _initialize_current_values(self):
        """Initialize default values for all data fields."""
        self.current_values = {
            'makine_id': '—',
            'serit_id': '—',
            'serit_dis_mm': '—',
            'serit_tip': '—',
            'serit_marka': '—',
            'serit_malz': '—',
            'malzeme_cinsi': '—',
            'malzeme_sertlik': '—',
            'kesit_yapisi': '—',
            'a_mm': '—',
            'b_mm': '—',
            'c_mm': '—',
            'd_mm': '—',
            'serit_sapmasi': '—',
            'serit_gerginligi_bar': '—',
            'kafa_yuksekligi_mm': '—',
            'ivme_olcer_x': '—',
            'ivme_olcer_y': '—',
            'ivme_olcer_z': '—',
            'mengene_basinc_bar': '—',
            'ortam_sicakligi_c': '—',
            'ortam_nem_percentage': '—',
            'kesilen_parca_adeti': '—',
            'testere_durumu': '—',
            'alarm_status': '—',
            'serit_kesme_hizi': '—',
            'serit_inme_hizi': '—',
            'serit_motor_akim_a': '—',
            'inme_motor_akim_a': '—',
            'serit_motor_tork_percentage': '—',
            'inme_motor_tork_percentage': '—'
        }

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
                font-size: 24px;
            }
        """

        label_field_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: medium;
                font-size: 20px;
            }
        """

        label_value_style = """
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 22px;
            }
        """

        # === MACHINE & BAND INFO FRAME (TOP LEFT) ===
        # Position: (0, 0, 500, 520)
        self.machineInfoFrame = QFrame(self)
        self.machineInfoFrame.setGeometry(0, 0, 500, 520)
        self.machineInfoFrame.setStyleSheet(frame_style)

        self.labelMachineInfoTitle = QLabel("Makine ve Şerit Bilgileri", self.machineInfoFrame)
        self.labelMachineInfoTitle.setGeometry(25, 20, 450, 35)
        self.labelMachineInfoTitle.setStyleSheet(label_title_style)

        # Machine ID
        self.labelMakineID = QLabel("Makine ID:", self.machineInfoFrame)
        self.labelMakineID.setGeometry(30, 70, 200, 30)
        self.labelMakineID.setStyleSheet(label_field_style)
        self.labelMakineIDValue = QLabel("—", self.machineInfoFrame)
        self.labelMakineIDValue.setGeometry(250, 70, 220, 30)
        self.labelMakineIDValue.setStyleSheet(label_value_style)
        self.labelMakineIDValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit ID
        self.labelSeritID = QLabel("Şerit ID:", self.machineInfoFrame)
        self.labelSeritID.setGeometry(30, 110, 200, 30)
        self.labelSeritID.setStyleSheet(label_field_style)
        self.labelSeritIDValue = QLabel("—", self.machineInfoFrame)
        self.labelSeritIDValue.setGeometry(250, 110, 220, 30)
        self.labelSeritIDValue.setStyleSheet(label_value_style)
        self.labelSeritIDValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit Dış Ölçüsü
        self.labelSeritDisOlcusu = QLabel("Şerit Dış Ölçüsü:", self.machineInfoFrame)
        self.labelSeritDisOlcusu.setGeometry(30, 150, 200, 30)
        self.labelSeritDisOlcusu.setStyleSheet(label_field_style)
        self.labelSeritDisOlcusuValue = QLabel("—", self.machineInfoFrame)
        self.labelSeritDisOlcusuValue.setGeometry(250, 150, 220, 30)
        self.labelSeritDisOlcusuValue.setStyleSheet(label_value_style)
        self.labelSeritDisOlcusuValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit Tipi
        self.labelSeritTipi = QLabel("Şerit Tipi:", self.machineInfoFrame)
        self.labelSeritTipi.setGeometry(30, 190, 200, 30)
        self.labelSeritTipi.setStyleSheet(label_field_style)
        self.labelSeritTipiValue = QLabel("—", self.machineInfoFrame)
        self.labelSeritTipiValue.setGeometry(250, 190, 220, 30)
        self.labelSeritTipiValue.setStyleSheet(label_value_style)
        self.labelSeritTipiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit Markası
        self.labelSeritMarkasi = QLabel("Şerit Markası:", self.machineInfoFrame)
        self.labelSeritMarkasi.setGeometry(30, 230, 200, 30)
        self.labelSeritMarkasi.setStyleSheet(label_field_style)
        self.labelSeritMarkasiValue = QLabel("—", self.machineInfoFrame)
        self.labelSeritMarkasiValue.setGeometry(250, 230, 220, 30)
        self.labelSeritMarkasiValue.setStyleSheet(label_value_style)
        self.labelSeritMarkasiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Band Şerit Malzemesi
        self.labelBandSeritMalzemesi = QLabel("Band Şerit Malzemesi:", self.machineInfoFrame)
        self.labelBandSeritMalzemesi.setGeometry(30, 270, 200, 30)
        self.labelBandSeritMalzemesi.setStyleSheet(label_field_style)
        self.labelBandSeritMalzemesiValue = QLabel("—", self.machineInfoFrame)
        self.labelBandSeritMalzemesiValue.setGeometry(250, 270, 220, 30)
        self.labelBandSeritMalzemesiValue.setStyleSheet(label_value_style)
        self.labelBandSeritMalzemesiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Malzeme Cinsi
        self.labelMalzemeCinsi = QLabel("Malzeme Cinsi:", self.machineInfoFrame)
        self.labelMalzemeCinsi.setGeometry(30, 310, 200, 30)
        self.labelMalzemeCinsi.setStyleSheet(label_field_style)
        self.labelMalzemeCinsiValue = QLabel("—", self.machineInfoFrame)
        self.labelMalzemeCinsiValue.setGeometry(250, 310, 220, 30)
        self.labelMalzemeCinsiValue.setStyleSheet(label_value_style)
        self.labelMalzemeCinsiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Malzeme Sertliği
        self.labelMalzemeSertligi = QLabel("Malzeme Sertliği:", self.machineInfoFrame)
        self.labelMalzemeSertligi.setGeometry(30, 350, 200, 30)
        self.labelMalzemeSertligi.setStyleSheet(label_field_style)
        self.labelMalzemeSertligiValue = QLabel("—", self.machineInfoFrame)
        self.labelMalzemeSertligiValue.setGeometry(250, 350, 220, 30)
        self.labelMalzemeSertligiValue.setStyleSheet(label_value_style)
        self.labelMalzemeSertligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Kesit Yapısı
        self.labelKesitYapisi = QLabel("Kesit Yapısı:", self.machineInfoFrame)
        self.labelKesitYapisi.setGeometry(30, 390, 200, 30)
        self.labelKesitYapisi.setStyleSheet(label_field_style)
        self.labelKesitYapisiValue = QLabel("—", self.machineInfoFrame)
        self.labelKesitYapisiValue.setGeometry(250, 390, 220, 30)
        self.labelKesitYapisiValue.setStyleSheet(label_value_style)
        self.labelKesitYapisiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # A, B, C, D değerleri
        self.labelABCD = QLabel("A, B, C, D (mm):", self.machineInfoFrame)
        self.labelABCD.setGeometry(30, 430, 200, 30)
        self.labelABCD.setStyleSheet(label_field_style)

        self.labelAValue = QLabel("—", self.machineInfoFrame)
        self.labelAValue.setGeometry(250, 430, 50, 30)
        self.labelAValue.setStyleSheet(label_value_style)
        self.labelAValue.setAlignment(Qt.AlignCenter)

        self.labelBValue = QLabel("—", self.machineInfoFrame)
        self.labelBValue.setGeometry(310, 430, 50, 30)
        self.labelBValue.setStyleSheet(label_value_style)
        self.labelBValue.setAlignment(Qt.AlignCenter)

        self.labelCValue = QLabel("—", self.machineInfoFrame)
        self.labelCValue.setGeometry(370, 430, 50, 30)
        self.labelCValue.setStyleSheet(label_value_style)
        self.labelCValue.setAlignment(Qt.AlignCenter)

        self.labelDValue = QLabel("—", self.machineInfoFrame)
        self.labelDValue.setGeometry(430, 430, 50, 30)
        self.labelDValue.setStyleSheet(label_value_style)
        self.labelDValue.setAlignment(Qt.AlignCenter)

        # === SENSOR DATA FRAME 1 (TOP CENTER) ===
        # Position: (520, 0, 500, 520)
        self.sensorData1Frame = QFrame(self)
        self.sensorData1Frame.setGeometry(520, 0, 500, 520)
        self.sensorData1Frame.setStyleSheet(frame_style)

        self.labelSensorData1Title = QLabel("Sensör Verileri", self.sensorData1Frame)
        self.labelSensorData1Title.setGeometry(25, 20, 450, 35)
        self.labelSensorData1Title.setStyleSheet(label_title_style)

        # Şerit Sapması
        self.labelSeritSapmasi = QLabel("Şerit Sapması:", self.sensorData1Frame)
        self.labelSeritSapmasi.setGeometry(30, 70, 200, 30)
        self.labelSeritSapmasi.setStyleSheet(label_field_style)
        self.labelSeritSapmasiValue = QLabel("—", self.sensorData1Frame)
        self.labelSeritSapmasiValue.setGeometry(250, 70, 220, 30)
        self.labelSeritSapmasiValue.setStyleSheet(label_value_style)
        self.labelSeritSapmasiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit Gerginliği
        self.labelSeritGerginligi = QLabel("Şerit Gerginliği (bar):", self.sensorData1Frame)
        self.labelSeritGerginligi.setGeometry(30, 110, 200, 30)
        self.labelSeritGerginligi.setStyleSheet(label_field_style)
        self.labelSeritGerginligiValue = QLabel("—", self.sensorData1Frame)
        self.labelSeritGerginligiValue.setGeometry(250, 110, 220, 30)
        self.labelSeritGerginligiValue.setStyleSheet(label_value_style)
        self.labelSeritGerginligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Kafa Yüksekliği
        self.labelKafaYuksekligi = QLabel("Kafa Yüksekliği (mm):", self.sensorData1Frame)
        self.labelKafaYuksekligi.setGeometry(30, 150, 200, 30)
        self.labelKafaYuksekligi.setStyleSheet(label_field_style)
        self.labelKafaYuksekligiValue = QLabel("—", self.sensorData1Frame)
        self.labelKafaYuksekligiValue.setGeometry(250, 150, 220, 30)
        self.labelKafaYuksekligiValue.setStyleSheet(label_value_style)
        self.labelKafaYuksekligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Titreşim X
        self.labelTitresimX = QLabel("Titreşim X:", self.sensorData1Frame)
        self.labelTitresimX.setGeometry(30, 190, 200, 30)
        self.labelTitresimX.setStyleSheet(label_field_style)
        self.labelTitresimXValue = QLabel("—", self.sensorData1Frame)
        self.labelTitresimXValue.setGeometry(250, 190, 220, 30)
        self.labelTitresimXValue.setStyleSheet(label_value_style)
        self.labelTitresimXValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Titreşim Y
        self.labelTitresimY = QLabel("Titreşim Y:", self.sensorData1Frame)
        self.labelTitresimY.setGeometry(30, 230, 200, 30)
        self.labelTitresimY.setStyleSheet(label_field_style)
        self.labelTitresimYValue = QLabel("—", self.sensorData1Frame)
        self.labelTitresimYValue.setGeometry(250, 230, 220, 30)
        self.labelTitresimYValue.setStyleSheet(label_value_style)
        self.labelTitresimYValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Titreşim Z
        self.labelTitresimZ = QLabel("Titreşim Z:", self.sensorData1Frame)
        self.labelTitresimZ.setGeometry(30, 270, 200, 30)
        self.labelTitresimZ.setStyleSheet(label_field_style)
        self.labelTitresimZValue = QLabel("—", self.sensorData1Frame)
        self.labelTitresimZValue.setGeometry(250, 270, 220, 30)
        self.labelTitresimZValue.setStyleSheet(label_value_style)
        self.labelTitresimZValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Mengene Basıncı
        self.labelMengeneBasinci = QLabel("Mengene Basıncı (bar):", self.sensorData1Frame)
        self.labelMengeneBasinci.setGeometry(30, 310, 200, 30)
        self.labelMengeneBasinci.setStyleSheet(label_field_style)
        self.labelMengeneBasinciValue = QLabel("—", self.sensorData1Frame)
        self.labelMengeneBasinciValue.setGeometry(250, 310, 220, 30)
        self.labelMengeneBasinciValue.setStyleSheet(label_value_style)
        self.labelMengeneBasinciValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Ortam Sıcaklığı
        self.labelOrtamSicakligi = QLabel("Ortam Sıcaklığı (°C):", self.sensorData1Frame)
        self.labelOrtamSicakligi.setGeometry(30, 350, 200, 30)
        self.labelOrtamSicakligi.setStyleSheet(label_field_style)
        self.labelOrtamSicakligiValue = QLabel("—", self.sensorData1Frame)
        self.labelOrtamSicakligiValue.setGeometry(250, 350, 220, 30)
        self.labelOrtamSicakligiValue.setStyleSheet(label_value_style)
        self.labelOrtamSicakligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Ortam Nem
        self.labelOrtamNem = QLabel("Ortam Nem (%):", self.sensorData1Frame)
        self.labelOrtamNem.setGeometry(30, 390, 200, 30)
        self.labelOrtamNem.setStyleSheet(label_field_style)
        self.labelOrtamNemValue = QLabel("—", self.sensorData1Frame)
        self.labelOrtamNemValue.setGeometry(250, 390, 220, 30)
        self.labelOrtamNemValue.setStyleSheet(label_value_style)
        self.labelOrtamNemValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Kesilen Parça Adeti
        self.labelKesilenParcaAdeti = QLabel("Kesilen Parça Adeti:", self.sensorData1Frame)
        self.labelKesilenParcaAdeti.setGeometry(30, 430, 200, 30)
        self.labelKesilenParcaAdeti.setStyleSheet(label_field_style)
        self.labelKesilenParcaAdetiValue = QLabel("—", self.sensorData1Frame)
        self.labelKesilenParcaAdetiValue.setGeometry(250, 430, 220, 30)
        self.labelKesilenParcaAdetiValue.setStyleSheet(label_value_style)
        self.labelKesilenParcaAdetiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # === STATUS & MOTOR DATA FRAME (TOP RIGHT) ===
        # Position: (1040, 0, 488, 520)
        self.statusMotorFrame = QFrame(self)
        self.statusMotorFrame.setGeometry(1040, 0, 488, 520)
        self.statusMotorFrame.setStyleSheet(frame_style)

        self.labelStatusMotorTitle = QLabel("Durum ve Motor Verileri", self.statusMotorFrame)
        self.labelStatusMotorTitle.setGeometry(25, 20, 438, 35)
        self.labelStatusMotorTitle.setStyleSheet(label_title_style)

        # Testere Durumu
        self.labelTestereDurum = QLabel("Testere Durumu:", self.statusMotorFrame)
        self.labelTestereDurum.setGeometry(30, 70, 200, 30)
        self.labelTestereDurum.setStyleSheet(label_field_style)
        self.labelTestereDurumValue = QLabel("—", self.statusMotorFrame)
        self.labelTestereDurumValue.setGeometry(250, 70, 210, 30)
        self.labelTestereDurumValue.setStyleSheet(label_value_style)
        self.labelTestereDurumValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Alarm Status
        self.labelAlarmStatus = QLabel("Alarm Status:", self.statusMotorFrame)
        self.labelAlarmStatus.setGeometry(30, 110, 200, 30)
        self.labelAlarmStatus.setStyleSheet(label_field_style)
        self.labelAlarmStatusValue = QLabel("—", self.statusMotorFrame)
        self.labelAlarmStatusValue.setGeometry(250, 110, 210, 30)
        self.labelAlarmStatusValue.setStyleSheet(label_value_style)
        self.labelAlarmStatusValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit Motor Hızı
        self.labelSeritMotorHiz = QLabel("Şerit Motor Hızı:", self.statusMotorFrame)
        self.labelSeritMotorHiz.setGeometry(30, 150, 200, 30)
        self.labelSeritMotorHiz.setStyleSheet(label_field_style)
        self.labelSeritMotorHizValue = QLabel("—", self.statusMotorFrame)
        self.labelSeritMotorHizValue.setGeometry(250, 150, 210, 30)
        self.labelSeritMotorHizValue.setStyleSheet(label_value_style)
        self.labelSeritMotorHizValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # İnme Motor Hızı
        self.labelInmeMotorHiz = QLabel("İnme Motor Hızı:", self.statusMotorFrame)
        self.labelInmeMotorHiz.setGeometry(30, 190, 200, 30)
        self.labelInmeMotorHiz.setStyleSheet(label_field_style)
        self.labelInmeMotorHizValue = QLabel("—", self.statusMotorFrame)
        self.labelInmeMotorHizValue.setGeometry(250, 190, 210, 30)
        self.labelInmeMotorHizValue.setStyleSheet(label_value_style)
        self.labelInmeMotorHizValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit Motor Akımı
        self.labelSeritMotorAkim = QLabel("Şerit Motor Akımı (A):", self.statusMotorFrame)
        self.labelSeritMotorAkim.setGeometry(30, 230, 200, 30)
        self.labelSeritMotorAkim.setStyleSheet(label_field_style)
        self.labelSeritMotorAkimValue = QLabel("—", self.statusMotorFrame)
        self.labelSeritMotorAkimValue.setGeometry(250, 230, 210, 30)
        self.labelSeritMotorAkimValue.setStyleSheet(label_value_style)
        self.labelSeritMotorAkimValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # İnme Motor Akımı
        self.labelInmeMotorAkim = QLabel("İnme Motor Akımı (A):", self.statusMotorFrame)
        self.labelInmeMotorAkim.setGeometry(30, 270, 200, 30)
        self.labelInmeMotorAkim.setStyleSheet(label_field_style)
        self.labelInmeMotorAkimValue = QLabel("—", self.statusMotorFrame)
        self.labelInmeMotorAkimValue.setGeometry(250, 270, 210, 30)
        self.labelInmeMotorAkimValue.setStyleSheet(label_value_style)
        self.labelInmeMotorAkimValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Şerit Motor Torku
        self.labelSeritMotorTork = QLabel("Şerit Motor Torku (%):", self.statusMotorFrame)
        self.labelSeritMotorTork.setGeometry(30, 310, 200, 30)
        self.labelSeritMotorTork.setStyleSheet(label_field_style)
        self.labelSeritMotorTorkValue = QLabel("—", self.statusMotorFrame)
        self.labelSeritMotorTorkValue.setGeometry(250, 310, 210, 30)
        self.labelSeritMotorTorkValue.setStyleSheet(label_value_style)
        self.labelSeritMotorTorkValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # İnme Motor Torku
        self.labelInmeMotorTork = QLabel("İnme Motor Torku (%):", self.statusMotorFrame)
        self.labelInmeMotorTork.setGeometry(30, 350, 200, 30)
        self.labelInmeMotorTork.setStyleSheet(label_field_style)
        self.labelInmeMotorTorkValue = QLabel("—", self.statusMotorFrame)
        self.labelInmeMotorTorkValue.setGeometry(250, 350, 210, 30)
        self.labelInmeMotorTorkValue.setStyleSheet(label_value_style)
        self.labelInmeMotorTorkValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Max Band Deviation
        self.labelMaxBandDeviation = QLabel("Max Band Deviation:", self.statusMotorFrame)
        self.labelMaxBandDeviation.setGeometry(30, 390, 200, 30)
        self.labelMaxBandDeviation.setStyleSheet(label_field_style)
        self.labelMaxBandDeviationValue = QLabel("—", self.statusMotorFrame)
        self.labelMaxBandDeviationValue.setGeometry(250, 390, 210, 30)
        self.labelMaxBandDeviationValue.setStyleSheet(label_value_style)
        self.labelMaxBandDeviationValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _setup_timers(self):
        """Setup all Qt timers for periodic updates."""
        # Data update timer (if callback provided)
        if self.get_data_callback:
            self._data_timer = QTimer(self)
            self._data_timer.timeout.connect(self._on_data_tick)
            self._data_timer.start(200)  # 200ms

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

    def update_data(self, processed_data: Dict):
        """
        Update display with latest data.

        Args:
            processed_data: Dictionary containing sensor and machine data
        """
        try:
            # Check if data is available
            if not processed_data or not processed_data.get('modbus_connected', False):
                # No data or not connected: show placeholders
                self._update_values({})
            else:
                self._update_values(processed_data)

        except Exception as e:
            logger.error(f"Data update error: {e}")

    def _update_values(self, processed_data: Dict):
        """Update all displayed values (thread-safe)."""
        try:
            with self._values_lock:
                # Machine and band info
                self.current_values['makine_id'] = processed_data.get('makine_id', '—')
                self.current_values['serit_id'] = processed_data.get('serit_id', '—')
                self.current_values['serit_dis_mm'] = processed_data.get('serit_dis_mm', '—')
                self.current_values['serit_tip'] = processed_data.get('serit_tip', '—')
                self.current_values['serit_marka'] = processed_data.get('serit_marka', '—')
                self.current_values['serit_malz'] = processed_data.get('serit_malz', '—')
                self.current_values['malzeme_cinsi'] = processed_data.get('malzeme_cinsi', '—')
                self.current_values['malzeme_sertlik'] = processed_data.get('malzeme_sertlik', '—')
                self.current_values['kesit_yapisi'] = processed_data.get('kesit_yapisi', '—')
                self.current_values['a_mm'] = processed_data.get('a_mm', '—')
                self.current_values['b_mm'] = processed_data.get('b_mm', '—')
                self.current_values['c_mm'] = processed_data.get('c_mm', '—')
                self.current_values['d_mm'] = processed_data.get('d_mm', '—')

                # Sensor data
                serit_sapmasi = processed_data.get('serit_sapmasi', None)
                if serit_sapmasi is not None and serit_sapmasi != '':
                    try:
                        self.current_values['serit_sapmasi'] = f"{float(serit_sapmasi):.2f}"
                    except (ValueError, TypeError):
                        self.current_values['serit_sapmasi'] = '—'
                else:
                    self.current_values['serit_sapmasi'] = '—'

                self.current_values['serit_gerginligi_bar'] = processed_data.get('serit_gerginligi_bar', '—')
                self.current_values['kafa_yuksekligi_mm'] = processed_data.get('kafa_yuksekligi_mm', '—')
                self.current_values['ivme_olcer_x'] = processed_data.get('ivme_olcer_x', '—')
                self.current_values['ivme_olcer_y'] = processed_data.get('ivme_olcer_y', '—')
                self.current_values['ivme_olcer_z'] = processed_data.get('ivme_olcer_z', '—')
                self.current_values['mengene_basinc_bar'] = processed_data.get('mengene_basinc_bar', '—')
                self.current_values['ortam_sicakligi_c'] = processed_data.get('ortam_sicakligi_c', '—')
                self.current_values['ortam_nem_percentage'] = processed_data.get('ortam_nem_percentage', '—')
                self.current_values['kesilen_parca_adeti'] = processed_data.get('kesilen_parca_adeti', '—')

                # Status and motor data
                testere_durumu = processed_data.get('testere_durumu', 0)
                if isinstance(testere_durumu, (int, float)):
                    durum_text = {
                        0: "BOŞTA",
                        1: "HİDROLİK AKTİF",
                        2: "ŞERİT MOTOR ÇALIŞIYOR",
                        3: "KESİM YAPILIYOR",
                        4: "KESİM BİTTİ",
                        5: "ŞERİT YUKARI ÇIKIYOR",
                        6: "MALZEME BESLEME"
                    }.get(int(testere_durumu), "BİLİNMİYOR")
                    self.current_values['testere_durumu'] = durum_text
                else:
                    self.current_values['testere_durumu'] = processed_data.get('testere_durumu', '—')

                self.current_values['alarm_status'] = processed_data.get('alarm_status', '—')
                self.current_values['serit_kesme_hizi'] = processed_data.get('serit_kesme_hizi', '—')
                self.current_values['serit_inme_hizi'] = processed_data.get('serit_inme_hizi', '—')
                self.current_values['serit_motor_akim_a'] = processed_data.get('serit_motor_akim_a', '—')
                self.current_values['inme_motor_akim_a'] = processed_data.get('inme_motor_akim_a', '—')
                self.current_values['serit_motor_tork_percentage'] = processed_data.get('serit_motor_tork_percentage', '—')
                self.current_values['inme_motor_tork_percentage'] = processed_data.get('inme_motor_tork_percentage', '—')

            # Update UI labels (outside lock)
            self._update_ui_labels()

        except Exception as e:
            logger.error(f"Values update error: {e}")

    def _update_ui_labels(self):
        """Update all UI labels with current values."""
        try:
            # Format helper function
            def format_value(value):
                """Format value for display, showing '—' for empty/None values."""
                if value is None or value == '' or value == '-':
                    return '—'
                return str(value)

            # Machine and band info
            self.labelMakineIDValue.setText(format_value(self.current_values.get('makine_id')))
            self.labelSeritIDValue.setText(format_value(self.current_values.get('serit_id')))
            self.labelSeritDisOlcusuValue.setText(format_value(self.current_values.get('serit_dis_mm')))
            self.labelSeritTipiValue.setText(format_value(self.current_values.get('serit_tip')))
            self.labelSeritMarkasiValue.setText(format_value(self.current_values.get('serit_marka')))
            self.labelBandSeritMalzemesiValue.setText(format_value(self.current_values.get('serit_malz')))
            self.labelMalzemeCinsiValue.setText(format_value(self.current_values.get('malzeme_cinsi')))
            self.labelMalzemeSertligiValue.setText(format_value(self.current_values.get('malzeme_sertlik')))
            self.labelKesitYapisiValue.setText(format_value(self.current_values.get('kesit_yapisi')))
            self.labelAValue.setText(format_value(self.current_values.get('a_mm')))
            self.labelBValue.setText(format_value(self.current_values.get('b_mm')))
            self.labelCValue.setText(format_value(self.current_values.get('c_mm')))
            self.labelDValue.setText(format_value(self.current_values.get('d_mm')))

            # Sensor data
            self.labelSeritSapmasiValue.setText(format_value(self.current_values.get('serit_sapmasi')))
            self.labelSeritGerginligiValue.setText(format_value(self.current_values.get('serit_gerginligi_bar')))
            self.labelKafaYuksekligiValue.setText(format_value(self.current_values.get('kafa_yuksekligi_mm')))
            self.labelTitresimXValue.setText(format_value(self.current_values.get('ivme_olcer_x')))
            self.labelTitresimYValue.setText(format_value(self.current_values.get('ivme_olcer_y')))
            self.labelTitresimZValue.setText(format_value(self.current_values.get('ivme_olcer_z')))
            self.labelMengeneBasinciValue.setText(format_value(self.current_values.get('mengene_basinc_bar')))
            self.labelOrtamSicakligiValue.setText(format_value(self.current_values.get('ortam_sicakligi_c')))
            self.labelOrtamNemValue.setText(format_value(self.current_values.get('ortam_nem_percentage')))
            self.labelKesilenParcaAdetiValue.setText(format_value(self.current_values.get('kesilen_parca_adeti')))

            # Status and motor data
            self.labelTestereDurumValue.setText(format_value(self.current_values.get('testere_durumu')))
            self.labelAlarmStatusValue.setText(format_value(self.current_values.get('alarm_status')))
            self.labelSeritMotorHizValue.setText(format_value(self.current_values.get('serit_kesme_hizi')))
            self.labelInmeMotorHizValue.setText(format_value(self.current_values.get('serit_inme_hizi')))
            self.labelSeritMotorAkimValue.setText(format_value(self.current_values.get('serit_motor_akim_a')))
            self.labelInmeMotorAkimValue.setText(format_value(self.current_values.get('inme_motor_akim_a')))
            self.labelSeritMotorTorkValue.setText(format_value(self.current_values.get('serit_motor_tork_percentage')))
            self.labelInmeMotorTorkValue.setText(format_value(self.current_values.get('inme_motor_tork_percentage')))
            self.labelMaxBandDeviationValue.setText(format_value(self.current_values.get('serit_sapmasi')))

        except Exception as e:
            logger.error(f"UI labels update error: {e}")

    # No cleanup() method needed - PySide6 handles timer cleanup automatically
    # when widget is destroyed via parent-child relationships
