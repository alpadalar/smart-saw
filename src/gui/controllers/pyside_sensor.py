from typing import Callable, Dict, Optional
from PySide6.QtCore import QTimer, QDateTime, Qt, QPoint
from PySide6.QtWidgets import QWidget, QButtonGroup, QLabel
from PySide6.QtGui import QIcon, QPainter, QPen, QColor, QBrush, QPolygon
import os
from datetime import datetime, timedelta
import threading
import collections
import logging

from gui.ui_files.sensor_widget_ui import Ui_Form

# Logger
logger = logging.getLogger(__name__)


class CuttingGraphWidget(QWidget):
    """Kesim grafiği widget'ı - seçilen X/Y eksenlerine göre son kesim verilerini çizer"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(860, 450)
        
        # Veri yapısı: (x_value, y_value) tuple'ları
        self.data_points = collections.deque(maxlen=1000)  # Son 1000 veri noktası
        self.max_points = 1000
        
        # Grafik ayarları
        self.padding = 20
        self.grid_color = QColor(255, 255, 255, 50)  # Şeffaf beyaz
        self.line_color = QColor(0xF4, 0xF6, 0xFC)  # Çizgi rengi (F4F6FC)
        self.fill_color = QColor(149, 9, 82, 30)  # Dolgu rengi
        
        # Eksen bilgileri
        self.x_axis_type = "timestamp"  # Varsayılan
        self.y_axis_type = "serit_kesme_hizi"  # Varsayılan

        # Zaman ekseni etiketleri için kesim başlangıcı ve son nokta zamanı
        self.cut_start_time: Optional[datetime] = None
        self.last_point_time: Optional[datetime] = None
        # Yükseklik ekseni için başlangıç ve mevcut değerler
        self.start_height_value: Optional[float] = None
        self.current_height_value: Optional[float] = None
        
        # Thread-safe veri erişimi için lock
        self._data_lock = threading.Lock()
        
        # Timer ile güncelleme
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(100)  # 10 FPS
        
        # Widget stil ayarları
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Grafik label'larını oluştur
        self._create_graph_labels()
        
    def set_axis_types(self, x_axis: str, y_axis: str):
        """X ve Y eksen tiplerini ayarlar"""
        try:
            with self._data_lock:
                self.x_axis_type = x_axis
                self.y_axis_type = y_axis
                # Eksen değiştiğinde verileri temizle
                self.data_points.clear()
        except Exception as e:
            logger.error(f"Eksen tipi ayarlama hatası: {e}")
    
    def add_data_point(self, x_value: float, y_value: float):
        """Yeni veri noktası ekler (thread-safe)"""
        try:
            with self._data_lock:
                self.data_points.append((x_value, y_value))
                # Maksimum veri sayısını aşarsa eski verileri sil
                if len(self.data_points) > self.max_points:
                    self.data_points.popleft()
                # Zaman ekseni kullanılıyorsa son nokta zamanını güncelle
                if self.x_axis_type == "timestamp":
                    self.last_point_time = datetime.now()
        except Exception as e:
            logger.error(f"Veri noktası ekleme hatası: {e}")
    
    def clear_data(self):
        """Tüm verileri temizler"""
        try:
            with self._data_lock:
                self.data_points.clear()
                # Zaman bilgilerini sıfırlama (kesim başlayınca yeniden ayarlanacak)
                self.last_point_time = None
            # Label'ları sıfırla - zaman ekseni için özel format
            if self.x_axis_type == "timestamp" or self.y_axis_type == "timestamp":
                self.update_label_values(0, 0, 0, 0)
            else:
                self.update_label_values(0.0, 0.0, 0.0, 0.0)
        except Exception as e:
            logger.error(f"Veri temizleme hatası: {e}")
    
    def paintEvent(self, event):
        """Grafiği çizer"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Arkaplan şeffaf
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            
            # Veri yoksa sadece grid çiz
            if not self.data_points:
                self._draw_grid(painter, self.rect().adjusted(self.padding, self.padding, -self.padding, -self.padding))
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
            
            # Dikey çizgiler (20 adet)
            for i in range(21):
                x = rect.left() + (rect.width() * i) // 20
                painter.drawLine(x, rect.top(), x, rect.bottom())
            
            # Yatay çizgiler (10 adet)
            for i in range(11):
                y = rect.top() + (rect.height() * i) // 10
                painter.drawLine(rect.left(), y, rect.right(), y)
                
        except Exception as e:
            logger.error(f"Grid çizim hatası: {e}")
    
    def _draw_data(self, painter: QPainter, rect):
        """Veri çizer"""
        try:
            with self._data_lock:
                if len(self.data_points) < 2:
                    return
                
                # X ve Y değerlerini ayır
                x_values = [point[0] for point in self.data_points]
                y_values = [point[1] for point in self.data_points]
                
                # Değer aralıklarını hesapla
                x_min, x_max = min(x_values), max(x_values)
                y_min, y_max = min(y_values), max(y_values)
                
                # Aralık çok küçükse genişlet
                if x_max - x_min < 0.1:
                    mid_val = (x_min + x_max) / 2
                    x_min = mid_val - 0.05
                    x_max = mid_val + 0.05
                
                if y_max - y_min < 0.1:
                    mid_val = (y_min + y_max) / 2
                    y_min = mid_val - 0.05
                    y_max = mid_val + 0.05
                
                # Label değerlerini güncelle
                if self.x_axis_type == "timestamp" and self.cut_start_time and self.last_point_time:
                    # Zaman ekseni için özel etiketler (başlangıç -> son)
                    self._update_time_axis_labels(self.cut_start_time, self.last_point_time, y_min, y_max)
                elif self.x_axis_type == "kafa_yuksekligi_mm" and self.start_height_value is not None and self.current_height_value is not None:
                    # Yükseklik ekseni için özel etiketler (başlangıç -> mevcut)
                    self._update_height_axis_labels(self.start_height_value, self.current_height_value, y_min, y_max)
                else:
                    self.update_label_values(x_min, x_max, y_min, y_max)
                
                # Çizgi rengi
                painter.setPen(QPen(self.line_color, 2))
                
                # Dolgu rengi
                painter.setBrush(QBrush(self.fill_color))
                
                # Çizgi noktalarını hesapla (yeni veri sağdan görünecek şekilde index'e göre yerleştir)
                points = []
                total_points = len(self.data_points)
                for i, (_x_value, y_value) in enumerate(self.data_points):
                    # X koordinatı: 0..N-1 arasında eşit aralıklı, en yeni sağda
                    if total_points > 1:
                        x = rect.left() + (rect.width() * i) // (total_points - 1)
                    else:
                        x = rect.left() + rect.width() // 2
                    
                    # Y koordinatı (ters çevrilmiş - Qt'de y aşağı doğru artar)
                    if y_max != y_min:
                        normalized_y = (y_value - y_min) / (y_max - y_min)
                    else:
                        normalized_y = 0.5
                    y = rect.bottom() - (rect.height() * normalized_y)
                    
                    points.append((x, y))
                
                # Çizgi çiz
                if len(points) > 1:
                    # Ana çizgi
                    for i in range(len(points) - 1):
                        painter.drawLine(int(points[i][0]), int(points[i][1]), 
                                       int(points[i+1][0]), int(points[i+1][1]))
 
                if points:
                    last_x, last_y = points[-1]
                    circle_size = 6
                    painter.setBrush(QBrush(QColor(255, 0, 0)))
                    painter.setPen(QPen(QColor(255, 0, 0), 1))
                    painter.drawEllipse(int(last_x - circle_size), int(last_y - circle_size), 
                                      circle_size * 2, circle_size * 2)
                    
        except Exception as e:
            logger.error(f"Veri çizim hatası: {e}")
    
    def resizeEvent(self, event):
        """Widget boyutu değiştiğinde"""
        super().resizeEvent(event)
        # Label pozisyonlarını güncelle (eğer label'lar varsa)
        if hasattr(self, 'yust') and self.yust:
            self._update_label_positions()
        self.update()
    
    def _create_graph_labels(self):
        """Grafik label'larını oluşturur"""
        from PySide6.QtWidgets import QLabel
        
        # Label stil ayarları
        label_style = """
            QLabel {
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                background-color: transparent;
                border: none;
            }
        """
        
        # Sol taraftaki label'lar (Y ekseni) - kesimGrafigiFrame içinde
        self.yust = QLabel(self.parent())
        self.yust.setStyleSheet(label_style)
        self.yust.setText("0")
        self.yust.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.yorta = QLabel(self.parent())
        self.yorta.setStyleSheet(label_style)
        self.yorta.setText("0")
        self.yorta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.yalt = QLabel(self.parent())
        self.yalt.setStyleSheet(label_style)
        self.yalt.setText("0")
        self.yalt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Alt taraftaki label'lar (X ekseni) - kesimGrafigiFrame içinde
        self.xust = QLabel(self.parent())
        self.xust.setStyleSheet(label_style)
        self.xust.setText("0.00")
        self.xust.setAlignment(Qt.AlignCenter)
        
        self.xorta = QLabel(self.parent())
        self.xorta.setStyleSheet(label_style)
        self.xorta.setText("0.00")
        self.xorta.setAlignment(Qt.AlignCenter)
        
        self.xalt = QLabel(self.parent())
        self.xalt.setStyleSheet(label_style)
        self.xalt.setText("0.00")
        self.xalt.setAlignment(Qt.AlignCenter)
        
        # Label'ları göster
        self.yust.show()
        self.yorta.show()
        self.yalt.show()
        self.xust.show()
        self.xorta.show()
        self.xalt.show()
        
        # Label pozisyonlarını güncelle
        self._update_label_positions()

    def _format_time_label(self, dt: datetime) -> str:
        """Zaman etiketlerini HH.MM formatında döndürür"""
        try:
            return dt.strftime('%H.%M')
        except Exception:
            return "0.00"

    def _update_time_axis_labels(self, start_dt: datetime, end_dt: datetime, y_min: float, y_max: float):
        """Zaman ekseni seçili olduğunda X etiketlerini (başlangıç, orta, son) günceller"""
        try:
            # Y ekseni etiketleri
            self.update_label_values(None, None, y_min, y_max)
            # X ekseni etiketleri
            if start_dt and end_dt:
                mid_dt = start_dt + (end_dt - start_dt) / 2
                if hasattr(self, 'xust'):
                    self.xust.setText(self._format_time_label(start_dt))
                if hasattr(self, 'xorta'):
                    self.xorta.setText(self._format_time_label(mid_dt))
                if hasattr(self, 'xalt'):
                    self.xalt.setText(self._format_time_label(end_dt))
        except Exception as e:
            logger.error(f"Zaman etiketi güncelleme hatası: {e}")
    
    def _update_height_axis_labels(self, start_height: float, current_height: float, y_min: float, y_max: float):
        """Yükseklik X ekseni seçili olduğunda X etiketlerini günceller: başlangıç | orta | mevcut"""
        try:
            # Y ekseni etiketlerini güncelle
            self.update_label_values(None, None, y_min, y_max)
            # X ekseni: solda başlangıç yüksekliği sabit, ortada ortalama, sağda mevcut yükseklik
            start_val = float(start_height)
            curr_val = float(current_height)
            mid_val = (start_val + curr_val) / 2.0
            if hasattr(self, 'xust'):
                self.xust.setText(f"{start_val:.2f}")
            if hasattr(self, 'xorta'):
                self.xorta.setText(f"{mid_val:.2f}")
            if hasattr(self, 'xalt'):
                self.xalt.setText(f"{curr_val:.2f}")
        except Exception as e:
            logger.error(f"Yükseklik etiketi güncelleme hatası: {e}")
    
    def _update_label_positions(self):
        """Label pozisyonlarını günceller"""
        try:
            # Grafik widget'ının pozisyonu (kesimGrafigiFrame içindeki konumu)
            graph_x = 72  # Grafik widget'ının x pozisyonu
            graph_y = 87  # Grafik widget'ının y pozisyonu
            graph_width = 860  # Grafik widget'ının genişliği
            graph_height = 450  # Grafik widget'ının yüksekliği
            
            # Label boyutları
            label_width = 80  # Genişliği artırdık
            label_height = 30
            
            # Sol taraftaki label'lar (Y ekseni) 
            # En üst
            self.yust.setGeometry(graph_x - label_width, graph_y + 20, label_width, label_height)
            # Orta
            self.yorta.setGeometry(graph_x - label_width, graph_y + (graph_height // 2) - (label_height // 2), label_width, label_height)
            # En alt
            self.yalt.setGeometry(graph_x - label_width, graph_y + graph_height - label_height - 20, label_width, label_height)
            
            # Alt taraftaki label'lar (X ekseni) - grafiğin altında
            # En sol
            self.xust.setGeometry(graph_x + 20, graph_y + graph_height + 5, label_width, label_height)
            # Orta
            self.xorta.setGeometry(graph_x + (graph_width // 2) - (label_width // 2), graph_y + graph_height + 5, label_width, label_height)
            # En sağ
            self.xalt.setGeometry(graph_x + graph_width - label_width - 20, graph_y + graph_height + 5, label_width, label_height)
            
        except Exception as e:
            logger.error(f"Label pozisyon güncelleme hatası: {e}")

    def update_label_values(self, x_min=None, x_max=None, y_min=None, y_max=None):
        """Label değerlerini günceller"""
        try:
            # Debug: Zaman değerlerini logla
            if self.x_axis_type == "timestamp" or self.y_axis_type == "timestamp":
                logger.info(f"ZAMAN DEBUG - X: {x_min} -> {x_max}, Y: {y_min} -> {y_max}")
                logger.info(f"Eksen tipleri - X: {self.x_axis_type}, Y: {self.y_axis_type}")
            
            # Y ekseni label'ları (sol taraftaki) - ondalık kısım 2 hane ile
            if y_min is not None and y_max is not None:
                # Zaman ekseni için özel format
                if self.y_axis_type == "timestamp":
                    # Zaman için saniye cinsinden göster (0-999 arası)
                    y_max_val = min(int(y_max), 999)
                    y_min_val = max(int(y_min), 0)
                    y_mid_val = int((y_min_val + y_max_val) / 2)
                    
                    logger.info(f"Y ekseni zaman değerleri: {y_min_val}s -> {y_mid_val}s -> {y_max_val}s")
                    
                    self.yust.setText(f"{y_max_val}s")
                    self.yorta.setText(f"{y_mid_val}s")
                    self.yalt.setText(f"{y_min_val}s")
                else:
                    # Diğer eksenler için iki ondalık basamak ile
                    y_max_val = min(float(y_max), 9999.99)
                    y_min_val = max(float(y_min), -999.99)
                    y_mid_val = (y_min_val + y_max_val) / 2.0
                    
                    self.yust.setText(f"{y_max_val:.2f}")
                    self.yorta.setText(f"{y_mid_val:.2f}")
                    self.yalt.setText(f"{y_min_val:.2f}")
            
            # X ekseni label'ları (alt taraftaki) - ondalık kısım ile
            if x_min is not None and x_max is not None:
                # Zaman ekseni için özel format
                if self.x_axis_type == "timestamp":
                    # Zaman için saniye cinsinden göster (0-999 arası)
                    x_max_val = min(int(x_max), 999)
                    x_min_val = max(int(x_min), 0)
                    x_mid_val = int((x_min_val + x_max_val) / 2)
                    
                    logger.info(f"X ekseni zaman değerleri: {x_min_val}s -> {x_mid_val}s -> {x_max_val}s")
                    
                    self.xust.setText(f"{x_min_val}s")
                    self.xorta.setText(f"{x_mid_val}s")
                    self.xalt.setText(f"{x_max_val}s")
                else:
                    # Diğer eksenler için ondalık kısım ile
                    x_max_val = min(x_max, 9999.99)  # Maksimum 4 haneli + 2 ondalık
                    x_min_val = max(x_min, -999.99)  # Minimum -999.99
                    x_mid_val = (x_min_val + x_max_val) / 2
                    
                    self.xust.setText(f"{x_min_val:.2f}")
                    self.xorta.setText(f"{x_mid_val:.2f}")
                    self.xalt.setText(f"{x_max_val:.2f}")
                
        except Exception as e:
            logger.error(f"Label değer güncelleme hatası: {e}")


class SensorPage(QWidget):
    def __init__(self, main_ref=None, get_data_callback: Optional[Callable[[], Dict]] = None) -> None:
        super().__init__(None)  # top-level window
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.main_ref = main_ref
        self.get_data_callback = get_data_callback
        # Apply same background image as control panel (efficient QLabel)
        self._apply_background()
        
        # Replace sidebar icons
        self._apply_local_icons()

        # Navigation
        self._connect_navigation()

        # Axis selection groups (exclusive)
        self._setup_axis_button_groups()

        # Anomaly states
        self.anomaly_states = {
            'KesmeHizi': False,
            'IlerlemeHizi': False,
            'SeritAkim': False,
            'Sicaklik': False,
            'Nem': False,
            'SeritSapmasi': False,
            'TitresimX': False,
            'TitresimY': False,
            'TitresimZ': False,
        }

        # Kesim grafiği widget'ı
        self.cutting_graph = None
        self._setup_cutting_graph()

        # Son kesim verilerini saklamak için
        self.last_cut_data = []
        self.is_cutting = False
        self.cut_start_time = None
        # Buffer to store full current cut for all metrics
        self.current_cut_buffer = []
        
        # Veritabanı bağlantısı
        try:
            import sqlite3
            self.db = sqlite3.connect('data/total.db')
            logger.info("Veritabanı bağlantısı başarılı: data/total.db")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            self.db = None

        # Timers (date/time)
        self._datetime_timer = QTimer(self)
        self._datetime_timer.timeout.connect(self._update_datetime_labels)
        self._datetime_timer.start(1000)
        self._update_datetime_labels()

        # Timers (data)
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self._on_data_tick)
        self._data_timer.start(200)  # 200 ms
        self._on_data_tick()

        # Optional reset button
        if hasattr(self.ui, 'toolButton'):
            self.ui.toolButton.clicked.connect(self.reset_anomaly_states)

        # Initial UI
        self._set_all_frames_green()
        self._set_all_info_labels("Her şey yolunda.")
        
        # Set sensor page as active initially
        self.set_active_nav('btnSensor')
        
        # İlk yüklemede grafiği tetikle
        if self.cutting_graph:
            # Eksen değişiklik event'ini manuel olarak tetikle
            self._on_x_axis_changed(None)

    def _setup_cutting_graph(self):
        """Kesim grafiği widget'ını kurar"""
        try:
            # Kesim grafiği frame'ini bul
            if hasattr(self.ui, 'kesimGrafigiFrame'):
                self.cutting_graph = CuttingGraphWidget(self.ui.kesimGrafigiFrame)
                self.cutting_graph.setGeometry(72, 87, 860, 450)  # 37 + 5 = 42 (5px sağa kaydırıldı)
                self.cutting_graph.show()
                
                # Default eksen tiplerini ayarla (Zaman - Kesme Hızı)
                self.cutting_graph.set_axis_types("timestamp", "serit_kesme_hizi")
                
                # Eski kesim verilerini yükle
                self._load_last_cut_data()
                
                # Grafik widget'ını güncelle
                self.cutting_graph.update()
                
                logger.info("Kesim grafiği widget'ı başarıyla kuruldu")
            else:
                logger.warning("kesimGrafigiFrame bulunamadı")
        except Exception as e:
            logger.error(f"Kesim grafiği kurulum hatası: {e}")

    def _get_selected_x_axis(self) -> str:
        """Seçili X eksenini döndürür"""
        try:
            if hasattr(self.ui, 'btnZaman') and self.ui.btnZaman.isChecked():
                return "timestamp"
            elif hasattr(self.ui, 'btnYukseklik') and self.ui.btnYukseklik.isChecked():
                return "kafa_yuksekligi_mm"
            else:
                return "timestamp"  # Varsayılan
        except Exception as e:
            logger.error(f"X ekseni seçimi hatası: {e}")
            return "timestamp"

    def _get_selected_y_axis(self) -> str:
        """Seçili Y eksenini döndürür"""
        try:
            if hasattr(self.ui, 'btnKesmeHizi') and self.ui.btnKesmeHizi.isChecked():
                return "serit_kesme_hizi"
            elif hasattr(self.ui, 'btnIlerlemeHizi') and self.ui.btnIlerlemeHizi.isChecked():
                return "serit_inme_hizi"
            elif hasattr(self.ui, 'btnSeritAkim') and self.ui.btnSeritAkim.isChecked():
                return "serit_motor_akim_a"
            elif hasattr(self.ui, 'btnSeritSapmasi') and self.ui.btnSeritSapmasi.isChecked():
                return "serit_sapmasi"
            elif hasattr(self.ui, 'btnSeritTork') and self.ui.btnSeritTork.isChecked():
                return "serit_motor_tork_percentage"
            else:
                return "serit_kesme_hizi"  # Varsayılan
        except Exception as e:
            logger.error(f"Y ekseni seçimi hatası: {e}")
            return "serit_kesme_hizi"

    def _on_x_axis_changed(self, button):
        """X ekseni değiştiğinde çağrılır"""
        try:
            if self.cutting_graph:
                x_axis = self._get_selected_x_axis()
                y_axis = self._get_selected_y_axis()
                self.cutting_graph.set_axis_types(x_axis, y_axis)
                # Kesim sürüyorsa veya buffer varsa buffer'dan yeniden çiz
                if self.is_cutting or (self.current_cut_buffer and len(self.current_cut_buffer) > 0):
                    self._rebuild_graph_from_buffer()
                else:
                    # Eski kesim verilerini yükle
                    self._load_last_cut_data()
                logger.info(f"X ekseni değiştirildi: {x_axis}")
        except Exception as e:
            logger.error(f"X ekseni değişiklik hatası: {e}")

    def _on_y_axis_changed(self, button):
        """Y ekseni değiştiğinde çağrılır"""
        try:
            if self.cutting_graph:
                x_axis = self._get_selected_x_axis()
                y_axis = self._get_selected_y_axis()
                self.cutting_graph.set_axis_types(x_axis, y_axis)
                # Kesim sürüyorsa veya buffer varsa buffer'dan yeniden çiz
                if self.is_cutting or (self.current_cut_buffer and len(self.current_cut_buffer) > 0):
                    self._rebuild_graph_from_buffer()
                else:
                    # Eski kesim verilerini yükle
                    self._load_last_cut_data()
                logger.info(f"Y ekseni değiştirildi: {y_axis}")
        except Exception as e:
            logger.error(f"Y ekseni değişiklik hatası: {e}")

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
            print(f"Navigation aktif durum ayarlama hatası: {e}")

    def _icon(self, name: str) -> QIcon:
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
        return QIcon(os.path.join(base, name))

    def _apply_background(self) -> None:
        try:
            bg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "background.png")
            self._bg_label = QLabel(self)
            self._bg_label.setGeometry(0, 0, self.width(), self.height())
            from PySide6.QtGui import QPixmap
            self._bg_label.setPixmap(QPixmap(bg_path))
            self._bg_label.setScaledContents(True)
            self._bg_label.lower()
            self._bg_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        except Exception:
            pass

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

    def _connect_navigation(self) -> None:
        if hasattr(self.ui, 'btnControlPanel'):
            self.ui.btnControlPanel.clicked.connect(self._open_control_panel)
        if hasattr(self.ui, 'btnPositioning'):
            self.ui.btnPositioning.clicked.connect(self._open_positioning)
        if hasattr(self.ui, 'btnTracking'):
            self.ui.btnTracking.clicked.connect(self._open_monitoring)
        if hasattr(self.ui, 'btnCamera'):
            self.ui.btnCamera.clicked.connect(self._open_camera)
        if hasattr(self.ui, 'btnSensor'):
            self.ui.btnSensor.clicked.connect(self._open_sensor)

    def _setup_axis_button_groups(self) -> None:
        # X-axis buttons
        self._x_group = QButtonGroup(self)
        self._x_group.setExclusive(True)
        for name in ('btnKesmeHizi', 'btnIlerlemeHizi', 'btnSeritAkim', 'btnSeritSapmasi', 'btnSeritTork'):
            btn = getattr(self.ui, name, None)
            if btn is not None:
                btn.setCheckable(True)
                self._x_group.addButton(btn)

        # Y-axis buttons
        self._y_group = QButtonGroup(self)
        self._y_group.setExclusive(True)
        for name in ('btnZaman', 'btnYukseklik'):
            btn = getattr(self.ui, name, None)
            if btn is not None:
                btn.setCheckable(True)
                self._y_group.addButton(btn)

        # Default olarak Kesme Hızı ve Zaman seçili olsun
        if hasattr(self.ui, 'btnKesmeHizi'):
            self.ui.btnKesmeHizi.setChecked(True)
        if hasattr(self.ui, 'btnZaman'):
            self.ui.btnZaman.setChecked(True)
        
        # Eksen değişikliklerini dinle
        self._x_group.buttonClicked.connect(self._on_x_axis_changed)
        self._y_group.buttonClicked.connect(self._on_y_axis_changed)

    def _open_control_panel(self) -> None:
        if self.main_ref:
            # Control panel'i direkt göster
            self.main_ref.set_active_nav("btnControlPanel")
            self.main_ref.showFullScreen()
            self.main_ref.raise_()
            self.main_ref.activateWindow()
            self.main_ref.setFocus()
            
            # Sensor page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    print(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _open_positioning(self) -> None:
        if self.main_ref:
            if not hasattr(self.main_ref, '_positioning_page') or self.main_ref._positioning_page is None:
                from .pyside_positioning import PositioningPage
                self.main_ref._positioning_page = PositioningPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            
            # Positioning widget'ını direkt göster
            self.main_ref._positioning_page.set_active_nav("btnPositioning_2")
            self.main_ref._positioning_page.showFullScreen()
            
            # Sensor page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    print(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _open_monitoring(self) -> None:
        if self.main_ref:
            if not hasattr(self.main_ref, '_monitoring_page') or self.main_ref._monitoring_page is None:
                from .pyside_monitoring import MonitoringPage
                self.main_ref._monitoring_page = MonitoringPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            
            # Monitoring widget'ını direkt göster
            self.main_ref._monitoring_page.set_active_nav("btnTracking")
            self.main_ref._monitoring_page.showFullScreen()
            
            # Sensor page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    print(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _open_camera(self) -> None:
        if self.main_ref:
            if not hasattr(self.main_ref, '_camera_page') or self.main_ref._camera_page is None:
                from .pyside_camera import CameraPage
                self.main_ref._camera_page = CameraPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            
            # Camera widget'ını direkt göster
            self.main_ref._camera_page.set_active_nav("btnCamera")
            self.main_ref._camera_page.showFullScreen()
            
            # Sensor page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    print(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _open_sensor(self) -> None:
        # already here
        self.showFullScreen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            if hasattr(self, '_bg_label') and self._bg_label:
                self._bg_label.setGeometry(0, 0, self.width(), self.height())
        except Exception:
            pass

    def _update_datetime_labels(self) -> None:
        now = QDateTime.currentDateTime()
        if hasattr(self.ui, 'labelDate'):
            self.ui.labelDate.setText(now.toString('dd.MM.yyyy dddd'))
        if hasattr(self.ui, 'labelTime'):
            self.ui.labelTime.setText(now.toString('HH:mm')) 

    # ---- Data path
    def _on_data_tick(self) -> None:
        try:
            data = self.get_data_callback() if self.get_data_callback else None
            if not data or not isinstance(data, dict):
                return
            self._update_sensor_values(data)
        except Exception:
            pass

    # ---- Anomaly logic (UI-thread only)
    def _set_all_frames_green(self) -> None:
        green_style = (
            """
            QFrame {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0,
                    x2:1, y2:1,
                    stop:0 rgba(0, 0, 0, 255),
                    stop:0.480769 rgba(9, 139, 7, 255),
                    stop:1 rgba(9, 139, 7, 255)
                );
                border-radius: 20px;
            }
            """
        )
        for name in (
            'KesmeHiziFrame','IlerlemeHiziFrame','SeritAkimFrame','SicaklikFrame','NemFrame',
            'SeritSapmasiFrame','TitresimXFrame','TitresimYFrame','TitresimZFrame'
        ):
            frame = getattr(self.ui, name, None)
            if frame:
                frame.setStyleSheet(green_style)

    def _set_all_info_labels(self, text: str) -> None:
        for name in (
            'labelKesmeHiziInfo','labelIlerlemeHiziInfo','labelSeritAkimInfo','labelSicaklikInfo','labelNemInfo',
            'labelSeritSapmasiInfo','labelTitresimXInfo','labelTitresimYInfo','labelTitresimZInfo'
        ):
            lbl = getattr(self.ui, name, None)
            if lbl:
                lbl.setText(text)

    def reset_anomaly_states(self) -> None:
        for key in self.anomaly_states:
            self.anomaly_states[key] = False
        self._set_all_frames_green()
        self._set_all_info_labels("Her şey yolunda.")

    def _update_sensor_values(self, data: Dict) -> None:
        try:
            # Use safe conversions
            def _f(val, default=0.0):
                try:
                    return float(val)
                except Exception:
                    return default

            current_time = datetime.now().strftime('%d.%m.%Y')

            # Thresholds and frame updates
            serit_akim = _f(data.get('serit_motor_akim_a', 0))
            ilerleme_hizi = _f(data.get('serit_inme_hizi', 0))
            serit_sapmasi = _f(data.get('serit_sapmasi', 0))
            vib_x = _f(data.get('ivme_olcer_x_hz', 0))
            vib_y = _f(data.get('ivme_olcer_y_hz', 0))
            vib_z = _f(data.get('ivme_olcer_z_hz', 0))
            sicaklik = _f(data.get('ortam_sicakligi_c', 0))
            nem = _f(data.get('ortam_nem_percentage', 0))
            
            # Kesim grafiği için veri güncelleme
            self._update_cutting_graph(data)

            red_style = (
                """
                QFrame {
                    background: qlineargradient(
                        spread:pad, x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(0, 0, 0, 255), stop:1 rgba(124, 4, 66, 255)
                    );
                    border-radius: 20px;
                }
                """
            )
            green_style = (
                """
                QFrame {
                    background: qlineargradient(
                        spread:pad,
                        x1:0, y1:0,
                        x2:1, y2:1,
                        stop:0 rgba(0, 0, 0, 255),
                        stop:0.480769 rgba(9, 139, 7, 255),
                        stop:1 rgba(9, 139, 7, 255)
                    );
                    border-radius: 20px;
                }
                """
            )

            def upd(frame_name: str, label_name: str, is_anom: bool, ok_text: str = "Her şey yolunda."):
                frame = getattr(self.ui, frame_name, None)
                label = getattr(self.ui, label_name, None)
                if frame:
                    frame.setStyleSheet(red_style if is_anom else green_style)
                if label:
                    label.setText(f"{current_time} tarihinde anomali tespit edildi.") if is_anom else label.setText(ok_text)

            # Rules (same as legacy)
            upd('KesmeHiziFrame','labelKesmeHiziInfo', serit_akim > 100 or self.anomaly_states['KesmeHizi'])
            self.anomaly_states['KesmeHizi'] |= (serit_akim > 100)

            upd('IlerlemeHiziFrame','labelIlerlemeHiziInfo', ilerleme_hizi < 100 or self.anomaly_states['IlerlemeHizi'])
            self.anomaly_states['IlerlemeHizi'] |= (ilerleme_hizi < 100)

            upd('SeritAkimFrame','labelSeritAkimInfo', serit_akim > 15 or self.anomaly_states['SeritAkim'])
            self.anomaly_states['SeritAkim'] |= (serit_akim > 15)

            upd('SicaklikFrame','labelSicaklikInfo', sicaklik > 40 or self.anomaly_states['Sicaklik'])
            self.anomaly_states['Sicaklik'] |= (sicaklik > 40)

            upd('NemFrame','labelNemInfo', nem > 80 or self.anomaly_states['Nem'])
            self.anomaly_states['Nem'] |= (nem > 80)

            upd('SeritSapmasiFrame','labelSeritSapmasiInfo', abs(serit_sapmasi) > 0.5 or self.anomaly_states['SeritSapmasi'])
            self.anomaly_states['SeritSapmasi'] |= (abs(serit_sapmasi) > 0.5)

            upd('TitresimXFrame','labelTitresimXInfo', vib_x > 200 or self.anomaly_states['TitresimX'])
            self.anomaly_states['TitresimX'] |= (vib_x > 200)

            upd('TitresimYFrame','labelTitresimYInfo', vib_y > 200 or self.anomaly_states['TitresimY'])
            self.anomaly_states['TitresimY'] |= (vib_y > 200)

            upd('TitresimZFrame','labelTitresimZInfo', vib_z > 200 or self.anomaly_states['TitresimZ'])
            self.anomaly_states['TitresimZ'] |= (vib_z > 200)
        except Exception:
            # swallow to keep UI responsive
            pass

    def _update_cutting_graph(self, data: Dict) -> None:
        """Kesim grafiğini günceller"""
        try:
            if not self.cutting_graph:
                return
            
            # Testere durumunu kontrol et
            testere_durumu = data.get('testere_durumu', 0)
            
            # Kesim başladı mı kontrol et
            if testere_durumu == 3:  # KESIM_YAPILIYOR
                if not self.is_cutting:
                    # Kesim başladı
                    self.is_cutting = True
                    self.cut_start_time = datetime.now()
                    # Zaman etiketleri için başlangıç saatini grafiğe aktar
                    self.cutting_graph.cut_start_time = self.cut_start_time
                    self.cutting_graph.last_point_time = self.cut_start_time
                    # Yükseklik için başlangıç değeri, ilk paket geldiğinde set edilecek
                    self.cutting_graph.start_height_value = None
                    self.cutting_graph.current_height_value = None
                    self.last_cut_data = []
                    self.current_cut_buffer = []
                    self.cutting_graph.clear_data()
                    # Gerçek zamanlı grafiği yeniden başlat
                    try:
                        if self.cutting_graph and not self.cutting_graph.update_timer.isActive():
                            self.cutting_graph.update_timer.start(100)
                    except Exception:
                        pass
                    logger.info("Kesim başladı - grafik verileri temizlendi")
                
                # Kesim sırasında veri topla
                self._add_cutting_data_point(data)
                
            elif testere_durumu != 3 and self.is_cutting:
                # Kesim bitti
                self.is_cutting = False
                # Başlangıç saatini koru, son kesim görünsün
                logger.info("Kesim bitti")
                # Gerçek zamanlı grafiği durdur (son kesimi göster)
                try:
                    if self.cutting_graph and self.cutting_graph.update_timer.isActive():
                        self.cutting_graph.update_timer.stop()
                except Exception:
                    pass
                
        except Exception as e:
            logger.error(f"Kesim grafiği güncelleme hatası: {e}")

    def _add_cutting_data_point(self, data: Dict) -> None:
        """Kesim sırasında veri noktası ekler"""
        try:
            if not self.cutting_graph or not self.is_cutting:
                return
            
            # Buffer'a tüm metrikleri ekle
            now_dt = datetime.now()
            elapsed_s = (now_dt - self.cut_start_time).total_seconds() if self.cut_start_time else 0.0
            buffer_row = {
                'timestamp_dt': now_dt,
                'elapsed_s': float(elapsed_s),
                'serit_kesme_hizi': float(data.get('serit_kesme_hizi', 0.0)),
                'serit_inme_hizi': float(data.get('serit_inme_hizi', 0.0)),
                'serit_motor_akim_a': float(data.get('serit_motor_akim_a', 0.0)),
                'serit_sapmasi': float(data.get('serit_sapmasi', 0.0)),
                'serit_motor_tork_percentage': float(data.get('serit_motor_tork_percentage', 0.0)),
                'kafa_yuksekligi_mm': float(data.get('kafa_yuksekligi_mm', 0.0)),
                'ivme_olcer_x_hz': float(data.get('ivme_olcer_x_hz', 0.0)),
                'ivme_olcer_y_hz': float(data.get('ivme_olcer_y_hz', 0.0)),
                'ivme_olcer_z_hz': float(data.get('ivme_olcer_z_hz', 0.0)),
            }
            self.current_cut_buffer.append(buffer_row)

            # Yükseklik ekseni etiketleri için başlangıç/mevcut değerleri güncelle
            try:
                h = buffer_row['kafa_yuksekligi_mm']
                if self.cutting_graph.start_height_value is None:
                    self.cutting_graph.start_height_value = h
                self.cutting_graph.current_height_value = h
            except Exception:
                pass

            # Seçili eksenlere göre son noktayı grafiğe ekle
            x_axis = self.cutting_graph.x_axis_type
            y_axis = self.cutting_graph.y_axis_type

            x_value = self._get_value_for_axis_from_buffer(buffer_row, x_axis)
            y_value = self._get_value_for_axis_from_buffer(buffer_row, y_axis)

            self.cutting_graph.add_data_point(float(x_value), float(y_value))
            
            # Son kesim verilerini sakla
            self.last_cut_data.append({
                'timestamp': datetime.now(),
                'x_value': x_value,
                'y_value': y_value,
                'x_axis': x_axis,
                'y_axis': y_axis
            })
            
        except Exception as e:
            logger.error(f"Veri noktası ekleme hatası: {e}")

    def _get_value_for_axis_from_buffer(self, row: Dict, axis_type: str) -> float:
        """Buffer satırından eksen değerini döndürür"""
        try:
            if axis_type == "timestamp":
                return float(row.get('elapsed_s', 0.0))
            elif axis_type == "serit_kesme_hizi":
                return float(row.get('serit_kesme_hizi', 0.0))
            elif axis_type == "serit_inme_hizi":
                return float(row.get('serit_inme_hizi', 0.0))
            elif axis_type == "serit_motor_akim_a":
                return float(row.get('serit_motor_akim_a', 0.0))
            elif axis_type == "serit_sapmasi":
                return float(row.get('serit_sapmasi', 0.0))
            elif axis_type == "serit_motor_tork_percentage":
                return float(row.get('serit_motor_tork_percentage', 0.0))
            elif axis_type == "kafa_yuksekligi_mm":
                return float(row.get('kafa_yuksekligi_mm', 0.0))
            else:
                return 0.0
        except Exception:
            return 0.0

    def _rebuild_graph_from_buffer(self) -> None:
        """Buffer'daki mevcut/son kesimi, seçili eksenlere göre yeniden çizer"""
        try:
            if not self.cutting_graph or not self.current_cut_buffer:
                return
            # Grafiği temizle
            self.cutting_graph.clear_data()

            x_axis = self.cutting_graph.x_axis_type
            y_axis = self.cutting_graph.y_axis_type

            # Zaman etiketleri için başlangıç/son
            if self.cut_start_time:
                self.cutting_graph.cut_start_time = self.cut_start_time
            first_dt = self.current_cut_buffer[0].get('timestamp_dt', None)
            last_dt = self.current_cut_buffer[-1].get('timestamp_dt', None)
            if first_dt and last_dt:
                self.cutting_graph.cut_start_time = first_dt
                self.cutting_graph.last_point_time = last_dt
            # Yükseklik için başlangıç/mevcut değerleri buffer'dan belirle
            try:
                first_h = self.current_cut_buffer[0].get('kafa_yuksekligi_mm', None)
                last_h = self.current_cut_buffer[-1].get('kafa_yuksekligi_mm', None)
                if first_h is not None and last_h is not None:
                    self.cutting_graph.start_height_value = float(first_h)
                    self.cutting_graph.current_height_value = float(last_h)
            except Exception:
                pass

            for row in self.current_cut_buffer:
                x_value = self._get_value_for_axis_from_buffer(row, x_axis)
                y_value = self._get_value_for_axis_from_buffer(row, y_axis)
                self.cutting_graph.add_data_point(float(x_value), float(y_value))
            
            logger.info("Grafik buffer'dan yeniden çizildi")
            # Yeniden çiz
            try:
                self.cutting_graph.update()
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Buffer'dan grafik çizim hatası: {e}")

    def _load_last_cut_data(self):
        """Son kesim verilerini veritabanından yükler - sadece kesim yapılmıyor ise"""
        try:
            # Eğer şu anda kesim yapılıyorsa, geçmiş verileri yükleme
            if self.is_cutting:
                logger.info("Kesim devam ediyor, geçmiş veri yüklenmeyecek")
                return
                
            if not self.cutting_graph or not self.db:
                logger.warning("Grafik widget veya veritabanı bağlantısı yok")
                return
            
            # Grafiği temizle
            self.cutting_graph.clear_data()
            logger.info("Grafik temizlendi")
            
            # Geçmiş veri yüklemesi öncesi hazırlık
            self._prepare_for_historical_data_load()
            
            # Son kesim verilerini al
            data = self._get_last_cut_data_from_db()
            if not data:
                logger.warning("Son kesim verisi bulunamadı")
                return
            
            logger.info(f"Veritabanından {len(data)} veri satırı alındı")
            
            # Seçili eksenlere göre verileri grafiğe ekle
            x_axis = self.cutting_graph.x_axis_type
            y_axis = self.cutting_graph.y_axis_type
            
            logger.info(f"Seçili eksenler - X: {x_axis}, Y: {y_axis}")
            
            added_points = 0
            # Zaman etiketleri için başlangıç/son zamanlarını hesapla
            start_dt = None
            end_dt = None
            
            # Veriyi kronolojik sıraya çevir (en eski önce olacak şekilde)
            data_sorted = sorted(data, key=lambda x: x.get('timestamp', ''))
            
            for i, row in enumerate(data_sorted):
                x_value = self._get_value_for_axis(row, x_axis)
                y_value = self._get_value_for_axis(row, y_axis)
                
                logger.debug(f"Veri {i}: X={x_value}, Y={y_value}")
                
                if x_value is not None and y_value is not None:
                    self.cutting_graph.add_data_point(x_value, y_value)
                    added_points += 1
                    
                # Zaman alanını oku
                try:
                    ts = row.get('timestamp')
                    if ts:
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        if start_dt is None or dt < start_dt:
                            start_dt = dt
                        if end_dt is None or dt > end_dt:
                            end_dt = dt
                except Exception:
                    pass
            
            logger.info(f"Son kesim verisi yüklendi: {added_points} nokta grafiğe eklendi")
            
            # Zaman ekseni seçiliyse etiketler için süreleri ata
            if self.cutting_graph.x_axis_type == "timestamp" and start_dt and end_dt:
                self.cutting_graph.cut_start_time = start_dt
                self.cutting_graph.last_point_time = end_dt
            
            # Yükseklik ekseni için başlangıç/mevcut değerleri ata
            if self.cutting_graph.x_axis_type == "kafa_yuksekligi_mm" and data_sorted:
                try:
                    start_height = self._get_value_for_axis(data_sorted[0], "kafa_yuksekligi_mm")
                    end_height = self._get_value_for_axis(data_sorted[-1], "kafa_yuksekligi_mm")
                    if start_height is not None and end_height is not None:
                        self.cutting_graph.start_height_value = float(start_height)
                        self.cutting_graph.current_height_value = float(end_height)
                except Exception:
                    pass
            
        except Exception as e:
            logger.error(f"Son kesim verisi yükleme hatası: {e}")
            import traceback
            logger.error(f"Detaylı hata: {traceback.format_exc()}")

    def _get_last_cut_data_from_db(self):
        """Veritabanından son kesim aralığının verilerini alır"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok")
                return None
            
            cursor = self.db.cursor()
            
            # Önce testere_durumu 3 olan son kesim aralığını bul
            # Son kesim bloğunun başlangıç ve bitiş zamanlarını tespit et
            find_last_cut_query = """
                WITH cutting_sessions AS (
                    SELECT 
                        timestamp,
                        testere_durumu,
                        LAG(testere_durumu) OVER (ORDER BY timestamp) as prev_durumu
                    FROM testere_data 
                    WHERE timestamp IS NOT NULL
                    ORDER BY timestamp
                ),
                session_boundaries AS (
                    SELECT 
                        timestamp,
                        testere_durumu,
                        CASE 
                            WHEN testere_durumu = 3 AND (prev_durumu != 3 OR prev_durumu IS NULL) THEN 'START'
                            WHEN testere_durumu != 3 AND prev_durumu = 3 THEN 'END'
                            ELSE NULL 
                        END as boundary_type
                    FROM cutting_sessions
                ),
                last_session AS (
                    SELECT 
                        MAX(CASE WHEN boundary_type = 'START' THEN timestamp END) as session_start
                    FROM session_boundaries
                )
                SELECT session_start FROM last_session WHERE session_start IS NOT NULL
            """
            
            result = cursor.execute(find_last_cut_query).fetchone()
            
            if not result or not result[0]:
                logger.warning("Son kesim oturumu bulunamadı")
                return None
                
            last_cut_start = result[0]
            logger.info(f"Son kesim başlangıcı: {last_cut_start}")
            
            # Son kesim oturumunun bitişini bul
            find_cut_end_query = """
                SELECT MIN(timestamp) as cut_end
                FROM testere_data 
                WHERE timestamp > ? AND testere_durumu != 3
            """
            
            end_result = cursor.execute(find_cut_end_query, (last_cut_start,)).fetchone()
            last_cut_end = end_result[0] if end_result and end_result[0] else None
            
            if last_cut_end:
                logger.info(f"Son kesim bitişi: {last_cut_end}")
                # Belirli bir aralıktaki verileri al
                data_query = """
                    SELECT 
                        timestamp,
                        serit_motor_akim_a,
                        inme_motor_akim_a,
                        kafa_yuksekligi_mm,
                        serit_kesme_hizi,
                        serit_inme_hizi,
                        serit_sapmasi,
                        serit_motor_tork_percentage,
                        ivme_olcer_x_hz,
                        ivme_olcer_y_hz,
                        ivme_olcer_z_hz
                    FROM testere_data
                    WHERE timestamp >= ? AND timestamp < ?
                    AND testere_durumu = 3
                    ORDER BY timestamp ASC
                """
                data_params = (last_cut_start, last_cut_end)
            else:
                # Eğer kesim bitişi bulunamadıysa, başlangıçtan itibaren tüm kesim verilerini al
                logger.info("Kesim bitişi bulunamadı, başlangıçtan itibaren alınıyor")
                data_query = """
                    SELECT 
                        timestamp,
                        serit_motor_akim_a,
                        inme_motor_akim_a,
                        kafa_yuksekligi_mm,
                        serit_kesme_hizi,
                        serit_inme_hizi,
                        serit_sapmasi,
                        serit_motor_tork_percentage,
                        ivme_olcer_x_hz,
                        ivme_olcer_y_hz,
                        ivme_olcer_z_hz
                    FROM testere_data
                    WHERE timestamp >= ?
                    AND testere_durumu = 3
                    ORDER BY timestamp ASC
                    LIMIT 1000
                """
                data_params = (last_cut_start,)
            
            result = cursor.execute(data_query, data_params).fetchall()
            logger.info(f"Son kesim aralığından {len(result)} kayıt bulundu")
            
            if not result:
                logger.warning("Son kesim aralığında veri bulunamadı")
                return None

            # Verileri sözlük formatına dönüştür
            data = []
            for i, row in enumerate(result):
                data.append({
                    'timestamp': row[0],
                    'serit_motor_akim_a': float(row[1]) if row[1] is not None else 0.0,
                    'inme_motor_akim_a': float(row[2]) if row[2] is not None else 0.0,
                    'kafa_yuksekligi_mm': float(row[3]) if row[3] is not None else 0.0,
                    'serit_kesme_hizi': float(row[4]) if row[4] is not None else 0.0,
                    'serit_inme_hizi': float(row[5]) if row[5] is not None else 0.0,
                    'serit_sapmasi': float(row[6]) if row[6] is not None else 0.0,
                    'serit_motor_tork_percentage': float(row[7]) if row[7] is not None else 0.0,
                    'ivme_olcer_x_hz': float(row[8]) if row[8] is not None else 0.0,
                    'ivme_olcer_y_hz': float(row[9]) if row[9] is not None else 0.0,
                    'ivme_olcer_z_hz': float(row[10]) if row[10] is not None else 0.0
                })
                
                # İlk birkaç kaydı log'la
                if i < 3:
                    logger.info(f"Örnek veri {i}: timestamp={row[0]}, kesme_hızı={row[4]}")
            
            logger.info(f"Toplam {len(data)} veri satırı hazırlandı")
            return data

        except Exception as e:
            logger.error(f"Veritabanından veri alma hatası: {e}")
            import traceback
            logger.error(f"Detaylı hata: {traceback.format_exc()}")
            return None

    def _get_value_for_axis(self, data_row, axis_type):
        """Veri satırından belirtilen eksen için değeri döndürür"""
        try:
            if axis_type == "serit_kesme_hizi":
                return data_row.get('serit_kesme_hizi', 0.0)
            elif axis_type == "serit_inme_hizi":
                return data_row.get('serit_inme_hizi', 0.0)
            elif axis_type == "serit_motor_akim_a":
                return data_row.get('serit_motor_akim_a', 0.0)
            elif axis_type == "serit_sapmasi":
                return data_row.get('serit_sapmasi', 0.0)
            elif axis_type == "serit_motor_tork_percentage":
                return data_row.get('serit_motor_tork_percentage', 0.0)
            elif axis_type == "kafa_yuksekligi_mm":
                return data_row.get('kafa_yuksekligi_mm', 0.0)
            elif axis_type == "timestamp":
                # Zaman için elapsed time hesapla (ilk veri noktasından itibaren geçen süre)
                try:
                    timestamp_str = data_row.get('timestamp', '')
                    if timestamp_str and hasattr(self, '_first_timestamp_for_axis'):
                        if not hasattr(self, '_first_timestamp_for_axis') or self._first_timestamp_for_axis is None:
                            # İlk timestamp'i kaydet
                            self._first_timestamp_for_axis = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            return 0.0
                        else:
                            # Geçen süreyi hesapla (saniye cinsinden)
                            current_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            elapsed_seconds = (current_dt - self._first_timestamp_for_axis).total_seconds()
                            return float(elapsed_seconds)
                    return 0.0
                except Exception as e:
                    logger.error(f"Timestamp dönüşüm hatası: {e}")
                    return 0.0
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Eksen değeri alma hatası: {e}")
            return 0.0

    # _get_last_cut_data_from_db metodunu çağırmadan önce timestamp referansını sıfırla
    def _prepare_for_historical_data_load(self):
        """Geçmiş veri yüklemesi öncesi hazırlık"""
        self._first_timestamp_for_axis = None 