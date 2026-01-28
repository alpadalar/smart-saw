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
            'inme_motor_tork_percentage': '—',
            'guc_kwh': '—'
        }

    def _setup_ui(self):
        """Setup the complete UI with all frames and widgets - matching old UI layout."""
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

        inner_frame_style = """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                border-radius: 20px;
            }
        """

        label_name_style = """
            QLabel {
                background-color: transparent;
                color: rgba(244, 246, 252, 151);
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
                font-size: 36px;
            }
        """

        # ============================================================
        # CONTAINER 1: Makine & Şerit Bilgileri (Sol Üst)
        # Eski: (425, 127, 582, 435) -> Yeni: (33, 127, 582, 435)
        # ============================================================
        self.Container = QFrame(self)
        self.Container.setGeometry(33, 127, 582, 435)
        self.Container.setStyleSheet(frame_style)

        # --- FrameMakineID (20, 27, 260, 105) ---
        self.FrameMakineID = QFrame(self.Container)
        self.FrameMakineID.setGeometry(20, 27, 260, 105)
        self.FrameMakineID.setStyleSheet(inner_frame_style)

        self.labelMakineID = QLabel("Makine ID", self.FrameMakineID)
        self.labelMakineID.setGeometry(33, 20, 201, 20)
        self.labelMakineID.setStyleSheet(label_name_style)

        self.labelMakineIDValue = QLabel("—", self.FrameMakineID)
        self.labelMakineIDValue.setGeometry(30, 43, 211, 50)
        self.labelMakineIDValue.setStyleSheet(label_value_style)
        self.labelMakineIDValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritID (297, 27, 260, 105) ---
        self.FrameSeritID = QFrame(self.Container)
        self.FrameSeritID.setGeometry(297, 27, 260, 105)
        self.FrameSeritID.setStyleSheet(inner_frame_style)

        self.labelSeritID = QLabel("Şerit ID", self.FrameSeritID)
        self.labelSeritID.setGeometry(33, 20, 201, 20)
        self.labelSeritID.setStyleSheet(label_name_style)

        self.labelSeritIDValue = QLabel("—", self.FrameSeritID)
        self.labelSeritIDValue.setGeometry(30, 43, 211, 50)
        self.labelSeritIDValue.setStyleSheet(label_value_style)
        self.labelSeritIDValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritDisOlcusu (20, 166, 260, 105) ---
        self.FrameSeritDisOlcusu = QFrame(self.Container)
        self.FrameSeritDisOlcusu.setGeometry(20, 166, 260, 105)
        self.FrameSeritDisOlcusu.setStyleSheet(inner_frame_style)

        self.labelSeritDisOlcusu = QLabel("Şerit Dış Ölçüsü", self.FrameSeritDisOlcusu)
        self.labelSeritDisOlcusu.setGeometry(33, 20, 201, 20)
        self.labelSeritDisOlcusu.setStyleSheet(label_name_style)

        self.labelSeritDisOlcusuValue = QLabel("—", self.FrameSeritDisOlcusu)
        self.labelSeritDisOlcusuValue.setGeometry(30, 43, 211, 50)
        self.labelSeritDisOlcusuValue.setStyleSheet(label_value_style)
        self.labelSeritDisOlcusuValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritTipi (297, 166, 260, 105) ---
        self.FrameSeritTipi = QFrame(self.Container)
        self.FrameSeritTipi.setGeometry(297, 166, 260, 105)
        self.FrameSeritTipi.setStyleSheet(inner_frame_style)

        self.labelSeritTipi = QLabel("Şerit Tipi", self.FrameSeritTipi)
        self.labelSeritTipi.setGeometry(33, 20, 201, 20)
        self.labelSeritTipi.setStyleSheet(label_name_style)

        self.labelSeritTipiValue = QLabel("—", self.FrameSeritTipi)
        self.labelSeritTipiValue.setGeometry(30, 43, 211, 50)
        self.labelSeritTipiValue.setStyleSheet(label_value_style)
        self.labelSeritTipiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritMarkasi (20, 306, 260, 105) ---
        self.FrameSeritMarkasi = QFrame(self.Container)
        self.FrameSeritMarkasi.setGeometry(20, 306, 260, 105)
        self.FrameSeritMarkasi.setStyleSheet(inner_frame_style)

        self.labelSeritMarkasi = QLabel("Şerit Markası", self.FrameSeritMarkasi)
        self.labelSeritMarkasi.setGeometry(33, 20, 201, 20)
        self.labelSeritMarkasi.setStyleSheet(label_name_style)

        self.labelSeritMarkasiValue = QLabel("—", self.FrameSeritMarkasi)
        self.labelSeritMarkasiValue.setGeometry(30, 43, 211, 50)
        self.labelSeritMarkasiValue.setStyleSheet(label_value_style)
        self.labelSeritMarkasiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritMalzemesi (297, 306, 260, 105) ---
        self.FrameSeritMalzemesi = QFrame(self.Container)
        self.FrameSeritMalzemesi.setGeometry(297, 306, 260, 105)
        self.FrameSeritMalzemesi.setStyleSheet(inner_frame_style)

        self.labelBandSeritMalzemesi = QLabel("Şerit Malzemesi", self.FrameSeritMalzemesi)
        self.labelBandSeritMalzemesi.setGeometry(33, 20, 201, 20)
        self.labelBandSeritMalzemesi.setStyleSheet(label_name_style)

        self.labelBandSeritMalzemesiValue = QLabel("—", self.FrameSeritMalzemesi)
        self.labelBandSeritMalzemesiValue.setGeometry(30, 43, 211, 50)
        self.labelBandSeritMalzemesiValue.setStyleSheet(label_value_style)
        self.labelBandSeritMalzemesiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ============================================================
        # CONTAINER 2: Motor Verileri (Sol Alt)
        # Eski: (425, 577, 582, 435) -> Yeni: (33, 547, 582, 495)
        # Genişletildi: Güç (kWh) göstergesi için 4. satır eklendi
        # ============================================================
        self.Container_2 = QFrame(self)
        self.Container_2.setGeometry(33, 547, 582, 495)
        self.Container_2.setStyleSheet(frame_style)

        # --- FrameSeritMotorHiz (20, 27, 260, 105) ---
        self.FrameSeritMotorHiz = QFrame(self.Container_2)
        self.FrameSeritMotorHiz.setGeometry(20, 27, 260, 105)
        self.FrameSeritMotorHiz.setStyleSheet(inner_frame_style)

        self.labelSeritMotorHiz = QLabel("Şerit Motor Hızı (m/dk)", self.FrameSeritMotorHiz)
        self.labelSeritMotorHiz.setGeometry(33, 20, 201, 20)
        self.labelSeritMotorHiz.setStyleSheet(label_name_style)

        self.labelSeritMotorHizValue = QLabel("—", self.FrameSeritMotorHiz)
        self.labelSeritMotorHizValue.setGeometry(30, 43, 211, 50)
        self.labelSeritMotorHizValue.setStyleSheet(label_value_style)
        self.labelSeritMotorHizValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameInmeMotorHiz (297, 27, 260, 105) ---
        self.FrameInmeMotorHiz = QFrame(self.Container_2)
        self.FrameInmeMotorHiz.setGeometry(297, 27, 260, 105)
        self.FrameInmeMotorHiz.setStyleSheet(inner_frame_style)

        self.labelInmeMotorHiz = QLabel("İlerleme Motor Hızı (mm/dk)", self.FrameInmeMotorHiz)
        self.labelInmeMotorHiz.setGeometry(33, 20, 201, 20)
        self.labelInmeMotorHiz.setStyleSheet(label_name_style)

        self.labelInmeMotorHizValue = QLabel("—", self.FrameInmeMotorHiz)
        self.labelInmeMotorHizValue.setGeometry(30, 43, 211, 50)
        self.labelInmeMotorHizValue.setStyleSheet(label_value_style)
        self.labelInmeMotorHizValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritMotorAkim (20, 166, 260, 105) ---
        self.FrameSeritMotorAkim = QFrame(self.Container_2)
        self.FrameSeritMotorAkim.setGeometry(20, 166, 260, 105)
        self.FrameSeritMotorAkim.setStyleSheet(inner_frame_style)

        self.labelSeritMotorAkim = QLabel("Şerit Motor Akımı (A)", self.FrameSeritMotorAkim)
        self.labelSeritMotorAkim.setGeometry(33, 20, 211, 20)
        self.labelSeritMotorAkim.setStyleSheet(label_name_style)

        self.labelSeritMotorAkimValue = QLabel("—", self.FrameSeritMotorAkim)
        self.labelSeritMotorAkimValue.setGeometry(30, 43, 211, 50)
        self.labelSeritMotorAkimValue.setStyleSheet(label_value_style)
        self.labelSeritMotorAkimValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameInmeMotorAkim (297, 166, 260, 105) ---
        self.FrameInmeMotorAkim = QFrame(self.Container_2)
        self.FrameInmeMotorAkim.setGeometry(297, 166, 260, 105)
        self.FrameInmeMotorAkim.setStyleSheet(inner_frame_style)

        self.labelInmeMotorAkim = QLabel("İlerleme Motor Akımı (A)", self.FrameInmeMotorAkim)
        self.labelInmeMotorAkim.setGeometry(33, 20, 211, 20)
        self.labelInmeMotorAkim.setStyleSheet(label_name_style)

        self.labelInmeMotorAkimValue = QLabel("—", self.FrameInmeMotorAkim)
        self.labelInmeMotorAkimValue.setGeometry(30, 43, 211, 50)
        self.labelInmeMotorAkimValue.setStyleSheet(label_value_style)
        self.labelInmeMotorAkimValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritMotorTork (20, 306, 260, 105) ---
        self.FrameSeritMotorTork = QFrame(self.Container_2)
        self.FrameSeritMotorTork.setGeometry(20, 306, 260, 105)
        self.FrameSeritMotorTork.setStyleSheet(inner_frame_style)

        self.labelSeritMotorTork = QLabel("Şerit Motor Torku (%)", self.FrameSeritMotorTork)
        self.labelSeritMotorTork.setGeometry(33, 20, 201, 20)
        self.labelSeritMotorTork.setStyleSheet(label_name_style)

        self.labelSeritMotorTorkValue = QLabel("—", self.FrameSeritMotorTork)
        self.labelSeritMotorTorkValue.setGeometry(30, 43, 211, 50)
        self.labelSeritMotorTorkValue.setStyleSheet(label_value_style)
        self.labelSeritMotorTorkValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameInmeMotorTork (297, 306, 260, 105) ---
        self.FrameInmeMotorTork = QFrame(self.Container_2)
        self.FrameInmeMotorTork.setGeometry(297, 306, 260, 105)
        self.FrameInmeMotorTork.setStyleSheet(inner_frame_style)

        self.labelInmeMotorTork = QLabel("İlerleme Motor Torku (%)", self.FrameInmeMotorTork)
        self.labelInmeMotorTork.setGeometry(33, 20, 211, 20)
        self.labelInmeMotorTork.setStyleSheet(label_name_style)

        self.labelInmeMotorTorkValue = QLabel("—", self.FrameInmeMotorTork)
        self.labelInmeMotorTorkValue.setGeometry(30, 43, 211, 50)
        self.labelInmeMotorTorkValue.setStyleSheet(label_value_style)
        self.labelInmeMotorTorkValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameGucKwh (20, 420, 537, 60) --- Full width for power display
        self.FrameGucKwh = QFrame(self.Container_2)
        self.FrameGucKwh.setGeometry(20, 420, 537, 60)
        self.FrameGucKwh.setStyleSheet(inner_frame_style)

        self.labelGucKwh = QLabel("Güç (kWh)", self.FrameGucKwh)
        self.labelGucKwh.setGeometry(33, 10, 201, 20)
        self.labelGucKwh.setStyleSheet(label_name_style)

        self.labelGucKwhValue = QLabel("—", self.FrameGucKwh)
        self.labelGucKwhValue.setGeometry(200, 10, 320, 40)
        self.labelGucKwhValue.setStyleSheet(label_value_style)
        self.labelGucKwhValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ============================================================
        # CONTAINER 3: Malzeme Bilgileri (Sağ Üst)
        # Eski: (1033, 127, 857, 281) -> Yeni: (641, 127, 857, 281)
        # ============================================================
        self.Container_3 = QFrame(self)
        self.Container_3.setGeometry(641, 127, 857, 281)
        self.Container_3.setStyleSheet(frame_style)

        # --- FrameMalzemeCinsi (20, 27, 260, 105) ---
        self.FrameMalzemeCinsi = QFrame(self.Container_3)
        self.FrameMalzemeCinsi.setGeometry(20, 27, 260, 105)
        self.FrameMalzemeCinsi.setStyleSheet(inner_frame_style)

        self.labelMalzemeCinsi = QLabel("Malzeme Cinsi", self.FrameMalzemeCinsi)
        self.labelMalzemeCinsi.setGeometry(33, 20, 201, 20)
        self.labelMalzemeCinsi.setStyleSheet(label_name_style)

        self.labelMalzemeCinsiValue = QLabel("—", self.FrameMalzemeCinsi)
        self.labelMalzemeCinsiValue.setGeometry(30, 43, 211, 50)
        self.labelMalzemeCinsiValue.setStyleSheet(label_value_style)
        self.labelMalzemeCinsiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameMalzemeSertligi (300, 27, 260, 105) ---
        self.FrameMalzemeSertligi = QFrame(self.Container_3)
        self.FrameMalzemeSertligi.setGeometry(300, 27, 260, 105)
        self.FrameMalzemeSertligi.setStyleSheet(inner_frame_style)

        self.labelMalzemeSertligi = QLabel("Malzeme Sertliği", self.FrameMalzemeSertligi)
        self.labelMalzemeSertligi.setGeometry(33, 20, 211, 31)
        self.labelMalzemeSertligi.setStyleSheet(label_name_style)

        self.labelMalzemeSertligiValue = QLabel("—", self.FrameMalzemeSertligi)
        self.labelMalzemeSertligiValue.setGeometry(30, 43, 211, 50)
        self.labelMalzemeSertligiValue.setStyleSheet(label_value_style)
        self.labelMalzemeSertligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameKesitYapisi (580, 27, 260, 105) ---
        self.FrameKesitYapisi = QFrame(self.Container_3)
        self.FrameKesitYapisi.setGeometry(580, 27, 260, 105)
        self.FrameKesitYapisi.setStyleSheet(inner_frame_style)

        self.labelKesitYapisi = QLabel("Kesit Yapısı", self.FrameKesitYapisi)
        self.labelKesitYapisi.setGeometry(33, 20, 201, 31)
        self.labelKesitYapisi.setStyleSheet(label_name_style)

        self.labelKesitYapisiValue = QLabel("—", self.FrameKesitYapisi)
        self.labelKesitYapisiValue.setGeometry(30, 43, 211, 50)
        self.labelKesitYapisiValue.setStyleSheet(label_value_style)
        self.labelKesitYapisiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameABCD (20, 154, 820, 105) ---
        self.FrameABCD = QFrame(self.Container_3)
        self.FrameABCD.setGeometry(20, 154, 820, 105)
        self.FrameABCD.setStyleSheet(inner_frame_style)

        self.labelA = QLabel("A (mm)", self.FrameABCD)
        self.labelA.setGeometry(24, 19, 131, 20)
        self.labelA.setStyleSheet(label_name_style)

        self.labelAValue = QLabel("—", self.FrameABCD)
        self.labelAValue.setGeometry(1, 43, 161, 50)
        self.labelAValue.setStyleSheet(label_value_style)
        self.labelAValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.labelB = QLabel("B (mm)", self.FrameABCD)
        self.labelB.setGeometry(237, 19, 131, 20)
        self.labelB.setStyleSheet(label_name_style)

        self.labelBValue = QLabel("—", self.FrameABCD)
        self.labelBValue.setGeometry(210, 40, 161, 50)
        self.labelBValue.setStyleSheet(label_value_style)
        self.labelBValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.labelC = QLabel("C (mm)", self.FrameABCD)
        self.labelC.setGeometry(450, 19, 121, 20)
        self.labelC.setStyleSheet(label_name_style)

        self.labelCValue = QLabel("—", self.FrameABCD)
        self.labelCValue.setGeometry(424, 40, 161, 50)
        self.labelCValue.setStyleSheet(label_value_style)
        self.labelCValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.labelD = QLabel("D (mm)", self.FrameABCD)
        self.labelD.setGeometry(663, 19, 141, 20)
        self.labelD.setStyleSheet(label_name_style)

        self.labelDValue = QLabel("—", self.FrameABCD)
        self.labelDValue.setGeometry(640, 40, 161, 50)
        self.labelDValue.setStyleSheet(label_value_style)
        self.labelDValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ============================================================
        # CONTAINER 4: Sensör Verileri (Sağ Orta)
        # Eski: (1033, 424, 857, 412) -> Yeni: (641, 424, 857, 412)
        # ============================================================
        self.Container_4 = QFrame(self)
        self.Container_4.setGeometry(641, 424, 857, 412)
        self.Container_4.setStyleSheet(frame_style)

        # --- FrameSeritSapmasi (20, 27, 260, 105) ---
        self.FrameSeritSapmasi = QFrame(self.Container_4)
        self.FrameSeritSapmasi.setGeometry(20, 27, 260, 105)
        self.FrameSeritSapmasi.setStyleSheet(inner_frame_style)

        self.labelSeritSapmasi = QLabel("Şerit Sapması", self.FrameSeritSapmasi)
        self.labelSeritSapmasi.setGeometry(33, 20, 201, 20)
        self.labelSeritSapmasi.setStyleSheet(label_name_style)

        self.labelSeritSapmasiValue = QLabel("—", self.FrameSeritSapmasi)
        self.labelSeritSapmasiValue.setGeometry(30, 43, 211, 50)
        self.labelSeritSapmasiValue.setStyleSheet(label_value_style)
        self.labelSeritSapmasiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameSeritGerginligi (300, 27, 260, 105) ---
        self.FrameSeritGerginligi = QFrame(self.Container_4)
        self.FrameSeritGerginligi.setGeometry(300, 27, 260, 105)
        self.FrameSeritGerginligi.setStyleSheet(inner_frame_style)

        self.labelSeritGerginligi = QLabel("Şerit Gerginliği (bar)", self.FrameSeritGerginligi)
        self.labelSeritGerginligi.setGeometry(33, 20, 211, 20)
        self.labelSeritGerginligi.setStyleSheet(label_name_style)

        self.labelSeritGerginligiValue = QLabel("—", self.FrameSeritGerginligi)
        self.labelSeritGerginligiValue.setGeometry(30, 43, 211, 50)
        self.labelSeritGerginligiValue.setStyleSheet(label_value_style)
        self.labelSeritGerginligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameKafaYuksekligi (580, 27, 260, 105) ---
        self.FrameKafaYuksekligi = QFrame(self.Container_4)
        self.FrameKafaYuksekligi.setGeometry(580, 27, 260, 105)
        self.FrameKafaYuksekligi.setStyleSheet(inner_frame_style)

        self.labelKafaYuksekligi = QLabel("Kafa Yüksekliği (mm)", self.FrameKafaYuksekligi)
        self.labelKafaYuksekligi.setGeometry(33, 20, 211, 20)
        self.labelKafaYuksekligi.setStyleSheet(label_name_style)

        self.labelKafaYuksekligiValue = QLabel("—", self.FrameKafaYuksekligi)
        self.labelKafaYuksekligiValue.setGeometry(30, 43, 211, 50)
        self.labelKafaYuksekligiValue.setStyleSheet(label_value_style)
        self.labelKafaYuksekligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameTitresimX (20, 154, 260, 105) ---
        self.FrameTitresimX = QFrame(self.Container_4)
        self.FrameTitresimX.setGeometry(20, 154, 260, 105)
        self.FrameTitresimX.setStyleSheet(inner_frame_style)

        self.labelTitresimX = QLabel("Titreşim X", self.FrameTitresimX)
        self.labelTitresimX.setGeometry(33, 20, 201, 20)
        self.labelTitresimX.setStyleSheet(label_name_style)

        self.labelTitresimXValue = QLabel("—", self.FrameTitresimX)
        self.labelTitresimXValue.setGeometry(30, 43, 211, 50)
        self.labelTitresimXValue.setStyleSheet(label_value_style)
        self.labelTitresimXValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameTitresimY (300, 154, 260, 105) ---
        self.FrameTitresimY = QFrame(self.Container_4)
        self.FrameTitresimY.setGeometry(300, 154, 260, 105)
        self.FrameTitresimY.setStyleSheet(inner_frame_style)

        self.labelTitresimY = QLabel("Titreşim Y", self.FrameTitresimY)
        self.labelTitresimY.setGeometry(33, 20, 201, 20)
        self.labelTitresimY.setStyleSheet(label_name_style)

        self.labelTitresimYValue = QLabel("—", self.FrameTitresimY)
        self.labelTitresimYValue.setGeometry(30, 43, 211, 50)
        self.labelTitresimYValue.setStyleSheet(label_value_style)
        self.labelTitresimYValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameTitresimZ (580, 154, 260, 105) ---
        self.FrameTitresimZ = QFrame(self.Container_4)
        self.FrameTitresimZ.setGeometry(580, 154, 260, 105)
        self.FrameTitresimZ.setStyleSheet(inner_frame_style)

        self.labelTitresimZ = QLabel("Titreşim Z", self.FrameTitresimZ)
        self.labelTitresimZ.setGeometry(33, 20, 201, 20)
        self.labelTitresimZ.setStyleSheet(label_name_style)

        self.labelTitresimZValue = QLabel("—", self.FrameTitresimZ)
        self.labelTitresimZValue.setGeometry(30, 43, 211, 50)
        self.labelTitresimZValue.setStyleSheet(label_value_style)
        self.labelTitresimZValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameMengeneBasinci (20, 281, 260, 105) ---
        self.FrameMengeneBasinci = QFrame(self.Container_4)
        self.FrameMengeneBasinci.setGeometry(20, 281, 260, 105)
        self.FrameMengeneBasinci.setStyleSheet(inner_frame_style)

        self.labelMengeneBasinci = QLabel("Mengene Basıncı (bar)", self.FrameMengeneBasinci)
        self.labelMengeneBasinci.setGeometry(33, 20, 211, 20)
        self.labelMengeneBasinci.setStyleSheet(label_name_style)

        self.labelMengeneBasinciValue = QLabel("—", self.FrameMengeneBasinci)
        self.labelMengeneBasinciValue.setGeometry(30, 43, 211, 50)
        self.labelMengeneBasinciValue.setStyleSheet(label_value_style)
        self.labelMengeneBasinciValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameOrtamSicakligi (300, 281, 260, 105) ---
        self.FrameOrtamSicakligi = QFrame(self.Container_4)
        self.FrameOrtamSicakligi.setGeometry(300, 281, 260, 105)
        self.FrameOrtamSicakligi.setStyleSheet(inner_frame_style)

        self.labelOrtamSicakligi = QLabel("Ortam Sıcaklığı (°C)", self.FrameOrtamSicakligi)
        self.labelOrtamSicakligi.setGeometry(33, 20, 211, 20)
        self.labelOrtamSicakligi.setStyleSheet(label_name_style)

        self.labelOrtamSicakligiValue = QLabel("—", self.FrameOrtamSicakligi)
        self.labelOrtamSicakligiValue.setGeometry(30, 43, 211, 50)
        self.labelOrtamSicakligiValue.setStyleSheet(label_value_style)
        self.labelOrtamSicakligiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameOrtamNem (580, 281, 260, 105) ---
        self.FrameOrtamNem = QFrame(self.Container_4)
        self.FrameOrtamNem.setGeometry(580, 281, 260, 105)
        self.FrameOrtamNem.setStyleSheet(inner_frame_style)

        self.labelOrtamNem = QLabel("Ortam Nem (%)", self.FrameOrtamNem)
        self.labelOrtamNem.setGeometry(33, 20, 201, 20)
        self.labelOrtamNem.setStyleSheet(label_name_style)

        self.labelOrtamNemValue = QLabel("—", self.FrameOrtamNem)
        self.labelOrtamNemValue.setGeometry(30, 43, 211, 50)
        self.labelOrtamNemValue.setStyleSheet(label_value_style)
        self.labelOrtamNemValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ============================================================
        # CONTAINER 5: Durum Bilgileri (Sağ Alt)
        # Eski: (1033, 851, 857, 159) -> Yeni: (641, 851, 857, 159)
        # ============================================================
        self.Container_5 = QFrame(self)
        self.Container_5.setGeometry(641, 851, 857, 159)
        self.Container_5.setStyleSheet(frame_style)

        # --- FrameKesilenParcaAdeti (20, 27, 260, 105) ---
        self.FrameKesilenParcaAdeti = QFrame(self.Container_5)
        self.FrameKesilenParcaAdeti.setGeometry(20, 27, 260, 105)
        self.FrameKesilenParcaAdeti.setStyleSheet(inner_frame_style)

        self.labelKesilenParcaAdeti = QLabel("Kesilen Parça Adeti", self.FrameKesilenParcaAdeti)
        self.labelKesilenParcaAdeti.setGeometry(33, 20, 211, 31)
        self.labelKesilenParcaAdeti.setStyleSheet(label_name_style)

        self.labelKesilenParcaAdetiValue = QLabel("—", self.FrameKesilenParcaAdeti)
        self.labelKesilenParcaAdetiValue.setGeometry(30, 43, 211, 50)
        self.labelKesilenParcaAdetiValue.setStyleSheet(label_value_style)
        self.labelKesilenParcaAdetiValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameTestereDurum (300, 27, 260, 105) ---
        self.FrameTestereDurum = QFrame(self.Container_5)
        self.FrameTestereDurum.setGeometry(300, 27, 260, 105)
        self.FrameTestereDurum.setStyleSheet(inner_frame_style)

        self.labelTestereDurum = QLabel("Testere Durumu", self.FrameTestereDurum)
        self.labelTestereDurum.setGeometry(33, 20, 201, 20)
        self.labelTestereDurum.setStyleSheet(label_name_style)

        self.labelTestereDurumValue = QLabel("—", self.FrameTestereDurum)
        self.labelTestereDurumValue.setGeometry(10, 43, 240, 50)
        self.labelTestereDurumValue.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 24px;
            }
        """)
        self.labelTestereDurumValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- FrameAlarm (580, 27, 260, 105) ---
        self.FrameAlarm = QFrame(self.Container_5)
        self.FrameAlarm.setGeometry(580, 27, 260, 105)
        self.FrameAlarm.setStyleSheet(inner_frame_style)

        self.labelAlarmStatus = QLabel("Alarm Durumu", self.FrameAlarm)
        self.labelAlarmStatus.setGeometry(33, 20, 211, 20)
        self.labelAlarmStatus.setStyleSheet(label_name_style)

        self.labelAlarmStatusValue = QLabel("—", self.FrameAlarm)
        self.labelAlarmStatusValue.setGeometry(30, 43, 211, 50)
        self.labelAlarmStatusValue.setStyleSheet(label_value_style)
        self.labelAlarmStatusValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Legacy aliases for backwards compatibility with _update_ui_labels
        self.machineInfoFrame = self.Container
        self.sensorData1Frame = self.Container_4
        self.statusMotorFrame = self.Container_5
        self.labelMaxBandDeviationValue = self.labelSeritSapmasiValue  # Re-use same label

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
                # get_data_callback is data_pipeline object
                # Get latest sensor data for display
                if hasattr(self.get_data_callback, 'get_latest_data'):
                    data = self.get_data_callback.get_latest_data()
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
                self.current_values['a_mm'] = processed_data.get('malzeme_a_mm', '—')
                self.current_values['b_mm'] = processed_data.get('malzeme_b_mm', '—')
                self.current_values['c_mm'] = processed_data.get('malzeme_c_mm', '—')
                self.current_values['d_mm'] = processed_data.get('malzeme_d_mm', '—')

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
                        -1: "BAĞLANTI BEKLENİYOR",  # Special value when Modbus not connected
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

                # Power measurement (5 decimal places for precision)
                guc_kwh = processed_data.get('guc_kwh', None)
                if guc_kwh is not None and guc_kwh != '':
                    try:
                        self.current_values['guc_kwh'] = f"{float(guc_kwh):.5f}"
                    except (ValueError, TypeError):
                        self.current_values['guc_kwh'] = '—'
                else:
                    self.current_values['guc_kwh'] = '—'

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

            # Power measurement
            self.labelGucKwhValue.setText(format_value(self.current_values.get('guc_kwh')))

        except Exception as e:
            logger.error(f"UI labels update error: {e}")

    def stop_timers(self):
        """
        Stop all QTimers in this controller.

        IMPORTANT: Must be called from the GUI thread before window closes
        to avoid segmentation fault on Linux.
        """
        try:
            if hasattr(self, '_data_timer') and self._data_timer:
                self._data_timer.stop()
            logger.debug("MonitoringController timers stopped")
        except Exception as e:
            logger.error(f"Error stopping monitoring controller timers: {e}")
