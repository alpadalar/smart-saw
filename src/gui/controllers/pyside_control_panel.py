from typing import Callable, Dict, Optional
from PySide6.QtCore import QTimer, Qt, QDateTime
from PySide6.QtWidgets import QMainWindow, QTextEdit, QWidget, QVBoxLayout
from PySide6.QtGui import QIcon, QTextCursor, QPainter, QPen, QColor, QBrush
import os
from datetime import datetime, timedelta
import threading
import queue
import logging
import collections

from gui.ui_files.control_panel_window_ui import Ui_MainWindow
from hardware.machine_control import MachineControl
# Logger
logger = logging.getLogger(__name__)
# Import'ları geçici olarak comment'e alıyorum
# from src.control.factory import ControllerType
# from src.core.constants import TestereState
# from src.hardware.modbus.writer import reverse_calculate_value
# from src.gui.numpad import NumpadDialog

# Geçici olarak enum değerlerini tanımlıyorum
class ControllerType:
    FUZZY = type('FUZZY', (), {'value': 'FUZZY'})()
    EXPERT = type('EXPERT', (), {'value': 'EXPERT'})()
    ML = type('ML', (), {'value': 'ML'})()

class TestereState:
    BOSTA = type('BOSTA', (), {'value': 0})()
    HIDROLIK_AKTIF = type('HIDROLIK_AKTIF', (), {'value': 1})()
    SERIT_MOTOR_CALISIYOR = type('SERIT_MOTOR_CALISIYOR', (), {'value': 2})()
    KESIM_YAPILIYOR = type('KESIM_YAPILIYOR', (), {'value': 3})()
    KESIM_BITTI = type('KESIM_BITTI', (), {'value': 4})()
    SERIT_YUKARI_CIKIYOR = type('SERIT_YUKARI_CIKIYOR', (), {'value': 5})()
    MALZEME_BESLEME = type('MALZEME_BESLEME', (), {'value': 6})()

# Geçici olarak fonksiyonları tanımlıyorum
def reverse_calculate_value(client, value, param, reverse=False):
    logger.info(f"reverse_calculate_value çağrıldı: {value}, {param}, {reverse}")
    return True

# NumpadDialog'u import et
try:
    # Absolute import deneyelim
    from src.gui.numpad import NumpadDialog
except ImportError:
    try:
        # Relative import deneyelim
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from numpad import NumpadDialog
    except ImportError:
        try:
            # Current directory'den deneyelim
            from numpad import NumpadDialog
        except ImportError as e:
            logger.error(f"NumpadDialog import hatası: {e}")
            # Gerçek dialog sınıfı oluşturalım
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
            
            class NumpadDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Sayı Girişi")
                    self.setModal(True)
                    self.setFixedSize(400, 300)
                    self.value = ""
                    self.Accepted = QDialog.Accepted
                    self.setup_ui()
                    self.center_on_screen()
                
                def setup_ui(self):
                    layout = QVBoxLayout(self)
                    
                    # Display label
                    self.display_label = QLabel("0")
                    self.display_label.setStyleSheet("font-size: 24px; padding: 10px; border: 1px solid gray;")
                    self.display_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(self.display_label)
                    
                    # Number buttons
                    for row in range(3):
                        row_layout = QHBoxLayout()
                        for col in range(3):
                            number = row * 3 + col + 1
                            btn = QPushButton(str(number))
                            btn.setFixedSize(80, 60)
                            btn.clicked.connect(lambda checked, n=number: self.add_digit(str(n)))
                            row_layout.addWidget(btn)
                        layout.addLayout(row_layout)
                    
                    # Bottom row
                    bottom_layout = QHBoxLayout()
                    
                    # Clear button
                    clear_btn = QPushButton("Temizle")
                    clear_btn.setFixedSize(80, 60)
                    clear_btn.clicked.connect(self.clear_value)
                    bottom_layout.addWidget(clear_btn)
                    
                    # Zero button
                    zero_btn = QPushButton("0")
                    zero_btn.setFixedSize(80, 60)
                    zero_btn.clicked.connect(lambda: self.add_digit("0"))
                    bottom_layout.addWidget(zero_btn)
                    
                    # OK button
                    ok_btn = QPushButton("Tamam")
                    ok_btn.setFixedSize(80, 60)
                    ok_btn.clicked.connect(self.accept)
                    bottom_layout.addWidget(ok_btn)
                    
                    layout.addLayout(bottom_layout)
                
                def add_digit(self, digit):
                    if len(self.value) < 10:
                        self.value += digit
                        self.update_label()
                
                def clear_value(self):
                    self.value = ""
                    self.update_label()
                
                def update_label(self):
                    self.display_label.setText(self.value if self.value else "0")
                
                def get_value(self):
                    return self.value
                
                def center_on_screen(self):
                    screen = self.screen()
                    screen_geometry = screen.geometry()
                    dialog_geometry = self.geometry()
                    x = (screen_geometry.width() - dialog_geometry.width()) // 2
                    y = (screen_geometry.height() - dialog_geometry.height()) // 2
                    self.move(x, y)

# Global değişkenler
last_meaningful_speed = None



class BandDeviationGraphWidget(QWidget):
    """Şerit sapması değerlerini gösteren gerçek zamanlı grafik widget'ı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(278, 144)
        
        # Veri yapısı: (timestamp, value) tuple'ları
        self.data_points = collections.deque(maxlen=300)  # 30 saniye * 10 veri/saniye
        self.max_points = 300
        
        # Maksimum ve minimum değer takibi
        self.max_value = float('-inf')
        self.min_value = float('inf')
        
        # Grafik ayarları
        self.padding = 10
        self.grid_color = QColor(255, 255, 255, 30)  # Şeffaf beyaz
        self.line_color = QColor(149, 9, 82)  # Ana renk
        self.fill_color = QColor(149, 9, 82, 50)  # Dolgu rengi
        
        # Thread-safe veri erişimi için lock
        self._data_lock = threading.Lock()
        
        # Timer ile güncelleme
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)  # 20 FPS - daha akıcı görünüm
        
        # Widget stil ayarları
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
    def add_data_point(self, value: float):
        """Yeni veri noktası ekler (thread-safe)"""
        try:
            with self._data_lock:
                timestamp = datetime.now()
                self.data_points.append((timestamp, value))
                
                # Maksimum ve minimum değerleri güncelle
                if value > self.max_value:
                    self.max_value = value
                if value < self.min_value:
                    self.min_value = value
        except Exception as e:
            logger.error(f"Veri noktası ekleme hatası: {e}")
    
    def clear_old_data(self):
        """30 saniyeden eski verileri temizler"""
        try:
            with self._data_lock:
                cutoff_time = datetime.now() - timedelta(seconds=30)
                while self.data_points and self.data_points[0][0] < cutoff_time:
                    self.data_points.popleft()
        except Exception as e:
            logger.error(f"Eski veri temizleme hatası: {e}")
    
    def get_max_value(self) -> float:
        """Maksimum pozitif değeri döndürür"""
        try:
            with self._data_lock:
                if self.max_value == float('-inf'):
                    return 0.0
                return max(0.0, self.max_value)  # Sadece pozitif değerleri döndür
        except Exception as e:
            logger.error(f"Maksimum değer alma hatası: {e}")
            return 0.0
    
    def get_min_value(self) -> float:
        """Minimum değeri döndürür (pozitif veya negatif olabilir)"""
        try:
            with self._data_lock:
                if self.min_value == float('inf'):
                    return 0.0
                return self.min_value
        except Exception as e:
            logger.error(f"Minimum değer alma hatası: {e}")
            return 0.0
    
    def paintEvent(self, event):
        """Grafiği çizer"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Arkaplan şeffaf
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            
            # Veri yoksa çizim yapma
            if not self.data_points:
                return
            
            # Çizim alanını hesapla
            draw_rect = self.rect().adjusted(self.padding, self.padding, -self.padding, -self.padding)
            
            # Grid çiz
            self._draw_grid(painter, draw_rect)
            
            # Veri çiz
            self._draw_data(painter, draw_rect)
            
        except Exception as e:
            logger.error(f"Grafik çizim hatası: {e}")
    
    def _draw_grid(self, painter: QPainter, rect):
        """Grid çizer"""
        try:
            painter.setPen(QPen(self.grid_color, 1))
            
            # Dikey çizgiler (16 adet)
            for i in range(17):
                x = rect.left() + (rect.width() * i) // 16
                painter.drawLine(x, rect.top(), x, rect.bottom())
            
            # Yatay çizgiler (4 adet)
            for i in range(5):
                y = rect.top() + (rect.height() * i) // 4
                painter.drawLine(rect.left(), y, rect.right(), y)
                
        except Exception as e:
            logger.error(f"Grid çizim hatası: {e}")
    
    def _draw_data(self, painter: QPainter, rect):
        """Veri çizer"""
        try:
            with self._data_lock:
                if len(self.data_points) < 2:
                    return
                
                # Değer aralığını hesapla
                values = [point[1] for point in self.data_points]
                min_val = min(values)
                max_val = max(values)
                
                # Aralık çok küçükse genişlet
                if max_val - min_val < 0.1:
                    mid_val = (min_val + max_val) / 2
                    min_val = mid_val - 0.05
                    max_val = mid_val + 0.05
                
                # Çizgi rengi
                painter.setPen(QPen(self.line_color, 3))
                
                # Dolgu rengi
                painter.setBrush(QBrush(self.fill_color))
                
                # Çizgi noktalarını hesapla
                points = []
                for i, (timestamp, value) in enumerate(self.data_points):
                    # X koordinatı (zaman)
                    x = rect.left() + (rect.width() * i) // (len(self.data_points) - 1)
                    
                    # Y koordinatı (değer)
                    if max_val != min_val:
                        normalized_value = (value - min_val) / (max_val - min_val)
                    else:
                        normalized_value = 0.5
                    
                    y = rect.bottom() - (rect.height() * normalized_value)
                    points.append((x, y))
                
                # Çizgi çiz
                if len(points) > 1:
                    # Ana çizgi
                    for i in range(len(points) - 1):
                        painter.drawLine(int(points[i][0]), int(points[i][1]), 
                                       int(points[i+1][0]), int(points[i+1][1]))
                    
                    # Dolgu alanı
                    fill_points = points.copy()
                    fill_points.append((points[-1][0], rect.bottom()))
                    fill_points.append((points[0][0], rect.bottom()))
                    
                    from PySide6.QtGui import QPolygon
                    polygon = QPolygon()
                    for x, y in fill_points:
                        polygon.append(int(x), int(y))
                    
                    painter.drawPolygon(polygon)
                
                # Son nokta için kırmızı üçgen
                if points:
                    last_x, last_y = points[-1]
                    triangle_size = 8
                    painter.setBrush(QBrush(QColor(255, 0, 0)))
                    painter.setPen(QPen(QColor(255, 0, 0), 1))
                    
                    triangle_points = [
                        (last_x, last_y - triangle_size),
                        (last_x - triangle_size//2, last_y + triangle_size//2),
                        (last_x + triangle_size//2, last_y + triangle_size//2)
                    ]
                    
                    triangle_polygon = QPolygon()
                    for x, y in triangle_points:
                        triangle_polygon.append(int(x), int(y))
                    
                    painter.drawPolygon(triangle_polygon)
                    
        except Exception as e:
            logger.error(f"Veri çizim hatası: {e}")
    
    def resizeEvent(self, event):
        """Widget boyutu değiştiğinde"""
        super().resizeEvent(event)
        self.update()


class ControlPanelWindow(QMainWindow):
    """PySide6 Control Panel main window (QMainWindow).
    - Hosts the sidebar
    - Opens other pages (widgets) fullscreen
    - Keeps optional get_data_callback to feed pages
    """

    def __init__(
        self,
        controller_factory: Optional[object] = None,
        get_data_callback: Optional[Callable[[], Dict]] = None,
    ) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Optional external dependencies
        self.controller_factory = controller_factory
        self.get_data_callback = get_data_callback

        # Machine control instance (for coolant, etc.)
        try:
            self.machine_control = MachineControl()
        except Exception as e:
            self.machine_control = None
            logger.error(f"MachineControl başlatılamadı: {e}")

        # Page instances (created on demand)
        self._monitoring_page = None
        self._camera_page = None
        self._sensor_page = None
        self._positioning_page = None

        # Şerit sapması grafik widget'ı
        self.band_deviation_graph = None

        # Veri yönetimi için gerekli değişkenler
        self.current_values = {}
        self._last_update_time = None
        self.kesim_baslama_zamani = None
        self._cutting_start_time = None
        
        # Hız değerleri
        self.speed_values = {
            "slow": {"cutting": 15.0, "descent": 8.0},
            "normal": {"cutting": 25.0, "descent": 12.0},
            "fast": {"cutting": 35.0, "descent": 18.0}
        }
        
        # Log kuyruğu (thread-safe)
        self.log_queue = queue.Queue()
        
        # Hız güncelleme flag'i
        self._force_update_cutting_speed = False
        
        # Frame tıklama kontrolü için flag
        self._frame_click_enabled = True
        
        # Başlangıç değerlerini ayarla
        self._initialize_current_values()
        
        # Başlangıçta bağlantı yok olarak ayarla
        self.current_values['testere_durumu'] = 'Bağlantı Yok'
        
        # Replace sidebar icons from images/ folder
        self._apply_local_icons()

        # Connections
        self._connect_navigation()

        # Timers (date/time)
        self._datetime_timer = QTimer(self)
        self._datetime_timer.timeout.connect(self._update_datetime_labels)
        self._datetime_timer.start(1000)
        self._update_datetime_labels()
        
        # Log işleme timer'ı
        self._log_timer = QTimer(self)
        self._log_timer.timeout.connect(self._process_logs)
        self._log_timer.start(100)  # 100ms
        
        # Data güncelleme timer'ı - sadece control panel aktifken çalışsın
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self._on_data_tick)
        # Timer'ı başlangıçta başlat
        self._data_timer.start(200)  # 200ms

        # GUI'yi başlat
        self.setup_gui()
        
        # Control panel'i aktif olarak ayarla
        self.set_active_nav("btnControlPanel")
        
        # Start fullscreen by default as requested
        self.showFullScreen()

    def set_active_nav(self, active_btn_name: str):
        """Navigation butonlarının aktif/pasif durumunu ayarla"""
        try:
            # Aktif ve pasif icon'ları tanımla
            nav_buttons = {
                'btnControlPanel': ('control-panel-icon2.svg', 'control-panel-icon2-active.svg'),
                'btnPositioning': ('positioning-icon2.svg', 'positioning-icon2-active.svg'),
                'btnCamera': ('camera-icon2.svg', 'camera-icon-active.svg'),
                'btnSensor': ('sensor-icon2.svg', 'sensor-icon2-active.svg'),
                'btnTracking': ('tracking-icon2.svg', 'tracking-icon2-active.svg'),
            }
            
            for btn_name, (passive_icon, active_icon) in nav_buttons.items():
                btn = getattr(self.ui, btn_name, None)
                if btn:
                    if btn_name == active_btn_name:
                        btn.setIcon(self._icon(active_icon))
                    else:
                        btn.setIcon(self._icon(passive_icon))
        except Exception as e:
            logger.error(f"Navigation aktif durum ayarlama hatası: {e}")

    def _on_data_tick(self):
        """Data timer'ından çağrılan metod"""
        try:
            if self.get_data_callback:
                data = self.get_data_callback()
                if data:
                    self.update_data(data)
        except Exception as e:
            logger.error(f"Data tick hatası: {e}")

    def _initialize_current_values(self):
        """Başlangıç değerlerini ayarlar"""
        self.current_values = {
            'makine_id': '-',
            'serit_id': '-',
            'serit_dis_mm': '-',
            'serit_tip': '-',
            'serit_marka': '-',
            'serit_malz': '-',
            'malzeme_cinsi': '-',
            'malzeme_sertlik': '-',
            'kesit_yapisi': '-',
            'a_mm': '-',
            'b_mm': '-',
            'c_mm': '-',
            'd_mm': '-',
            'kafa_yuksekligi_mm': '0.0',
            'serit_motor_akim_a': '0.0',
            'serit_motor_tork_percentage': '0.0',
            'inme_motor_akim_a': '0.0',
            'inme_motor_tork_percentage': '0.0',
            'mengene_basinc_bar': '0.0',
            'serit_gerginligi_bar': '0.0',
            'serit_sapmasi': '0.00 ',
            'ortam_sicakligi_c': '0.0',
            'ortam_nem_percentage': '0.0',
            'sogutma_sivi_sicakligi_c': '0.0',
            'hidrolik_yag_sicakligi_c': '0.0',
            'ivme_olcer_x': '0.000',
            'ivme_olcer_y': '0.000',
            'ivme_olcer_z': '0.000',
            'ivme_olcer_x_hz': '0.0',
            'ivme_olcer_y_hz': '0.0',
            'ivme_olcer_z_hz': '0.0',
            'serit_kesme_hizi': '0.0',
            'serit_inme_hizi': '0.0',
            'kesilen_parca_adeti': '0',
            'testere_durumu': 'Bağlantı Yok',
            'alarm_status': '-',
            'alarm_bilgisi': '-',
            'kesim_baslama': '-',
            'kesim_sure': '-',
            'modbus_status': 'Bağlantı Yok'
        }

    def setup_gui(self):
        """GUI bileşenlerini başlatır"""
        try:
            # Pencere başlığı
            self.setWindowTitle("Akıllı Testere Kontrol Paneli")
            
            # Kesim modu butonları
            self.ui.btnManualMode.clicked.connect(lambda: self._handle_cutting_mode_buttons(self.ui.btnManualMode))
            self.ui.btnFuzzyMode.clicked.connect(lambda: self._handle_cutting_mode_buttons(self.ui.btnFuzzyMode))
            self.ui.btnExpertSystemMode.clicked.connect(lambda: self._handle_cutting_mode_buttons(self.ui.btnExpertSystemMode))
            self.ui.btnAiMode.clicked.connect(lambda: self._handle_cutting_mode_buttons(self.ui.btnAiMode))
            
            # Kesim hızı butonları
            self.ui.btnSlowSpeed.clicked.connect(lambda: self._handle_speed_buttons(self.ui.btnSlowSpeed))
            self.ui.btnNormalSpeed.clicked.connect(lambda: self._handle_speed_buttons(self.ui.btnNormalSpeed))
            self.ui.btnFastSpeed.clicked.connect(lambda: self._handle_speed_buttons(self.ui.btnFastSpeed))
            
            # Log widget'ı - eğer logViewerScroll varsa
            if hasattr(self.ui, 'logViewerScroll') and self.ui.logViewerScroll.widget():
                self.ui.log_text = QTextEdit()
                try:
                    self.ui.logViewerScroll.widget().layout().addWidget(self.ui.log_text)
                    self.ui.log_text.setReadOnly(True)
                    # Log text arkaplanını şeffaf yap
                    self.ui.log_text.setStyleSheet("background-color: transparent;")
                except Exception as e:
                    logger.warning(f"Log widget kurulum hatası: {e}")
                    self.ui.log_text = None
            else:
                self.ui.log_text = None
            
            # Başlangıç değerlerini ayarla
            if hasattr(self.ui, 'labelBandCuttingSpeedValue'):
                self.ui.labelBandCuttingSpeedValue.setText("0.0")
            if hasattr(self.ui, 'labelBandDescentSpeedValue'):
                self.ui.labelBandDescentSpeedValue.setText("0.0")
            if hasattr(self.ui, 'labelBandDeviationValue'):
                self.ui.labelBandDeviationValue.setText("0.00")
            if hasattr(self.ui, 'ustdegerlabel'):
                self.ui.ustdegerlabel.setText(" 0.00")
            if hasattr(self.ui, 'altdegerlabel'):
                self.ui.altdegerlabel.setText(" 0.00")
            

            
            # Sistem durumu etiketi başlangıç metni
            if hasattr(self.ui, 'labelSystemStatusInfo'):
                self.ui.labelSystemStatusInfo.setText("Bağlantı Kontrol Ediliyor...")
            
            # Frame'leri tıklanabilir yap - eğer varsa
            if hasattr(self.ui, 'bandCuttingSpeedFrame'):
                # Frame'i tıklanabilir yap
                self.ui.bandCuttingSpeedFrame.setCursor(Qt.PointingHandCursor)
                # Frame'e doğrudan mousePressEvent ekle
                self.ui.bandCuttingSpeedFrame.mousePressEvent = self._handle_cutting_speed_frame_click
                
            if hasattr(self.ui, 'bandDescentSpeedFrame'):
                # Frame'i tıklanabilir yap
                self.ui.bandDescentSpeedFrame.setCursor(Qt.PointingHandCursor)
                # Frame'e doğrudan mousePressEvent ekle
                self.ui.bandDescentSpeedFrame.mousePressEvent = self._handle_descent_speed_frame_click
            
            # Şerit sapması grafik widget'ını oluştur
            if hasattr(self.ui, 'bandDeviationGraphFrame'):
                self.band_deviation_graph = BandDeviationGraphWidget(self.ui.bandDeviationGraphFrame)
                self.band_deviation_graph.setGeometry(0, 0, 278, 144)
                self.band_deviation_graph.show()
            
            # Başlangıç değerlerini ayarla
            self.update_ui()

            # Coolant button wiring
            if hasattr(self.ui, 'toolBtnCoolant'):
                try:
                    # Toggled handler: gerçek checked durumunu verir
                    self.ui.toolBtnCoolant.toggled.connect(self._on_coolant_toggled)
                    # Initialize coolant button state from machine
                    QTimer.singleShot(0, self._refresh_coolant_state)
                except Exception as e:
                    logger.error(f"Soğutma düğmesi bağlantı hatası: {e}")

            # Sawdust cleaning button wiring
            if hasattr(self.ui, 'toolBtnSawdustCleaning'):
                try:
                    self.ui.toolBtnSawdustCleaning.toggled.connect(self._on_chip_cleaning_toggled)
                    QTimer.singleShot(0, self._refresh_chip_cleaning_state)
                except Exception as e:
                    logger.error(f"Talaş temizlik düğmesi bağlantı hatası: {e}")
            
        except Exception as e:
            logger.error(f"GUI başlatma hatası: {e}")
            logger.exception("Detaylı hata:")

    def _refresh_coolant_state(self):
        """Makineden soğutma durumunu okuyup butonu senkronize eder."""
        try:
            if not hasattr(self.ui, 'toolBtnCoolant'):
                return
            if not self.machine_control:
                logger.error("MachineControl mevcut değil")
                return
            status = self.machine_control.is_coolant_active()
            if status is None:
                logger.error("Soğutma durumu okunamadı")
                return
            self.ui.toolBtnCoolant.blockSignals(True)
            self.ui.toolBtnCoolant.setChecked(bool(status))
            self.ui.toolBtnCoolant.blockSignals(False)
        except Exception as e:
            logger.error(f"Soğutma durumu senkronizasyon hatası: {e}")

    def _on_coolant_toggled(self, checked: bool):
        """Soğutma butonu durum değişince başlat/durdur."""
        try:
            if not self.machine_control:
                self.add_log("Soğutma kontrol edilemedi: MachineControl yok.", "ERROR")
                # Revert UI to unknown/off
                if hasattr(self.ui, 'toolBtnCoolant'):
                    self.ui.toolBtnCoolant.blockSignals(True)
                    self.ui.toolBtnCoolant.setChecked(False)
                    self.ui.toolBtnCoolant.blockSignals(False)
                return

            success = False
            if checked:
                # Enable coolant
                success = self.machine_control.start_coolant()
                if success:
                    self.add_log("Soğutma sıvısı açıldı.", "INFO")
                else:
                    self.add_log("Soğutma sıvısı AÇILAMADI!", "ERROR")
            else:
                # Disable coolant
                success = self.machine_control.stop_coolant()
                if success:
                    self.add_log("Soğutma sıvısı kapatıldı.", "INFO")
                else:
                    self.add_log("Soğutma sıvısı KAPATILAMADI!", "ERROR")

            # Eğer işlem başarısızsa UI durumunu geri al
            if not success and hasattr(self.ui, 'toolBtnCoolant'):
                self.ui.toolBtnCoolant.blockSignals(True)
                self.ui.toolBtnCoolant.setChecked(not checked)
                self.ui.toolBtnCoolant.blockSignals(False)

            # Başarılı işlemde UI mevcut durumu korusun; başarısızlıkta geri alındı

        except Exception as e:
            logger.error(f"Soğutma butonu işlem hatası: {e}")
            # Hata durumunda UI'ı güvenli duruma çek
            if hasattr(self.ui, 'toolBtnCoolant'):
                self.ui.toolBtnCoolant.blockSignals(True)
                self.ui.toolBtnCoolant.setChecked(False)
                self.ui.toolBtnCoolant.blockSignals(False)

    def _refresh_chip_cleaning_state(self):
        """Makineden talaş temizlik durumunu okuyup butonu senkronize eder."""
        try:
            if not hasattr(self.ui, 'toolBtnSawdustCleaning'):
                return
            if not self.machine_control:
                logger.error("MachineControl mevcut değil")
                return
            status = self.machine_control.is_chip_cleaning_active()
            if status is None:
                logger.error("Talaş temizlik durumu okunamadı")
                return
            self.ui.toolBtnSawdustCleaning.blockSignals(True)
            self.ui.toolBtnSawdustCleaning.setChecked(bool(status))
            self.ui.toolBtnSawdustCleaning.blockSignals(False)
        except Exception as e:
            logger.error(f"Talaş temizlik durumu senkronizasyon hatası: {e}")

    def _on_chip_cleaning_toggled(self, checked: bool):
        """Talaş temizlik butonu durum değişince başlat/durdur."""
        try:
            if not self.machine_control:
                self.add_log("Talaş temizlik kontrol edilemedi: MachineControl yok.", "ERROR")
                if hasattr(self.ui, 'toolBtnSawdustCleaning'):
                    self.ui.toolBtnSawdustCleaning.blockSignals(True)
                    self.ui.toolBtnSawdustCleaning.setChecked(False)
                    self.ui.toolBtnSawdustCleaning.blockSignals(False)
                return

            success = False
            if checked:
                success = self.machine_control.start_chip_cleaning()
                if success:
                    self.add_log("Talaş temizliği açıldı.", "INFO")
                else:
                    self.add_log("Talaş temizliği AÇILAMADI!", "ERROR")
            else:
                success = self.machine_control.stop_chip_cleaning()
                if success:
                    self.add_log("Talaş temizliği kapatıldı.", "INFO")
                else:
                    self.add_log("Talaş temizliği KAPATILAMADI!", "ERROR")

            if not success and hasattr(self.ui, 'toolBtnSawdustCleaning'):
                self.ui.toolBtnSawdustCleaning.blockSignals(True)
                self.ui.toolBtnSawdustCleaning.setChecked(not checked)
                self.ui.toolBtnSawdustCleaning.blockSignals(False)

        except Exception as e:
            logger.error(f"Talaş temizlik butonu işlem hatası: {e}")
            if hasattr(self.ui, 'toolBtnSawdustCleaning'):
                self.ui.toolBtnSawdustCleaning.blockSignals(True)
                self.ui.toolBtnSawdustCleaning.setChecked(False)
                self.ui.toolBtnSawdustCleaning.blockSignals(False)
    
    def _get_status_message(self, status_text):
        """Sistem durumuna göre özel mesaj döndürür."""
        status_messages = {
            "BOŞTA": "Boşta.",
            "HİDROLİK AKTİF": "Makine kesime\nhazır.",
            "ŞERİT MOTOR ÇALIŞIYOR": "Şerit motor\nçalışıyor!",
            "KESİM YAPILIYOR": "Kesim yapılıyor!",
            "KESİM BİTTİ": "Kesim bitti!",
            "ŞERİT YUKARI ÇIKIYOR": "Şerit yukarı\nçıkıyor.",
            "MALZEME BESLEME": "Kesilecek malzeme\nkonumlandırılıyor.",
            "BİLİNMİYOR": "Bilinmiyor!",
            "Bağlantı Yok": "Bağlantı bekleniyor...",
            "Veri bekleniyor...": "Veri akışı\nbekleniyor..."
        }
        return status_messages.get(status_text, status_text)

    def _handle_cutting_mode_buttons(self, clicked_button):
        """Kesim modu butonlarını yönetir"""
        try:
            # Tüm kesim modu butonlarını al
            mode_buttons = [
                self.ui.btnManualMode,
                self.ui.btnFuzzyMode,
                self.ui.btnExpertSystemMode,
                self.ui.btnAiMode
            ]
            
            # Tüm butonları kapat
            for button in mode_buttons:
                button.setChecked(False)
            
            # Tıklanan butonu seç
            clicked_button.setChecked(True)
            
            # Seçilen butona göre kontrol sistemini ayarla
            if clicked_button == self.ui.btnManualMode:
                self._switch_controller(None)
                self.add_log("Kesim modu manuel olarak ayarlandı", "INFO")
            elif clicked_button == self.ui.btnFuzzyMode:
                self._switch_controller("FUZZY")
                self.add_log("Kesim modu fuzzy olarak ayarlandı", "INFO")
            elif clicked_button == self.ui.btnExpertSystemMode:
                self._switch_controller("EXPERT")
                self.add_log("Kesim modu expert system olarak ayarlandı", "INFO")
            elif clicked_button == self.ui.btnAiMode:
                self._switch_controller("ML")
                self.add_log("Kesim modu AI olarak ayarlandı", "INFO")
                
            # Sistem durumu etiketi
            if hasattr(self.ui, 'labelSystemStatusInfo'):
                self.ui.labelSystemStatusInfo.setText(self._get_status_message(self.current_values['testere_durumu']))
            
        except Exception as e:
            logger.error(f"Kesim modu buton yönetimi hatası: {e}")
            self.add_log(f"Kesim modu değiştirme hatası: {str(e)}", "ERROR")

    def _handle_speed_buttons(self, clicked_button):
        """Kesim hızı butonlarını yönetir"""
        try:
            # Tüm hız butonlarını al
            speed_buttons = [
                self.ui.btnSlowSpeed,
                self.ui.btnNormalSpeed,
                self.ui.btnFastSpeed
            ]
            # Tüm butonları kapat
            for button in speed_buttons:
                button.setChecked(False)
            # Tıklanan butonu seç
            clicked_button.setChecked(True)
            # Seçilen butona göre hızı ayarla
            if clicked_button.isChecked():
                speeds = None
                if clicked_button == self.ui.btnSlowSpeed:
                    self._send_manual_speed("slow")
                    speeds = self.speed_values["slow"]
                elif clicked_button == self.ui.btnNormalSpeed:
                    self._send_manual_speed("normal")
                    speeds = self.speed_values["normal"]
                elif clicked_button == self.ui.btnFastSpeed:
                    self._send_manual_speed("fast")
                    speeds = self.speed_values["fast"]
                # Hız butonuna basıldığında flag'i ayarla
                self._force_update_cutting_speed = True
                # Frame tıklamalarını geçici olarak devre dışı bırak
                self._frame_click_enabled = False
                QTimer.singleShot(2000, lambda: setattr(self, '_frame_click_enabled', True))
                # Label'ları doğrudan gönderilen hız değerleriyle güncelle
                if speeds is not None:
                    if hasattr(self.ui, 'labelBandCuttingSpeedValue'):
                        self.ui.labelBandCuttingSpeedValue.setText(f"{speeds['cutting']:.1f}")
                    if hasattr(self.ui, 'labelBandDescentSpeedValue'):
                        self.ui.labelBandDescentSpeedValue.setText(f"{speeds['descent']:.1f}")
        except Exception as e:
            logger.error(f"Kesim hızı buton yönetimi hatası: {e}")
            self.add_log(f"Kesim hızı değiştirme hatası: {str(e)}", "ERROR")

    def _switch_controller(self, controller_type: Optional[str]):
        """Kontrol sistemini değiştirir"""
        try:
            if controller_type is None:
                self.controller_factory.set_controller(None)
            else:
                self.controller_factory.set_controller(controller_type)
        except Exception as e:
            logger.error(f"Kontrol sistemi değiştirme hatası: {e}")
            logger.exception("Detaylı hata:")

    def _process_logs(self):
        """Log kuyruğunu işler"""
        try:
            while not self.log_queue.empty():
                log_entry = self.log_queue.get_nowait()
                self.add_log(log_entry['message'], log_entry['level'])
        except Exception as e:
            logger.error(f"Log işleme hatası: {e}")

    def _update_values(self, processed_data: Dict):
        """Gösterilen değerleri günceller"""
        global last_meaningful_speed
        ui_speed = None
        try:
            # Temel bilgiler
            self.current_values['makine_id'] = str(processed_data.get('makine_id', '-'))
            self.current_values['serit_id'] = str(processed_data.get('serit_id', '-'))
            self.current_values['serit_dis_mm'] = str(processed_data.get('serit_dis_mm', '-'))
            self.current_values['serit_tip'] = str(processed_data.get('serit_tip', '-'))
            self.current_values['serit_marka'] = str(processed_data.get('serit_marka', '-'))
            self.current_values['serit_malz'] = str(processed_data.get('serit_malz', '-'))
            
            # # Malzeme bilgileri
            self.current_values['malzeme_cinsi'] = str(processed_data.get('malzeme_cinsi', '-'))
            self.current_values['malzeme_sertlik'] = str(processed_data.get('malzeme_sertlik', '-'))
            self.current_values['kesit_yapisi'] = str(processed_data.get('kesit_yapisi', '-'))
            self.current_values['a_mm'] = str(processed_data.get('a_mm', '-'))
            self.current_values['b_mm'] = str(processed_data.get('b_mm', '-'))
            self.current_values['c_mm'] = str(processed_data.get('c_mm', '-'))
            self.current_values['d_mm'] = str(processed_data.get('d_mm', '-'))
            
            # Motor ve hareket bilgileri
            kafa_yuksekligi = processed_data.get('kafa_yuksekligi_mm', 0)
            self.current_values['kafa_yuksekligi_mm'] = f"{kafa_yuksekligi:.1f} "
            
            # Kafa yüksekliği değerini UI'da güncelle
            if hasattr(self.ui, 'labelValue'):
                self.ui.labelValue.setText(f"{kafa_yuksekligi:.1f}")
            if hasattr(self.ui, 'progressBarHeight'):
                try:
                    self.ui.progressBarHeight.setValue(int(kafa_yuksekligi))
                except (ValueError, TypeError):
                    self.ui.progressBarHeight.setValue(0)
            serit_motor_akim = processed_data.get('serit_motor_akim_a', 0)
            inme_motor_akim = processed_data.get('inme_motor_akim_a', 0)
            self.current_values['serit_motor_akim_a'] = f"{serit_motor_akim:.1f} "
            self.current_values['serit_motor_tork_percentage'] = f"{processed_data.get('serit_motor_tork_percentage', 0):.1f} "
            self.current_values['inme_motor_akim_a'] = f"{inme_motor_akim:.1f} "
            self.current_values['inme_motor_tork_percentage'] = f"{processed_data.get('inme_motor_tork_percentage', 0):.1f} "
            
            # Motor akım değerlerini UI'da güncelle
            if hasattr(self.ui, 'labelBandCuttingCurrentValue'):
                self.ui.labelBandCuttingCurrentValue.setText(f"{serit_motor_akim:.1f}")
            if hasattr(self.ui, 'labelBandDescentCurrentValue'):
                self.ui.labelBandDescentCurrentValue.setText(f"{inme_motor_akim:.1f}")
            
            # Motor tork değerlerini UI'da güncelle
            serit_motor_tork = processed_data.get('serit_motor_tork_percentage', 0)
            inme_motor_tork = processed_data.get('inme_motor_tork_percentage', 0)
            if hasattr(self.ui, 'labelBandCuttingTorqueValue'):
                self.ui.labelBandCuttingTorqueValue.setText(f"{serit_motor_tork:.1f}")
            if hasattr(self.ui, 'labelBandDescentTorqueValue'):
                self.ui.labelBandDescentTorqueValue.setText(f"{inme_motor_tork:.1f}")
            
            # Basınç ve sıcaklık bilgileri
            self.current_values['mengene_basinc_bar'] = f"{processed_data.get('mengene_basinc_bar', 0):.1f} "
            self.current_values['serit_gerginligi_bar'] = f"{processed_data.get('serit_gerginligi_bar', 0):.1f} "
            
            # Şerit sapması grafiğine veri ekle
            if self.band_deviation_graph:
                try:
                    deviation_value = float(processed_data.get('serit_sapmasi', 0))
                    self.band_deviation_graph.add_data_point(deviation_value)
                    # Eski verileri temizle
                    self.band_deviation_graph.clear_old_data()
                    
                    # Maksimum ve minimum değerleri güncelle
                    max_value = self.band_deviation_graph.get_max_value()
                    min_value = self.band_deviation_graph.get_min_value()
                    
                    if hasattr(self.ui, 'ustdegerlabel'):
                        self.ui.ustdegerlabel.setText(f" {max_value:.2f}")
                    if hasattr(self.ui, 'altdegerlabel'):
                        if min_value >= 0:
                            self.ui.altdegerlabel.setText(f" {min_value:.2f}")
                        else:
                            self.ui.altdegerlabel.setText(f"{min_value:.2f}")
                        
                except Exception as e:
                    logger.error(f"Grafik veri ekleme hatası: {e}")
            
            # Şerit sapması değerini UI'da güncelle
            if hasattr(self.ui, 'labelBandDeviationValue'):
                deviation_value = processed_data.get('serit_sapmasi', 0)
                self.ui.labelBandDeviationValue.setText(f"{deviation_value:.2f}")
                # current_values'ı da güncelle
                self.current_values['serit_sapmasi'] = f"{deviation_value:.2f} "
            
            self.current_values['ortam_sicakligi_c'] = f"{processed_data.get('ortam_sicakligi_c', 0):.1f} "
            self.current_values['ortam_nem_percentage'] = f"{processed_data.get('ortam_nem_percentage', 0):.1f} "
            self.current_values['sogutma_sivi_sicakligi_c'] = f"{processed_data.get('sogutma_sivi_sicakligi_c', 0):.1f} "
            self.current_values['hidrolik_yag_sicakligi_c'] = f"{processed_data.get('hidrolik_yag_sicakligi_c', 0):.1f} "
            
            # İvme ölçer bilgileri
            self.current_values['ivme_olcer_x'] = f"{processed_data.get('ivme_olcer_x', 0):.3f} "
            self.current_values['ivme_olcer_y'] = f"{processed_data.get('ivme_olcer_y', 0):.3f} "
            self.current_values['ivme_olcer_z'] = f"{processed_data.get('ivme_olcer_z', 0):.3f} "
            self.current_values['ivme_olcer_x_hz'] = f"{processed_data.get('ivme_olcer_x_hz', 0):.1f} "
            self.current_values['ivme_olcer_y_hz'] = f"{processed_data.get('ivme_olcer_y_hz', 0):.1f} "
            self.current_values['ivme_olcer_z_hz'] = f"{processed_data.get('ivme_olcer_z_hz', 0):.1f} "
            
            # Hız bilgileri
            cutting_speed = processed_data.get('serit_kesme_hizi', 0)
            descent_speed = processed_data.get('serit_inme_hizi', 0)
            self.current_values['serit_kesme_hizi'] = f"{cutting_speed:.1f} "
            self.current_values['serit_inme_hizi'] = f"{descent_speed:.1f} "
            
            # Hız değerlerini UI'da güncelle
            if hasattr(self.ui, 'labelBandCuttingSpeedValue'):
                self.ui.labelBandCuttingSpeedValue.setText(f"{cutting_speed:.1f}")
            if hasattr(self.ui, 'labelBandDescentSpeedValue'):
                self.ui.labelBandDescentSpeedValue.setText(f"{descent_speed:.1f}")
            
            # Kesim bilgileri
            self.current_values['kesilen_parca_adeti'] = str(processed_data.get('kesilen_parca_adeti', 0))
            
            # Durum ve alarm bilgileri
            testere_durumu = processed_data.get('testere_durumu', 0)
            durum_text = {
                0: "BOŞTA",
                1: "HİDROLİK AKTİF",
                2: "ŞERİT MOTOR ÇALIŞIYOR",
                3: "KESİM YAPILIYOR",
                4: "KESİM BİTTİ",
                5: "ŞERİT YUKARI ÇIKIYOR",
                6: "MALZEME BESLEME"
            }.get(testere_durumu, "BİLİNMİYOR")
            
            self.current_values['testere_durumu'] = durum_text
            self.current_values['alarm_status'] = str(processed_data.get('alarm_status', '-'))
            self.current_values['alarm_bilgisi'] = str(processed_data.get('alarm_bilgisi', '-'))
            
            # Kesim durumunu kontrol et
            if testere_durumu == 3:  # KESIM_YAPILIYOR
                if not self.kesim_baslama_zamani:
                    # Kesim başladı
                    self.kesim_baslama_zamani = datetime.now()
                    self.current_values['kesim_baslama'] = self.kesim_baslama_zamani.strftime("%H:%M:%S.%f")[:-3]
                    # Log ekle
                    self.add_log("Kesim Başladı !", "INFO")
                
                # Kesim süresini güncelle
                if self.kesim_baslama_zamani:
                    sure = datetime.now() - self.kesim_baslama_zamani
                    self.current_values['kesim_sure'] = f"{int(sure.total_seconds())} saniye"
            elif testere_durumu != 3 and self.kesim_baslama_zamani:
                # Kesim bitti, süreyi sıfırla
                self.kesim_baslama_zamani = None
                self.current_values['kesim_baslama'] = "-"
                self.current_values['kesim_sure'] = "-"
                # Log ekle
                self.add_log("Kesim Bitti !", "INFO")
            
            # Son güncelleme zamanını kaydet
            self._last_update_time = datetime.now()
            
            # UI'ı güncelle
            self.update_ui()
            
        except Exception as e:
            logger.error(f"Değer güncelleme hatası: {e}")
            logger.exception("Detaylı hata:")

    def add_log(self, message: str, level: str = 'INFO'):
        """Thread-safe log ekleme"""
        try:
            if not hasattr(self.ui, 'log_text') or not self.ui.log_text:
                return
                
            # Saat ve dakika formatı
            timestamp = datetime.now().strftime('%H:%M')
            
            # Log seviyesine göre renk belirle
            color = "#F4F6FC" # Varsayılan renk
            # Hata mesajları için rengi koruyalım
            if level == 'WARNING':
                color = "orange"
            elif level == 'ERROR':
                color = "red"
            
            # Mesaj içeriğini kontrol edip kullanıcı dostu hale getir
            display_message = message
            # Örnek: Hız gönderme mesajlarını yakala ve yeniden biçimlendir
            if "Kesme hızı gönderildi" in message:
                try:
                    # Mesajdaki parantez içindeki hız seviyesini al (ör: slow, normal, fast)
                    import re
                    match_level = re.search(r'\((.*?)\)', message)
                    
                    speed_value = float(message.split(":")[-1].strip().split(" ")[0])
                    display_message = f"Şerit Kesme Hızı \"{speed_value:.2f}\" olarak ayarlandı!"
                except (ValueError, IndexError, AttributeError):
                    pass # Hata olursa orijinal mesajı kullan
            elif "İnme hızı gönderildi" in message:
                 try:
                    # Mesajdaki parantez içindeki hız seviyesini al (ör: slow, normal, fast)
                    import re
                    match_level = re.search(r'\((.*?)\)', message)

                    speed_value = float(message.split(":")[-1].strip().split(" ")[0])
                    display_message = f"Şerit İnme Hızı \"{speed_value:.2f}\"  olarak ayarlandı!"
                 except (ValueError, IndexError, AttributeError):
                    pass # Hata olursa orijinal mesajı kullan
                
            # HTML formatında mesaj oluştur
            # Saat ve mesajı ayrı satırlarda ve istenen stilde göster
            # Saat için daha ince, mesaj için daha kalın font ağırlığı
            log_message_html = f"<span style='font-size:20px; color:{color}; font-weight:extra-light;'>{timestamp}</span><br>"
            log_message_html += f"<span style='font-size:20px; color:{color}; font-weight:medium;'>{display_message}</span><br><br>"
            
            # HTML olarak ekle
            self.ui.log_text.insertHtml(log_message_html)
            
            # En alta kaydır
            self.ui.log_text.verticalScrollBar().setValue(self.ui.log_text.verticalScrollBar().maximum())
            
            
            while self.ui.log_text.document().blockCount() > 1000:
                cursor = self.ui.log_text.textCursor()
                cursor.movePosition(QTextCursor.Start)
                # İlk bloğu sil
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                
        except Exception as e:
            logger.error(f"Log ekleme hatası: {e}")

    def update_modbus_status(self, connected: bool, ip: str):
        """Modbus durumunu günceller"""
        try:
            if connected:
                self.current_values['modbus_status'] = f"Bağlı ({ip})"
                self.current_values['testere_durumu'] = "Veri bekleniyor..."
                if hasattr(self.ui, 'labelSystemStatusInfo'):
                    self.ui.labelSystemStatusInfo.setText("Veri bekleniyor...")
            else:
                self.current_values['modbus_status'] = f"Bağlantı Yok ({ip})"
                self.current_values['testere_durumu'] = "Bağlantı Yok"
                if hasattr(self.ui, 'labelSystemStatusInfo'):
                    self.ui.labelSystemStatusInfo.setText("Bağlantı Yok")
        except Exception as e:
            logger.error(f"Modbus durum güncelleme hatası: {e}")
    
    def update_ui(self):
        """UI bileşenlerini günceller"""
        try:
            # Sistem durumu etiketi
            if hasattr(self.ui, 'labelSystemStatusInfo'):
                self.ui.labelSystemStatusInfo.setText(self._get_status_message(self.current_values['testere_durumu']))
            
        except Exception as e:
            logger.error(f"UI güncelleme hatası: {e}")
            logger.exception("Detaylı hata:") 

    def update_data(self, processed_data: Dict):
        """Arayüz verilerini günceller"""
        try:
            # Modbus durumunu güncelle
            if 'modbus_connected' in processed_data:
                self.update_modbus_status(
                    processed_data['modbus_connected'],
                    processed_data.get('modbus_ip', '192.168.1.147')
                )
            
            # Testere durumunu güncelle
            testere_durumu = int(processed_data.get('testere_durumu', 0))
            durum_text = {
                0: "BOŞTA",
                1: "HİDROLİK AKTİF",
                2: "ŞERİT MOTOR ÇALIŞIYOR",
                3: "KESİM YAPILIYOR",
                4: "KESİM BİTTİ",
                5: "ŞERİT YUKARI ÇIKIYOR",
                6: "MALZEME BESLEME"
            }.get(testere_durumu, "BİLİNMİYOR")
            
            self.current_values['testere_durumu'] = durum_text
            if hasattr(self.ui, 'labelSystemStatusInfo'):
                self.ui.labelSystemStatusInfo.setText(self._get_status_message(durum_text))
            
            # Kesim durumunu kontrol et
            if testere_durumu == 3:  # KESIM_YAPILIYOR
                if not self._cutting_start_time:
                    self._cutting_start_time = datetime.now()
                    self.current_values['kesim_baslama'] = self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3]
                
                # Geçen süreyi hesapla ve göster
                elapsed = datetime.now() - self._cutting_start_time
                minutes = int(elapsed.total_seconds() // 60)
                seconds = int(elapsed.total_seconds() % 60)
                milliseconds = int(elapsed.total_seconds() * 1000) % 1000
                self.current_values['cutting_time'] = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
                
            elif testere_durumu != 3 and self._cutting_start_time:
                # Kesim bitti, süreleri kaydet
                end_time = datetime.now()
                elapsed = end_time - self._cutting_start_time
                
                # Önceki kesim bilgilerini güncelle
                self.current_values['kesim_baslama'] = self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3]
                self.current_values['kesim_sure'] = f"{int(elapsed.total_seconds() // 60):02d}:{int(elapsed.total_seconds() % 60):02d}"
                
                # Kesim bilgilerini sıfırla
                self._cutting_start_time = None
                self.current_values['cutting_time'] = "00:00"
            
            # Diğer değerleri güncelle
            self._update_values(processed_data)
            
            # Kritik değerleri kontrol et
            self._check_critical_values(processed_data)
            
            # Kamera frame sayısını güncelle
            if hasattr(self, 'camera') and self.camera.is_recording:
                self.current_values['camera_frame_count'] = str(self.camera.frame_count)
            
        except Exception as e:
            logger.error(f"Veri güncelleme hatası: {str(e)}")
            logger.exception("Detaylı hata:") 

    def _check_critical_values(self, data: Dict):
        """Kritik değerleri kontrol eder ve gerekirse log ekler"""
        # Testere durumunu al
        testere_durumu = int(data.get('testere_durumu', 0))
        
        # Akım kontrolü
        if testere_durumu == 3:  # KESIM_YAPILIYOR
            current = float(data.get('serit_motor_akim_a', 0))
            if current > 25:
                self.add_log(f"Yüksek motor akımı: {current:.2f}A", "WARNING")
            elif current > 30:
                self.add_log(f"Kritik motor akımı: {current:.2f}A", "ERROR")
            
            # Sapma kontrolü - sadece kesim durumunda
            deviation = float(data.get('serit_sapmasi', 0))
            if abs(deviation) > 0.4:
                self.add_log(f"Yüksek şerit sapması: {deviation:.2f}mm", "WARNING")
            elif abs(deviation) > 0.6:
                self.add_log(f"Kritik şerit sapması: {deviation:.2f}mm", "ERROR")
            
        # Titreşim kontrolü - her durumda kontrol et
        vib_x = float(data.get('ivme_olcer_x_hz', 0))
        vib_y = float(data.get('ivme_olcer_y_hz', 0))
        vib_z = float(data.get('ivme_olcer_z_hz', 0))
        max_vib = max(vib_x, vib_y, vib_z)
        
        if max_vib > 200.0:
            self.add_log(f"Yüksek titreşim: {max_vib:.2f}Hz", "WARNING")
        elif max_vib > 300.0:
            self.add_log(f"Kritik titreşim: {max_vib:.2f}Hz", "ERROR") 

    def _send_manual_speed(self, speed_level: str):
        """Tek bir hızı gönderir"""
        try:
            # Modbus client'ı al
            if not self.controller_factory or not self.controller_factory.modbus_client:
                logger.error("Modbus bağlantısı bulunamadı")
                self.add_log("Hız ayarlanamadı: Modbus bağlantısı yok.", "ERROR")
                return
            
            modbus_client = self.controller_factory.modbus_client
            
            # Seçilen hız seviyesine ait değerleri al
            speeds = self.speed_values.get(speed_level)
            if not speeds:
                logger.error(f"Geçersiz hız seviyesi: {speed_level}")
                self.add_log(f"Hata: Geçersiz hız seviyesi {speed_level}.", "ERROR")
                return
                
            cutting_speed = speeds["cutting"]
            descent_speed = speeds["descent"]
            
            # Kesme hızını gönder
            # Negatif hız değerleri olabilir mi? Varsayılan olarak pozitif kabul edelim.
            reverse_calculate_value(modbus_client, cutting_speed, 'serit_kesme_hizi', False)
            logger.info(f"Kesme hızı {cutting_speed:.1f} mm/s olarak ayarlandı")
            self.add_log(f"Kesme hızı {cutting_speed:.1f} mm/s olarak ayarlandı", "INFO")
            
            # İnme hızını gönder
            reverse_calculate_value(modbus_client, descent_speed, 'serit_inme_hizi', False)
            logger.info(f"İnme hızı {descent_speed:.1f} mm/s olarak ayarlandı")
            self.add_log(f"İnme hızı {descent_speed:.1f} mm/s olarak ayarlandı", "INFO")

        except Exception as e:
            logger.error(f"Hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            self.add_log(f"Hız ayarlama hatası: {str(e)}", "ERROR") 

    def _handle_cutting_speed_frame_click(self, event=None):
        """BandCuttingSpeedFrame tıklama olayını yönetir"""
        try:
            # Frame tıklama kontrolü
            if not self._frame_click_enabled:
                return
            
            if event is not None:
                event.accept()
            
            # Mevcut değeri al ve float'a çevir
            if hasattr(self.ui, 'labelBandCuttingSpeedValue'):
                current_value = self.ui.labelBandCuttingSpeedValue.text()
                try:
                    initial_value = float(current_value) if current_value != "NULL" else 0.0
                except ValueError:
                    initial_value = 0.0
                
                # NumpadDialog ile kullanıcıdan değer al
                dialog = NumpadDialog(self)
                dialog.value = str(int(initial_value)) if initial_value != 0.0 else ""
                dialog.update_label()
                
                result = dialog.exec()
                
                if result == dialog.Accepted:
                    value_str = dialog.get_value()
                    try:
                        value = float(value_str.replace(",", "."))
                    except Exception:
                        value = 0.0
                    
                    if value > 0:
                        self._send_manual_speed_value(value)
                        self.current_values['serit_kesme_hizi'] = f"{value:.1f}"
                        self.ui.labelBandCuttingSpeedValue.setText(f"{value:.2f}")
                        self.add_log(f"Kesme hızı {value:.2f} mm/s olarak ayarlandı", "INFO")
        except Exception as e:
            logger.error(f"Kesme hızı ayarlama hatası: {e}")
            logger.exception("Detaylı hata:")
            self.add_log(f"Kesme hızı ayarlama hatası: {str(e)}", "ERROR")

    def _send_manual_speed_value(self, speed_value: float):
        """Belirli bir hız değerini gönderir"""
        try:
            # Modbus client'ı al
            if not self.controller_factory or not self.controller_factory.modbus_client:
                logger.error("Modbus bağlantısı bulunamadı")
                self.add_log("Hız ayarlanamadı: Modbus bağlantısı yok.", "ERROR")
                return
            
            modbus_client = self.controller_factory.modbus_client
            
            # Kesme hızını gönder
            reverse_calculate_value(modbus_client, speed_value, 'serit_kesme_hizi', False)
            logger.info(f"Kesme hızı {speed_value:.1f} mm/s olarak gönderildi")
            
        except Exception as e:
            logger.error(f"Hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            self.add_log(f"Hız ayarlama hatası: {str(e)}", "ERROR") 

    def _handle_descent_speed_frame_click(self, event=None):
        """BandDescentSpeedFrame tıklama olayını yönetir"""
        try:
            # Frame tıklama kontrolü
            if not self._frame_click_enabled:
                return
            
            if event is not None:
                event.accept()
            
            # Mevcut değeri al ve float'a çevir
            if hasattr(self.ui, 'labelBandDescentSpeedValue'):
                current_value = self.ui.labelBandDescentSpeedValue.text()
                try:
                    initial_value = float(current_value) if current_value != "NULL" else 0.0
                except ValueError:
                    initial_value = 0.0
                
                # NumpadDialog ile kullanıcıdan değer al
                dialog = NumpadDialog(self)
                dialog.value = str(int(initial_value)) if initial_value != 0.0 else ""
                dialog.update_label()
                
                result = dialog.exec()
                
                if result == dialog.Accepted:
                    value_str = dialog.get_value()
                    try:
                        value = float(value_str.replace(",", "."))
                    except Exception:
                        value = 0.0
                    
                    if value > 0:
                        self._send_manual_descent_speed_value(value)
                        self.current_values['serit_inme_hizi'] = f"{value:.1f}"
                        self.ui.labelBandDescentSpeedValue.setText(f"{value:.2f}")
                        self.add_log(f"İnme hızı {value:.2f} mm/s olarak ayarlandı", "INFO")
        except Exception as e:
            logger.error(f"İnme hızı ayarlama hatası: {e}")
            logger.exception("Detaylı hata:")
            self.add_log(f"İnme hızı ayarlama hatası: {str(e)}", "ERROR")

    def _send_manual_descent_speed_value(self, speed_value: float):
        """Belirli bir inme hızı değerini gönderir"""
        try:
            # Modbus client'ı al
            if not self.controller_factory or not self.controller_factory.modbus_client:
                logger.error("Modbus bağlantısı bulunamadı")
                self.add_log("Hız ayarlanamadı: Modbus bağlantısı yok.", "ERROR")
                return
            
            modbus_client = self.controller_factory.modbus_client
            
            # İnme hızını gönder
            reverse_calculate_value(modbus_client, speed_value, 'serit_inme_hizi', False)
            logger.info(f"İnme hızı {speed_value:.2f} mm/s olarak gönderildi")
            
        except Exception as e:
            logger.error(f"Hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            self.add_log(f"Hız ayarlama hatası: {str(e)}", "ERROR") 

    def _icon(self, name: str) -> QIcon:
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
        return QIcon(os.path.join(base, name))

    def _apply_local_icons(self) -> None:
        try:
            if hasattr(self.ui, 'btnControlPanel'):
                self.ui.btnControlPanel.setIcon(self._icon("control-panel-icon2.svg"))
            if hasattr(self.ui, 'btnPositioning'):
                self.ui.btnPositioning.setIcon(self._icon("positioning-icon2.svg"))
            if hasattr(self.ui, 'btnCamera'):
                self.ui.btnCamera.setIcon(self._icon("camera-icon2.svg"))
            if hasattr(self.ui, 'btnSensor'):
                self.ui.btnSensor.setIcon(self._icon("sensor-icon2.svg"))
            if hasattr(self.ui, 'btnTracking'):
                self.ui.btnTracking.setIcon(self._icon("tracking-icon2.svg"))
        except Exception:
            pass

    # ---- Navigation
    def _connect_navigation(self) -> None:
        self.ui.btnControlPanel.clicked.connect(self._open_control_panel)
        self.ui.btnTracking.clicked.connect(self._open_monitoring)
        self.ui.btnCamera.clicked.connect(self._open_camera)
        self.ui.btnSensor.clicked.connect(self._open_sensor)
        self.ui.btnPositioning.clicked.connect(self._open_positioning)

    def _open_control_panel(self) -> None:
        # Control panel'i göster
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        
        # Focus'u control panel'e ver
        self.setFocus()


    def _open_positioning(self) -> None:
        if self._positioning_page is None:
            from .pyside_positioning import PositioningPage
            self._positioning_page = PositioningPage(main_ref=self, get_data_callback=self.get_data_callback)
        
        # Control panel'i gizle
        self.hide()
            
        # Positioning widget'ını göster ve aktif icon'u ayarla
        self._positioning_page.set_active_nav("btnPositioning_2")
        self._positioning_page.showFullScreen()            
        self._positioning_page.raise_()
        self._positioning_page.activateWindow()
            
        # Focus'u positioning widget'ına ver
        self._positioning_page.setFocus()

    def _open_monitoring(self) -> None:
        if self._monitoring_page is None:
            from .pyside_monitoring import MonitoringPage
            self._monitoring_page = MonitoringPage(main_ref=self, get_data_callback=self.get_data_callback)
        
        # Control panel'i gizle
        self.hide()
        
        # Monitoring widget'ını göster ve aktif icon'u ayarla
        self._monitoring_page.set_active_nav("btnTracking")
        self._monitoring_page.showFullScreen()
        self._monitoring_page.raise_()
        self._monitoring_page.activateWindow()
        
        # Focus'u monitoring widget'ına ver
        self._monitoring_page.setFocus()

    def _open_camera(self) -> None:
        if self._camera_page is None:
            from .pyside_camera import CameraPage
            self._camera_page = CameraPage(main_ref=self, get_data_callback=self.get_data_callback)
            
            # Wear calculator referansını camera page'e ver
            if hasattr(self, 'wear_calculator') and self.wear_calculator:
                self._camera_page.wear_calculator = self.wear_calculator
        
        # Control panel'i gizle
        self.hide()
        
        # Camera widget'ını göster ve aktif icon'u ayarla
        self._camera_page.set_active_nav("btnCamera")
        self._camera_page.showFullScreen()
        self._camera_page.raise_()
        self._camera_page.activateWindow()
        
        # Focus'u camera widget'ına ver
        self._camera_page.setFocus()

    def _open_sensor(self) -> None:
        if self._sensor_page is None:
            from .pyside_sensor import SensorPage
            self._sensor_page = SensorPage(main_ref=self, get_data_callback=self.get_data_callback)
        
        # Control panel'i gizle
        self.hide()
        
        # Sensor widget'ını göster ve aktif icon'u ayarla
        self._sensor_page.set_active_nav("btnSensor")
        self._sensor_page.showFullScreen()
        self._sensor_page.raise_()
        self._sensor_page.activateWindow()
        
        # Focus'u sensor widget'ına ver
        self._sensor_page.setFocus()

    # ---- Date/Time
    def _update_datetime_labels(self) -> None:
        now = QDateTime.currentDateTime()
        date_text = now.toString('dd.MM.yyyy dddd')
        time_text = now.toString('HH:mm')
        if hasattr(self.ui, 'labelDate'):
            self.ui.labelDate.setText(date_text)
        if hasattr(self.ui, 'labelTime'):
            self.ui.labelTime.setText(time_text) 