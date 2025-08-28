from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap
from .qt_camera_interface import Ui_MainWindow
from typing import Dict, Callable, Optional, List
from datetime import datetime
from core.camera import CameraModule
import os
import json
import cv2
from core.constants import TestereState

class CameraWindow(QMainWindow):
    _camera_module_instance = None  # Singleton CameraModule

    def __init__(self, parent=None, get_data_callback: Callable[[], Dict] = None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.parent = parent
        self.get_data_callback = get_data_callback
        self.monitoring_window = None
        self.sensor_window = None
        
        # Singleton pattern için CameraModule
        if CameraWindow._camera_module_instance is None:
            CameraWindow._camera_module_instance = CameraModule()
        self.camera_module = CameraWindow._camera_module_instance
        self.camera_module.set_detection_finish_callback(self.detection_bitti_callback)

        # Navigation butonları için icon mapping
        self.nav_buttons = {
            'btnControlPanel': (QIcon("src/gui/images/control-panel-icon2.svg"), QIcon("src/gui/images/control-panel-icon2-active.svg")),
            'btnPositioning': (QIcon("src/gui/images/positioning-icon2.svg"), QIcon("src/gui/images/positioning-icon2-active.svg")),
            'btnCamera': (QIcon("src/gui/images/camera-icon2.svg"), QIcon("src/gui/images/camera-icon-active.svg")),
            'btnSensor': (QIcon("src/gui/images/sensor-icon2.svg"), QIcon("src/gui/images/sensor-icon2-active.svg")),
            'btnTracking': (QIcon("src/gui/images/tracking-icon2.svg"), QIcon("src/gui/images/tracking-icon2-active.svg")),
        }

        # Label mapping for data updates
        self.label_data_mapping = {
            'labelTestereSagligiValue': 'testere_sagligi',
            'labelAsinmaYuzdesiValue': 'asinma_yuzdesi',
            'labelTestereDurumuValue': 'testere_durumu',
            'labelTespitEdilenKirikValue': 'tespit_edilen_kirik',
            'labelTespitEdilenDisValue': 'tespit_edilen_dis',
        }

        # Frame öncelik sırası
        self.frame_priority = ['broken', 'tooth']
        
        # Recordings directory cache
        self._recordings_dir = os.path.join(os.getcwd(), "recordings")
        self._detection_was_running = False

        self._setup_ui_components()
        self._connect_signals()
        self._setup_timers()
        self.set_active_nav("btnCamera")

        # Başlangıç durumu
        self.ui.labelKirikTespitInfo.setText("Kırık tespit edilmedi.")
        self.ui.KirikTespitiInfoFrame.setStyleSheet("QFrame {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(9, 139, 7, 255), stop:1 rgba(9, 139, 7, 255)); border-radius: 20px;}")

    def _setup_ui_components(self):
        """UI bileşenlerini ayarla"""
        # KameraFrame içinde QLabel oluştur
        self.camera_label = QLabel(self.ui.KameraFrame)
        self.camera_label.setGeometry(0, 0, self.ui.KameraFrame.width(), self.ui.KameraFrame.height())
        self.camera_label.setScaledContents(True)
        self.camera_label.setStyleSheet("background: transparent;")
        self.camera_label.lower()  # En alta gönder
        self.camera_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Mouse eventlerini yutmasın

    def _connect_signals(self):
        """Signal-slot bağlantılarını kur"""
        # Navigation butonları
        self.ui.btnControlPanel.clicked.connect(self.open_control_panel)
        self.ui.btnTracking.clicked.connect(self.open_monitoring_window)
        self.ui.btnSensor.clicked.connect(self.open_sensor_window)
        self.ui.btnCamera.clicked.connect(self.open_camera_window)
        
        # Kamera kontrolü
        self.ui.kameraOnOffButton.toggled.connect(self.toggle_camera_stream)

    def _setup_timers(self):
        """Timer'ları ayarla"""
        # Kamera stream timer
        self.camera_stream_timer = QTimer(self)
        self.camera_stream_timer.timeout.connect(self.update_camera_frame)
        self.camera_stream_timer.start(300)  # 300ms'de bir frame güncelle

        # Periyodik güncelleme timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.periodic_update)
        self.timer.start(1000)  # Her saniye güncelle
        self.periodic_update()  # İlk açılışta hemen güncelle

    def detection_bitti_callback(self):
        # Detection thread'i bittiğinde çağrılır, label ve frame'i günceller
        stats = self.camera_module.get_last_detection_stats()
        info_label = self.ui.labelKirikTespitInfo
        info_frame = self.ui.KirikTespitiInfoFrame
        from datetime import datetime
        if stats:
            total_broken = stats.get('total_broken', 0)
            timestamp_str = stats.get('timestamp', datetime.now().strftime('%d.%m.%Y'))
            try:
                dt_object = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                formatted_date = dt_object.strftime('%d.%m.%Y')
            except ValueError:
                formatted_date = timestamp_str.split(' ')[0]
            if total_broken > 0:
                info_frame.setStyleSheet("QFrame {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(124, 4, 66, 255), stop:1 rgba(124, 4, 66, 255)); border-radius: 20px;}")
                info_label.setText(f"{formatted_date} tarihinde {total_broken} kırık tespit edildi.")
            else:
                info_frame.setStyleSheet("QFrame {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(9, 139, 7, 255), stop:1 rgba(9, 139, 7, 255)); border-radius: 20px;}")
                info_label.setText("Her şey yolunda.")

    def periodic_update(self):
        """Periyodik UI güncellemelerini yap"""
        # Saat ve tarihi güncelle
        now = datetime.now()
        self.ui.labelDate.setText(now.strftime('%d.%m.%Y %A'))
        self.ui.labelTime.setText(now.strftime('%H:%M'))
        
        # Verileri güncelle
        if self.get_data_callback:
            data = self.get_data_callback()
            if data:
                self.update_ui(data)
                # Detection kontrolü
                testere_durumu_raw = data.get('testere_durumu', 0)
                try:
                    testere_durumu = int(testere_durumu_raw)
                except (ValueError, TypeError):
                    str_to_val = {
                        'BOŞTA': TestereState.BOSTA.value,
                        'HİDROLİK AKTİF': TestereState.HIDROLIK_AKTIF.value,
                        'ŞERİT MOTOR ÇALIŞIYOR': TestereState.SERIT_MOTOR_CALISIYOR.value,
                        'KESİM YAPILIYOR': TestereState.KESIM_YAPILIYOR.value,
                        'KESİM BİTTİ': TestereState.KESIM_BITTI.value,
                        'ŞERİT YUKARI ÇIKIYOR': TestereState.SERIT_YUKARI_CIKIYOR.value,
                        'MALZEME BESLEME': TestereState.MALZEME_BESLEME.value
                    }
                    testere_durumu = str_to_val.get(str(testere_durumu_raw).strip().upper(), 0)
                allowed_states = [
                    TestereState.KESIM_YAPILIYOR.value,
                    TestereState.KESIM_BITTI.value,
                    TestereState.SERIT_YUKARI_CIKIYOR.value
                ]
                if testere_durumu in allowed_states:
                    if not self.camera_module.is_detecting:
                        self.camera_module.start_detection(on_finish=self.detection_bitti_callback)
                else:
                    self.camera_module.stop_detection()

    def set_active_nav(self, active_btn_name: str):
        """Navigation butonlarının aktif/pasif durumunu ayarla"""
        for btn_name, (passive_icon, active_icon) in self.nav_buttons.items():
            btn = getattr(self.ui, btn_name, None)
            if btn:
                icon = active_icon if btn_name == active_btn_name else passive_icon
                btn.setIcon(icon)

    def _show_window(self, window_class, window_attr: str, nav_btn: str):
        """Ortak pencere gösterme fonksiyonu"""
        window = getattr(self, window_attr)
        if window is None or not window.isVisible():
            setattr(self, window_attr, window_class(parent=self.parent, get_data_callback=self.get_data_callback))
            window = getattr(self, window_attr)
        
        self.hide()
        window.set_active_nav(nav_btn)
        window.showFullScreen()

    def open_control_panel(self):
        """Kontrol panelini aç"""
        if self.parent:
            self.hide()
            self.parent.set_active_nav("btnControlPanel")
            self.parent.showFullScreen()

    def open_monitoring_window(self):
        """İzleme penceresini aç"""
        from .monitoring_controller import MonitoringWindow
        self._show_window(MonitoringWindow, 'monitoring_window', 'btnTracking')

    def open_sensor_window(self):
        """Sensör penceresini aç"""
        from .sensor_controller import SensorWindow
        self._show_window(SensorWindow, 'sensor_window', 'btnSensor')

    def open_camera_window(self):
        """Kamera penceresi zaten açık"""
        pass

    def toggle_camera_stream(self, checked: bool):
        """Kamera stream'ini aç/kapat"""
        print(f"toggle_camera_stream: checked={checked}")
        if checked:
            print("Kamera başlatılıyor...")
            self.camera_module.start_viewing()
            self.camera_stream_timer.start(30)  # ~30 FPS
        else:
            print("Kamera durduruluyor...")
            self.camera_module.stop_viewing()
            self.camera_stream_timer.stop()
            self.camera_label.clear()

    def _get_latest_folder(self) -> Optional[str]:
        """En son recordings klasörünü bul"""
        if not os.path.exists(self._recordings_dir):
            return None
            
        folders = [f for f in os.listdir(self._recordings_dir) 
                  if os.path.isdir(os.path.join(self._recordings_dir, f))]
        
        return max(folders) if folders else None

    def _find_priority_frame(self, detected_frames: List[str], detected_dir: str) -> Optional[str]:
        """Öncelik sırasına göre frame bul"""
        # Öncelik sırasına göre frame ara
        for priority_keyword in self.frame_priority:
            for fname in detected_frames:
                if priority_keyword in fname:
                    return os.path.join(detected_dir, fname)
        
        # Hiçbiri yoksa ilk frame
        return os.path.join(detected_dir, detected_frames[0]) if detected_frames else None

    def _load_stats_file(self, stats_path: str) -> Optional[dict]:
        """Stats dosyasını yükle"""
        if not os.path.exists(stats_path):
            return None
            
        try:
            with open(stats_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Stats dosyası okuma hatası: {e}")
            return None

    def _get_latest_detection_data(self) -> tuple[Optional[str], Optional[dict]]:
        """En son detection verilerini al"""
        latest_folder = self._get_latest_folder()
        if not latest_folder:
            return None, None

        folder_path = os.path.join(self._recordings_dir, latest_folder)
        detected_dir = os.path.join(folder_path, "detected")
        
        # Frame path bul
        frame_path = None
        if os.path.exists(detected_dir):
            detected_frames = [f for f in sorted(os.listdir(detected_dir)) if f.endswith('.jpg')]
            frame_path = self._find_priority_frame(detected_frames, detected_dir)

        # Stats yükle
        stats_file = os.path.join(folder_path, "detection_stats.json")
        stats = self._load_stats_file(stats_file)
        
        return frame_path, stats

    def _load_and_display_frame(self, frame_path: str):
        """Frame'i yükle ve göster"""
        if not os.path.exists(frame_path):
            self.camera_label.clear()
            return

        try:
            frame = cv2.imread(frame_path)
            if frame is None:
                self.camera_label.clear()
                return

            # BGR'dan RGB'ye çevir
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # QImage ve QPixmap oluştur
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            self.camera_label.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Frame yükleme hatası: {e}")
            self.camera_label.clear()

    def update_camera_frame(self):
        """Kamera frame'ini güncelle"""
        # En son detection verilerini al
        frame_path, stats = self._get_latest_detection_data()
        
        # UI verilerini hazırla
        processed_data = {
            'tespit_edilen_dis': stats.get("total_tooth", "-") if stats else "-",
            'tespit_edilen_kirik': stats.get("total_broken", "-") if stats else "-"
        }
        
        # UI'ı güncelle
        self.update_ui(processed_data)
        
        # Frame'i göster
        if frame_path:
            self._load_and_display_frame(frame_path)
        else:
            self.camera_label.clear()

    def _get_stats_from_recordings(self) -> Optional[dict]:
        """Recordings klasöründen stats al - DRY için tekrar kullanımı"""
        latest_folder = self._get_latest_folder()
        if not latest_folder:
            return None
            
        stats_file = os.path.join(self._recordings_dir, latest_folder, "detection_stats.json")
        return self._load_stats_file(stats_file)

    def _update_values(self, processed_data: Dict):
        """Değerleri güncelle"""
        try:
            # Recordings'dan stats al
            stats = self._get_stats_from_recordings()
            
            for label_name, data_key in self.label_data_mapping.items():
                value = processed_data.get(data_key, '-')
                
                # Stats'tan özel değerleri al
                if stats:
                    if label_name == 'labelTespitEdilenDisValue':
                        value = stats.get("total_tooth", '-')
                    elif label_name == 'labelTespitEdilenKirikValue':
                        value = stats.get("total_broken", '-')
                
                # Label'ı güncelle
                label_widget = getattr(self.ui, label_name, None)
                if label_widget:
                    label_widget.setText(str(value))

            # Detection durumu kontrolü
            if self.camera_module.is_detecting:
                self._detection_was_running = True
            else:
                if self._detection_was_running:
                    # Detection yeni bitti, stats oku ve label güncelle
                    stats = self.camera_module.get_last_detection_stats()
                    info_label = self.ui.labelKirikTespitInfo
                    info_frame = self.ui.KirikTespitiInfoFrame
                    if stats:
                        total_broken = stats.get('total_broken', 0)
                        timestamp_str = stats.get('timestamp', datetime.now().strftime('%d.%m.%Y'))
                        try:
                            # Tarih formatını dd.mm.YYYY'ye çevir
                            dt_object = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            formatted_date = dt_object.strftime('%d.%m.%Y')
                        except ValueError:
                            formatted_date = timestamp_str.split(' ')[0]


                        if total_broken > 0:
                            # Kırmızı arka plan
                            info_frame.setStyleSheet("QFrame {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(124, 4, 66, 255), stop:1 rgba(124, 4, 66, 255)); border-radius: 20px;}")
                            info_label.setText(f"{formatted_date} tarihinde {total_broken} kırık tespit edildi.")
                        else:
                            # Yeşil arka plan
                            info_frame.setStyleSheet("QFrame {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(9, 139, 7, 255), stop:1 rgba(9, 139, 7, 255)); border-radius: 20px;}")
                            info_label.setText("Her şey yolunda.")
                    self._detection_was_running = False
                    
        except Exception as e:
            print(f"Camera _update_values hata: {e}")

    def update_ui(self, processed_data: Dict):
        """UI'ı güncelle"""
        self._update_values(processed_data)