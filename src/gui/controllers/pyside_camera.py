from typing import Callable, Dict, Optional, List
from PySide6.QtCore import QTimer, Qt, QDateTime
from PySide6.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QIcon, QImage, QPixmap
import os
import json
import csv
import cv2
import random
from datetime import datetime


from gui.ui_files.camera_widget_ui import Ui_Form
from core.camera import CameraModule
from core.constants import TestereState
from core.saw_health_calculator import SawHealthCalculator



class CameraPage(QWidget):
    def __init__(self, main_ref=None, get_data_callback: Optional[Callable[[], Dict]] = None) -> None:
        super().__init__(None)  # top-level window
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.main_ref = main_ref
        self.get_data_callback = get_data_callback
        # Apply same background image as control panel (efficient QLabel)
        self._apply_background()
        
        # Create a QLabel on top of KameraFrame to render images/video
        self.camera_label = QLabel(self.ui.KameraFrame)
        self.camera_label.setGeometry(0, 0, self.ui.KameraFrame.width(), self.ui.KameraFrame.height())
        self.camera_label.setScaledContents(True)
        self.camera_label.setStyleSheet("background: transparent;")
        self.camera_label.lower()
        self.camera_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Camera module (singleton)
        if not hasattr(CameraPage, "_camera_module_instance"):
            CameraPage._camera_module_instance = CameraModule()
        self.camera_module: CameraModule = CameraPage._camera_module_instance
        self.camera_module.set_detection_finish_callback(self._on_detection_finished)

        # Detection/recordings state
        self._recordings_dir = os.path.join(os.getcwd(), "recordings")
        self._detection_was_running = False
        
        # Kırık tespiti rectangle'ları için container
        self._kirik_info_frames = []
        self._kirik_info_labels = []
        
        # Çatlak tespiti rectangle'ları için container
        self._crack_info_frames = []
        self._crack_info_labels = []
        
        # Okey icon'ları için container'lar
        self._kirik_okey_icon = None
        self._crack_okey_icon = None
        
        # Sıralı görüntü sistemi için container
        self._siralı_goruntu_labels = []
        self._max_images = 4  # Tam olarak 4 adet görüntü
        self._image_width = 240  # Her görüntünün genişliği (1920/8)
        self._image_height = 150  # Her görüntünün yüksekliği (1200/8)
        self._siralı_goruntu_loaded = False  # İlk yükleme kontrolü
        self._last_siralı_goruntu_update = 0  # Son güncelleme zamanı

        # Replace sidebar icons
        self._apply_local_icons()

        # Navigation
        self._connect_navigation()

        # Timers (date/time)
        self._datetime_timer = QTimer(self)
        self._datetime_timer.timeout.connect(self._update_datetime_labels)
        self._datetime_timer.start(1000)
        self._update_datetime_labels()

        # Timers (camera frame + periodic data)
        self._camera_stream_timer = QTimer(self)
        self._camera_stream_timer.timeout.connect(self.update_camera_frame)
        # Start a periodic refresh to keep labels in sync even if live stream is off
        self._camera_stream_timer.start(500)

        self._periodic_timer = QTimer(self)
        self._periodic_timer.timeout.connect(self._periodic_update)
        self._periodic_timer.start(1000)
        self._periodic_update()
        
        # Wear calculator timer - her 2 saniyede bir wear değerini güncelle
        self._wear_timer = QTimer(self)
        self._wear_timer.timeout.connect(self._update_wear_percentage)
        self._wear_timer.start(2000)  # 2 saniyede bir
        
        # Kırık tespiti frame güncelleme timer'ı - her 5 saniyede bir güncelle
        self._kirik_frame_timer = QTimer(self)
        self._kirik_frame_timer.timeout.connect(self._update_kirik_frames)
        self._kirik_frame_timer.start(5000)  # 5 saniyede bir
        
        # Wear calculator referansı (main'den gelecek)
        self.wear_calculator = None
        
        # Sıralı görüntü güncelleme timer'ı - her 30 saniyede bir güncelle
        self._siralı_goruntu_timer = QTimer(self)
        self._siralı_goruntu_timer.timeout.connect(self._check_and_update_siralı_goruntu)
        self._siralı_goruntu_timer.start(10000)  # 30 saniyede bir kontrol et

        # Detected büyük önizleme güncelleme timer'ı - 30 saniyede bir
        self._detected_refresh_timer = QTimer(self)
        self._detected_refresh_timer.timeout.connect(self._refresh_detected_preview)
        self._detected_refresh_timer.start(10000)

        # Optional toggle button wiring (safe if not present)
        if hasattr(self.ui, 'kameraOnOffButton'):
            self.ui.kameraOnOffButton.toggled.connect(self._toggle_camera_stream)
            
        # İlk yüklemede recordings klasörünü kontrol et
        self._check_recordings_and_create_frames()
        self._check_recordings_and_create_crack_frames()
        
        # İlk yüklemede sıralı görüntüleri kontrol et
        self._check_and_update_siralı_goruntu()  # İlk yüklemede çalıştır
        
        # Set camera page as active initially
        self.set_active_nav('btnCamera')
        
        # Wear percentage tracking
        self._current_wear_percentage = 0.0
        
        # Saw health calculator
        self.saw_health_calculator = SawHealthCalculator()
        self._current_saw_health = 100.0
        
    def update_wear_percentage(self, wear_percentage: float):
        """Update the wear percentage label with the new value."""
        try:
            self._current_wear_percentage = wear_percentage
            if hasattr(self.ui, 'labelAsinmaYuzdesiValue'):
                self.ui.labelAsinmaYuzdesiValue.setText(f"{wear_percentage:.2f}")
            
            # Wear percentage değiştiğinde saw health'i de güncelle
            self._calculate_and_update_saw_health()
        except Exception as e:
            print(f"Wear percentage güncelleme hatası: {e}")
    
    def _update_wear_percentage(self):
        """Timer-based wear percentage update - uses wear calculator if available."""
        try:
            # Wear calculator varsa onu kullan
            if hasattr(self, 'wear_calculator') and self.wear_calculator:
                latest_average = self.wear_calculator.get_latest_recording_average()
                self.update_wear_percentage(latest_average)
            else:
                # Fallback: En son recording klasöründen wear.csv'yi oku
                latest_folder = self._get_latest_folder()
                if not latest_folder:
                    return
                    
                csv_path = os.path.join(self._recordings_dir, latest_folder, "wear.csv")
                if not os.path.exists(csv_path):
                    return
                    
                # CSV'den wear değerlerini oku ve ortalama hesapla
                wear_values = []
                with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            wear_percent = float(row.get('wear_percent', 0))
                            wear_values.append(wear_percent)
                        except (ValueError, KeyError):
                            continue
                
                if wear_values:
                    average_wear = sum(wear_values) / len(wear_values)
                    self.update_wear_percentage(average_wear)
                    
        except Exception as e:
            print(f"Wear güncelleme hatası: {e}")
    
    def _update_kirik_frames(self):
        """Periyodik olarak kırık tespiti frame'lerini günceller"""
        try:
            # Eğer detection çalışıyorsa frame'leri güncelleme
            if self.camera_module.is_detecting:
                return
            
            # Kırık tespiti frame'lerini yeniden oluştur
            self._check_recordings_and_create_frames()
            self._check_recordings_and_create_crack_frames()
            
        except Exception as e:
            print(f"Kırık frame güncelleme hatası: {e}")
    
    def _calculate_and_update_saw_health(self):
        """Testere sağlığını hesapla ve güncelle."""
        try:
            # En son detection stats'ı al
            stats = self._get_stats_from_recordings()
            if not stats:
                return
            
            detected_teeth = stats.get('total_tooth', 0)
            detected_broken = stats.get('total_broken', 0)
            
            # Testere sağlığını hesapla
            saw_health = self.saw_health_calculator.calculate_saw_health(
                detected_teeth=detected_teeth,
                detected_broken=detected_broken,
                wear_percentage=self._current_wear_percentage
            )
            
            self._current_saw_health = saw_health
            
            # UI'yi güncelle
            if hasattr(self.ui, 'labelTestereSagligiValue'):
                self.ui.labelTestereSagligiValue.setText(f"{saw_health:.2f}")
                
            # Durum metnini de güncelle (opsiyonel)
            health_status = self.saw_health_calculator.get_health_status(saw_health)
            if hasattr(self.ui, 'labelTestereDurumuValue'):
                self.ui.labelTestereDurumuValue.setText(health_status)
                
        except Exception as e:
            print(f"Saw health hesaplama hatası: {e}")

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

    def _open_control_panel(self) -> None:
        if self.main_ref:
            # Control panel'i direkt göster
            self.main_ref.set_active_nav("btnControlPanel")
            self.main_ref.showFullScreen()
            self.main_ref.raise_()
            self.main_ref.activateWindow()
            self.main_ref.setFocus()
            
            # Camera page'i 500ms sonra gizle (flaş efektini engellemek için)
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
            
            # Camera page'i 500ms sonra gizle (flaş efektini engellemek için)
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
            
            # Camera page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    print(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _open_camera(self) -> None:
        # already here
        self.showFullScreen()

    def _open_sensor(self) -> None:
        if self.main_ref:
            if not hasattr(self.main_ref, '_sensor_page') or self.main_ref._sensor_page is None:
                from .pyside_sensor import SensorPage
                self.main_ref._sensor_page = SensorPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            
            # Sensor widget'ını direkt göster
            self.main_ref._sensor_page.set_active_nav("btnSensor")
            self.main_ref._sensor_page.showFullScreen()
            
            # Camera page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    print(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _update_datetime_labels(self) -> None:
        now = QDateTime.currentDateTime()
        if hasattr(self.ui, 'labelDate'):
            self.ui.labelDate.setText(now.toString('dd.MM.yyyy dddd'))
        if hasattr(self.ui, 'labelTime'):
            self.ui.labelTime.setText(now.toString('HH:mm')) 

    # ---- Camera/detection integration (UI-thread via QTimer)
    def _on_detection_finished(self) -> None:
        # Called from CameraModule thread; only schedule UI work if needed
        # Here we let the regular timers pull stats and update UI safely
        pass

    def _toggle_camera_stream(self, checked: bool) -> None:
        if checked:
            self.camera_module.start_viewing()
            self._camera_stream_timer.start(30)  # ~30 FPS
        else:
            self.camera_module.stop_viewing()
            self._camera_stream_timer.stop()
            self.camera_label.clear()

    def _periodic_update(self) -> None:
        # Update date/time handled by its own timer; here handle data + detection state
        if self.get_data_callback:
            data = self.get_data_callback() or {}
            self._update_ui_from_data(data)
            # Detection kontrolü: yalnızca aktif kayıt varken GUI tarafından başlat, otomatik durdurma yapma
            if getattr(self.camera_module, 'is_recording', False) and not self.camera_module.is_detecting:
                self.camera_module.start_detection(on_finish=self._on_detection_finished)

    # ---- Frame/stat helpers
    def _get_latest_folder(self) -> Optional[str]:
        if not os.path.exists(self._recordings_dir):
            return None
        folders = [f for f in os.listdir(self._recordings_dir) if os.path.isdir(os.path.join(self._recordings_dir, f))]
        return max(folders) if folders else None

    def _find_priority_frame(self, detected_frames: List[str], detected_dir: str) -> Optional[str]:
        for keyword in ('broken', 'tooth'):
            for fname in detected_frames:
                if keyword in fname:
                    return os.path.join(detected_dir, fname)
        return os.path.join(detected_dir, detected_frames[0]) if detected_frames else None

    def _load_stats_file(self, stats_path: str) -> Optional[dict]:
        if not os.path.exists(stats_path):
            return None
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _get_latest_detection_data(self) -> tuple[Optional[str], Optional[dict]]:
        latest_folder = self._get_latest_folder()
        if not latest_folder:
            return None, None
        folder_path = os.path.join(self._recordings_dir, latest_folder)
        detected_dir = os.path.join(folder_path, 'detected')
        frame_path = None
        if os.path.exists(detected_dir):
            detected_frames = [f for f in sorted(os.listdir(detected_dir)) if f.endswith('.jpg')]
            frame_path = self._find_priority_frame(detected_frames, detected_dir)
        stats = self._load_stats_file(os.path.join(folder_path, 'detection_stats.json'))
        return frame_path, stats

    def _load_and_display_frame(self, frame_path: str) -> None:
        if not os.path.exists(frame_path):
            self.camera_label.clear()
            return
        frame = cv2.imread(frame_path)
        if frame is None:
            self.camera_label.clear()
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.camera_label.setPixmap(pixmap)

    def update_camera_frame(self) -> None:
        frame_path, stats = self._get_latest_detection_data()
        processed = {
            'tespit_edilen_dis': stats.get('total_crack', '-') if stats else '-',
            'tespit_edilen_kirik': stats.get('total_broken', '-') if stats else '-',
        }
        self._update_values(processed)
        if frame_path:
            self._load_and_display_frame(frame_path)
        else:
            self.camera_label.clear()

    # ---- UI mapping
    def _get_stats_from_recordings(self) -> Optional[dict]:
        latest_folder = self._get_latest_folder()
        if not latest_folder:
            return None
        stats_file = os.path.join(self._recordings_dir, latest_folder, 'detection_stats.json')
        return self._load_stats_file(stats_file)

    def _update_values(self, processed_data: Dict) -> None:
        try:
            # Optional: augment with latest stats
            stats = self._get_stats_from_recordings()
            label_map = getattr(self, 'label_data_mapping', None)
            if label_map is None:
                self.label_data_mapping = {
                    'labelTestereSagligiValue': 'testere_sagligi',
                    'labelAsinmaYuzdesiValue': 'asinma_yuzdesi',
                    'labelTestereDurumuValue': 'testere_durumu',
                    'labelTespitEdilenKirikValue': 'tespit_edilen_kirik',
                    'labelTespitEdilenDisValue': 'tespit_edilen_dis',
                }
                label_map = self.label_data_mapping

            for label_name, data_key in label_map.items():
                value = processed_data.get(data_key, '-')
                if stats:
                    if label_name == 'labelTespitEdilenDisValue':
                        value = stats.get('total_crack', value)
                    elif label_name == 'labelTespitEdilenKirikValue':
                        value = stats.get('total_broken', value)
                label_widget = getattr(self.ui, label_name, None)
                if label_widget:
                    label_widget.setText(str(value))
            
            # Wear percentage güncellemesi - mevcut değeri koru
            if hasattr(self, '_current_wear_percentage') and hasattr(self.ui, 'labelAsinmaYuzdesiValue'):
                self.ui.labelAsinmaYuzdesiValue.setText(f"{self._current_wear_percentage:.2f}")
            
            # Saw health güncellemesi - mevcut değeri koru
            if hasattr(self, '_current_saw_health') and hasattr(self.ui, 'labelTestereSagligiValue'):
                self.ui.labelTestereSagligiValue.setText(f"{self._current_saw_health:.2f}")
            
            # Detection stats değiştiğinde saw health'i yeniden hesapla
            if stats and (stats.get('total_tooth', 0) > 0 or stats.get('total_broken', 0) > 0):
                self._calculate_and_update_saw_health()

            # Detection end info banner - yeni sistem kullanılıyor
            if self.camera_module.is_detecting:
                if not self._detection_was_running:
                    # Detection başladığında sıralı görüntüleri güncelle
                    self._check_and_update_siralı_goruntu()
                self._detection_was_running = True
            elif self._detection_was_running:
                # Detection bittiğinde recordings klasörünü yeniden kontrol et
                self._check_recordings_and_create_frames()
                self._check_recordings_and_create_crack_frames()
                # Sıralı görüntüleri güncelle
                self._check_and_update_siralı_goruntu()
                self._detection_was_running = False
            else:
                # Detection çalışmıyorsa sadece ilk yüklemede sıralı görüntüleri göster
                if not self._siralı_goruntu_loaded:
                    self._check_and_update_siralı_goruntu()
                    self._siralı_goruntu_loaded = True
        except Exception as e:
            print(f"Camera _update_values hata: {e}")

    def _update_ui_from_data(self, data: Dict) -> None:
        # Keep placeholder mapping extensible
        try:
            # Only update labels present in UI
            if hasattr(self.ui, 'labelDate') and hasattr(self.ui, 'labelTime'):
                now = datetime.now()
                self.ui.labelDate.setText(now.strftime('%d.%m.%Y %A'))
                self.ui.labelTime.setText(now.strftime('%H:%M'))
            # Additional mappings can be added here if the camera page shows live machine values
        except Exception:
            pass 

    def _check_recordings_and_create_frames(self) -> None:
        """Recordings klasörünü kontrol edip kırık tespiti frame'lerini oluşturur"""
        try:
            # Mevcut frame'leri temizle
            self._clear_kirik_info_frames()
            
            if not os.path.exists(self._recordings_dir):
                # Recordings klasörü yoksa yeşil frame göster
                self._create_green_info_frame("Kırık diş tespit edilmedi.")
                return
            
            # Tüm recordings klasörlerini kontrol et
            recordings_data = self._scan_all_recordings()
            
            if not recordings_data:
                # Hiç detection verisi yoksa yeşil frame göster
                self._create_green_info_frame("Kırık diş tespit edilmedi.")
                return
            
            # Kırık tespit edilen kayıtları filtrele
            broken_detections = [data for data in recordings_data if data['total_broken'] > 0]
            
            if not broken_detections:
                # Hiç kırık tespit edilmemişse yeşil frame göster
                self._create_green_info_frame("Kırık diş tespit edilmedi.")
                return
            
            # Kırık tespit edilen her kayıt için bordo frame oluştur
            for detection in broken_detections:
                message = f"{detection['formatted_date']} tarihinde {detection['total_broken']} kırık tespit edildi."
                self._create_red_info_frame(message)
                
        except Exception as e:
            print(f"Recordings kontrol hatası: {e}")
            # Hata durumunda yeşil frame göster
            self._create_green_info_frame("Kırık diş tespit edilmedi.")
    
    def _scan_all_recordings(self) -> List[Dict]:
        """Tüm recordings klasörlerini tarar ve detection_stats.json dosyalarını okur"""
        recordings_data = []
        
        try:
            if not os.path.exists(self._recordings_dir):
                return recordings_data
            
            # Tüm klasörleri listele
            folders = [f for f in os.listdir(self._recordings_dir) 
                      if os.path.isdir(os.path.join(self._recordings_dir, f))]
            
            for folder in sorted(folders, reverse=True):  # En yeni önce
                folder_path = os.path.join(self._recordings_dir, folder)
                stats_file = os.path.join(folder_path, 'detection_stats.json')
                
                if os.path.exists(stats_file):
                    stats = self._load_stats_file(stats_file)
                    if stats:
                        # En yeni klasörün detection_stats.json dosyasının tamamlanmış olup olmadığını kontrol et
                        # Eğer timestamp yoksa veya çok yeni ise (son 10 saniye içinde) bu klasörü atla
                        timestamp = stats.get('timestamp', '')
                        if not timestamp:
                            continue
                        
                        try:
                            dt_object = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            current_time = datetime.now()
                            time_diff = (current_time - dt_object).total_seconds()
                            
                            # Eğer en yeni klasör ve 10 saniyeden daha yeni ise atla
                            if time_diff < 10 and folder == sorted(folders, reverse=True)[0]:
                                continue
                                
                        except ValueError:
                            # Geçersiz timestamp formatı, bu klasörü atla
                            continue
                        
                        # Tarih formatını düzenle (yılın ilk iki rakamını kaldır)
                        try:
                            formatted_date = dt_object.strftime('%d.%m.%y')  # %y kullanarak 2 haneli yıl
                        except:
                            formatted_date = str(timestamp).split(' ')[0]
                        
                        recordings_data.append({
                            'folder': folder,
                            'total_broken': stats.get('total_broken', 0),
                            'total_tooth': stats.get('total_tooth', 0),
                            'timestamp': timestamp,
                            'formatted_date': formatted_date
                        })
                        
        except Exception as e:
            print(f"Recordings tarama hatası: {e}")
            
        return recordings_data
    
    def _clear_kirik_info_frames(self) -> None:
        """Mevcut kırık tespiti frame'lerini temizler"""
        try:
            # Mevcut frame'leri sil
            for frame in self._kirik_info_frames:
                if frame and frame.parent():
                    frame.setParent(None)
                    frame.deleteLater()
            
            for label in self._kirik_info_labels:
                if label and label.parent():
                    label.setParent(None)
                    label.deleteLater()
            
            self._kirik_info_frames.clear()
            self._kirik_info_labels.clear()
            
            # Okey icon'ını da gizle
            self._hide_kirik_okey_icon()
            
        except Exception as e:
            print(f"Frame temizleme hatası: {e}")
    
    def _create_red_info_frame(self, message: str) -> None:
        """Bordo renkli kırık tespiti frame'i oluşturur"""
        try:
            # Frame oluştur
            info_frame = QFrame(self.ui.KirikTespitiFrame)
            info_frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(
                        spread:pad, 
                        x1:0, y1:0, 
                        x2:1, y2:1, 
                        stop:0 rgba(0, 0, 0, 255), 
                        stop:1 rgba(124, 4, 66, 255)
                    );
                    border-radius: 20px;
                }
            """)
            
            # Label oluştur
            info_label = QLabel(info_frame)
            info_label.setText(message)
            info_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #F4F6FC;
                    font-family: 'Plus-Jakarta-Sans';
                    font-weight: medium;
                    font-size: 20px;
                }
            """)
            info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # Layout oluştur
            layout = QVBoxLayout(info_frame)
            layout.addWidget(info_label)
            layout.setContentsMargins(25, 22, 25, 22)
            
            # Frame'i konumlandır
            frame_count = len(self._kirik_info_frames)
            y_position = 94 + (frame_count * 80)  # Her frame 80 piksel aşağıda
            info_frame.setGeometry(31, y_position, 443, 60)
            
            # Listeye ekle
            self._kirik_info_frames.append(info_frame)
            self._kirik_info_labels.append(info_label)
            
            info_frame.show()
            
            # Kırık tespit edildiğinde okey icon'ını gizle
            self._hide_kirik_okey_icon()
            
        except Exception as e:
            print(f"Kırmızı frame oluşturma hatası: {e}")
    
    def _create_green_info_frame(self, message: str) -> None:
        """Yeşil renkli bilgi frame'i oluşturur"""
        try:
            # Frame oluştur
            info_frame = QFrame(self.ui.KirikTespitiFrame)
            info_frame.setStyleSheet("""
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
            """)
            
            # Label oluştur
            info_label = QLabel(info_frame)
            info_label.setText(message)
            info_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #F4F6FC;
                    font-family: 'Plus-Jakarta-Sans';
                    font-weight: medium;
                    font-size: 20px;
                }
            """)
            info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # Layout oluştur
            layout = QVBoxLayout(info_frame)
            layout.addWidget(info_label)
            layout.setContentsMargins(25, 22, 25, 22)
            
            # Frame'i konumlandır
            info_frame.setGeometry(31, 94, 443, 60)
            
            # Listeye ekle
            self._kirik_info_frames.append(info_frame)
            self._kirik_info_labels.append(info_label)
            
            info_frame.show()
            
            # Eğer "Kırık diş tespit edilmedi" mesajı varsa okey icon'ını göster
            if "Kırık diş tespit edilmedi" in message:
                self._show_kirik_okey_icon()
            else:
                self._hide_kirik_okey_icon()
            
        except Exception as e:
            print(f"Yeşil frame oluşturma hatası: {e}") 

    def _create_okey_icon(self, parent_frame, icon_type: str) -> QLabel:
        """Okey icon'ı oluşturur"""
        try:
            # Icon path'ini belirle
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "okey-icon.svg")
            
            if not os.path.exists(icon_path):
                print(f"Okey icon dosyası bulunamadı: {icon_path}")
                return None
            
            # QLabel oluştur
            icon_label = QLabel(parent_frame)
            icon_label.setPixmap(QPixmap(icon_path))
            icon_label.setFixedSize(71, 71)
            icon_label.setScaledContents(True)
            icon_label.setStyleSheet("background: transparent;")
            
            # Pozisyonu ayarla (x217, y271)
            icon_label.move(217, 271)
            
            return icon_label
            
        except Exception as e:
            print(f"Okey icon oluşturma hatası ({icon_type}): {e}")
            return None
    
    def _show_kirik_okey_icon(self) -> None:
        """Kırık tespiti için okey icon'ını gösterir"""
        try:
            # Eğer icon zaten varsa gösterme
            if self._kirik_okey_icon and self._kirik_okey_icon.isVisible():
                return
            
            # Eğer icon yoksa oluştur
            if not self._kirik_okey_icon:
                self._kirik_okey_icon = self._create_okey_icon(self.ui.KirikTespitiFrame, "kirik")
            
            if self._kirik_okey_icon:
                self._kirik_okey_icon.show()
                
        except Exception as e:
            print(f"Kırık okey icon gösterme hatası: {e}")
    
    def _hide_kirik_okey_icon(self) -> None:
        """Kırık tespiti için okey icon'ını gizler"""
        try:
            if self._kirik_okey_icon:
                self._kirik_okey_icon.hide()
        except Exception as e:
            print(f"Kırık okey icon gizleme hatası: {e}")
    
    def _show_crack_okey_icon(self) -> None:
        """Çatlak tespiti için okey icon'ını gösterir"""
        try:
            # Eğer icon zaten varsa gösterme
            if self._crack_okey_icon and self._crack_okey_icon.isVisible():
                return
            
            # Eğer icon yoksa oluştur
            if not self._crack_okey_icon:
                self._crack_okey_icon = self._create_okey_icon(self.ui.CatlakTespitiFrame, "crack")
            
            if self._crack_okey_icon:
                self._crack_okey_icon.show()
                
        except Exception as e:
            print(f"Çatlak okey icon gösterme hatası: {e}")
    
    def _hide_crack_okey_icon(self) -> None:
        """Çatlak tespiti için okey icon'ını gizler"""
        try:
            if self._crack_okey_icon:
                self._crack_okey_icon.hide()
        except Exception as e:
            print(f"Çatlak okey icon gizleme hatası: {e}")

    def _check_and_update_siralı_goruntu(self) -> None:
        """Sıralı görüntü güncellemesini kontrol eder ve gerekirse günceller"""
        try:
            # En son recordings klasöründen görüntüleri al
            latest_folder = self._get_latest_folder()
            if not latest_folder:
                return
            
            # Recordings klasörünün kendisinden görüntüleri al
            recordings_dir = os.path.join(self._recordings_dir, latest_folder)
            if not os.path.exists(recordings_dir):
                return
            
            # Tüm görüntü dosyalarını listele (100KB altını ele)
            image_files = []
            for f in os.listdir(recordings_dir):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and f.startswith('frame_'):
                    fpath = os.path.join(recordings_dir, f)
                    try:
                        if os.path.getsize(fpath) >= 100 * 1024:
                            image_files.append(f)
                    except OSError:
                        continue
            
            if not image_files:
                return
            
            # Dosyaları sırala (en yeni önce)
            image_files.sort(reverse=True)
            
            # Eğer yeterli görüntü varsa güncelle
            if len(image_files) >= 1:  # En az 1 görüntü varsa güncelle
                self._update_siralı_goruntu()
            
        except Exception as e:
            print(f"Sıralı görüntü kontrol hatası: {e}")
    
    def _update_siralı_goruntu(self) -> None:
        """Sıralı görüntü frame'ini günceller - recordings klasöründen 4 adet frame alır"""
        try:
            # En son recordings klasöründen görüntüleri al
            latest_folder = self._get_latest_folder()
            if not latest_folder:
                print("Sıralı görüntü: En son klasör bulunamadı")
                return
            
            # Recordings klasörünün kendisinden görüntüleri al (detected değil)
            recordings_dir = os.path.join(self._recordings_dir, latest_folder)
            if not os.path.exists(recordings_dir):
                print(f"Sıralı görüntü: Klasör bulunamadı: {recordings_dir}")
                return
            
            # Tüm görüntü dosyalarını listele (frame_*.png, frame_*.jpg vb.) ve 100KB altını ele
            image_files = []
            for f in os.listdir(recordings_dir):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and f.startswith('frame_'):
                    fpath = os.path.join(recordings_dir, f)
                    try:
                        if os.path.getsize(fpath) >= 100 * 1024:
                            image_files.append(f)
                    except OSError:
                        continue
            
            if not image_files:
                print(f"Sıralı görüntü: {recordings_dir} klasöründe görüntü dosyası bulunamadı")
                return
            
            # Dosyaları sırala (en yeni önce)
            image_files.sort(reverse=True)
            
            # Tam olarak 4 adet görüntü seç (eğer 4'ten az varsa hepsini al, 4'ten fazla varsa rastgele 4 tane)
            if len(image_files) >= 4:
                selected_images = random.sample(image_files, 4)
            else:
                selected_images = image_files  # 4'ten az varsa hepsini al
            
            print(f"Sıralı görüntü: {len(selected_images)} adet görüntü seçildi")
            
            # Mevcut görüntü label'larını temizle
            self._clear_siralı_goruntu_labels()
            
            # Sıralı görüntü frame'ini oluştur
            self._create_siralı_goruntu_frame(selected_images, recordings_dir)
            
            # Son güncelleme zamanını kaydet
            self._last_siralı_goruntu_update = datetime.now().timestamp()
            
        except Exception as e:
            print(f"Sıralı görüntü güncelleme hatası: {e}")
    
    def _clear_siralı_goruntu_labels(self) -> None:
        """Mevcut sıralı görüntü label'larını temizler"""
        try:
            # Eğer hiç label yoksa temizleme yapma
            if len(self._siralı_goruntu_labels) == 0:
                return
                
            for label in self._siralı_goruntu_labels:
                if label and label.parent():
                    label.setParent(None)
                    label.deleteLater()
            
            self._siralı_goruntu_labels.clear()
            
        except Exception as e:
            print(f"Sıralı görüntü temizleme hatası: {e}")
    
    def _create_siralı_goruntu_frame(self, image_files: List[str], recordings_dir: str) -> None:
        """Sıralı görüntü frame'ini oluşturur - 4 adet görüntüyü yan yana dizerek"""
        try:
            # SiraliGoruntuFrame'i kontrol et
            if not hasattr(self.ui, 'SiraliGoruntuFrame'):
                print("SiraliGoruntuFrame bulunamadı")
                return
            
            # Mevcut widget'ları temizle
            for child in self.ui.SiraliGoruntuFrame.children():
                if isinstance(child, QWidget):
                    child.setParent(None)
                    child.deleteLater()
            
            # Container widget oluştur
            container_widget = QWidget(self.ui.SiraliGoruntuFrame)
            container_widget.setFixedHeight(self._image_height)
            container_widget.setFixedWidth(self._image_width * len(image_files))  # Tam genişlik
            
            # Horizontal layout oluştur (boşluksuz)
            layout = QHBoxLayout(container_widget)
            layout.setSpacing(0)  # Görüntüler arası boşluk yok
            layout.setContentsMargins(0, 0, 0, 0)  # Kenar boşlukları yok
            
            # Her görüntü için label oluştur
            for image_file in image_files:
                image_path = os.path.join(recordings_dir, image_file)
                if os.path.exists(image_path):
                    # Görüntüyü yükle ve boyutlandır
                    image = cv2.imread(image_path)
                    if image is not None:
                        # Görüntüyü 240x150 boyutuna getir (1920x1200'den /8)
                        resized_image = cv2.resize(image, (self._image_width, self._image_height))
                        
                        # BGR'den RGB'ye çevir
                        rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
                        
                        # QImage oluştur
                        h, w, ch = rgb_image.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        
                        # QPixmap oluştur
                        pixmap = QPixmap.fromImage(qt_image)
                        
                        # Label oluştur
                        image_label = QLabel(container_widget)
                        image_label.setPixmap(pixmap)
                        image_label.setFixedSize(self._image_width, self._image_height)
                        image_label.setStyleSheet("""
                            QLabel {
                                border: none;
                                background-color: transparent;
                            }
                        """)
                        
                        # Layout'a ekle
                        layout.addWidget(image_label)
                        self._siralı_goruntu_labels.append(image_label)
                        
                        print(f"Görüntü eklendi: {image_file}")
                    else:
                        print(f"Görüntü yüklenemedi: {image_path}")
                else:
                    print(f"Görüntü dosyası bulunamadı: {image_path}")
            
            # Container'ı SiraliGoruntuFrame'e yerleştir (sola yaslanmış)
            container_widget.move(0, 0)
            container_widget.show()
            
            # Görüntülerin yüklendiğini işaretle
            print(f"Sıralı görüntü frame oluşturuldu: {len(self._siralı_goruntu_labels)} görüntü")
            
        except Exception as e:
            print(f"Sıralı görüntü frame oluşturma hatası: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_detected_preview(self) -> None:
        """Detected klasöründeki büyük frame önizlemesini 30 saniyede bir yeniler."""
        try:
            frame_path, _ = self._get_latest_detection_data()
            if frame_path:
                self._load_and_display_frame(frame_path)
        except Exception as e:
            print(f"Detected önizleme yenileme hatası: {e}")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            if hasattr(self, '_bg_label') and self._bg_label:
                self._bg_label.setGeometry(0, 0, self.width(), self.height())
        except Exception:
            pass
    
    def _check_recordings_and_create_crack_frames(self) -> None:
        """Recordings klasörünü kontrol edip çatlak tespiti frame'lerini oluşturur"""
        try:
            # Mevcut frame'leri temizle
            self._clear_crack_info_frames()
            
            if not os.path.exists(self._recordings_dir):
                # Recordings klasörü yoksa yeşil frame göster
                self._create_green_crack_info_frame("Çatlak tespit edilmedi.")
                return
            
            # Tüm recordings klasörlerini kontrol et
            recordings_data = self._scan_all_recordings_for_cracks()
            
            if not recordings_data:
                # Hiç detection verisi yoksa yeşil frame göster
                self._create_green_crack_info_frame("Çatlak tespit edilmedi.")
                return
            
            # Çatlak tespit edilen kayıtları filtrele
            crack_detections = [data for data in recordings_data if data['total_crack'] > 0]
            
            if not crack_detections:
                # Hiç çatlak tespit edilmemişse yeşil frame göster
                self._create_green_crack_info_frame("Çatlak tespit edilmedi.")
                return
            
            # Çatlak tespit edilen her kayıt için bordo frame oluştur (kırık tespitinde olduğu gibi)
            for detection in crack_detections:
                message = f"{detection['formatted_date']} tarihinde {detection['total_crack']} çatlak tespit edildi."
                self._create_red_crack_info_frame(message)
                
        except Exception as e:
            print(f"Recordings crack kontrol hatası: {e}")
            # Hata durumunda yeşil frame göster
            self._create_green_crack_info_frame("Çatlak tespit edilmedi.")
    
    def _scan_all_recordings_for_cracks(self) -> List[Dict]:
        """Tüm recordings klasörlerini tarar ve crack detection_stats.json dosyalarını okur"""
        recordings_data = []
        
        try:
            if not os.path.exists(self._recordings_dir):
                return recordings_data
            
            # Tüm klasörleri listele
            folders = [f for f in os.listdir(self._recordings_dir) 
                      if os.path.isdir(os.path.join(self._recordings_dir, f))]
            
            for folder in sorted(folders, reverse=True):  # En yeni önce
                folder_path = os.path.join(self._recordings_dir, folder)
                stats_file = os.path.join(folder_path, 'detection_stats.json')
                
                if os.path.exists(stats_file):
                    stats = self._load_stats_file(stats_file)
                    if stats and 'total_crack' in stats:
                        # En yeni klasörün detection_stats.json dosyasının tamamlanmış olup olmadığını kontrol et
                        # Eğer timestamp yoksa veya çok yeni ise (son 10 saniye içinde) bu klasörü atla
                        timestamp = stats.get('timestamp', '')
                        if not timestamp:
                            continue
                        
                        try:
                            dt_object = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            current_time = datetime.now()
                            time_diff = (current_time - dt_object).total_seconds()
                            
                            # Eğer en yeni klasör ve 10 saniyeden daha yeni ise atla
                            if time_diff < 10 and folder == sorted(folders, reverse=True)[0]:
                                continue
                                
                        except ValueError:
                            # Geçersiz timestamp formatı, bu klasörü atla
                            continue
                        
                        # Tarih formatını düzenle (yılın ilk iki rakamını kaldır)
                        try:
                            formatted_date = dt_object.strftime('%d.%m.%y')  # %y kullanarak 2 haneli yıl
                        except:
                            formatted_date = str(timestamp).split(' ')[0]
                        
                        recordings_data.append({
                            'folder': folder,
                            'total_crack': stats.get('total_crack', 0),
                            'timestamp': timestamp,
                            'formatted_date': formatted_date
                        })
                        
        except Exception as e:
            print(f"Recordings crack tarama hatası: {e}")
            
        return recordings_data
    
    def _clear_crack_info_frames(self) -> None:
        """Mevcut çatlak tespiti frame'lerini temizler"""
        try:
            # Mevcut frame'leri sil
            for frame in self._crack_info_frames:
                if frame and frame.parent():
                    frame.setParent(None)
                    frame.deleteLater()
            
            for label in self._crack_info_labels:
                if label and label.parent():
                    label.setParent(None)
                    label.deleteLater()
            
            self._crack_info_frames.clear()
            self._crack_info_labels.clear()
            
            # Okey icon'ını da gizle
            self._hide_crack_okey_icon()
            
        except Exception as e:
            print(f"Crack frame temizleme hatası: {e}")
    
    def _create_red_crack_info_frame(self, message: str) -> None:
        """Bordo renkli çatlak tespiti frame'i oluşturur (kırık tespitinde olduğu gibi)"""
        try:
            # Frame oluştur
            info_frame = QFrame(self.ui.CatlakTespitiFrame)
            info_frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(
                        spread:pad, 
                        x1:0, y1:0, 
                        x2:1, y2:1, 
                        stop:0 rgba(0, 0, 0, 255), 
                        stop:1 rgba(124, 4, 66, 255)
                    );
                    border-radius: 20px;
                }
            """)
            
            # Label oluştur
            info_label = QLabel(info_frame)
            info_label.setText(message)
            info_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #F4F6FC;
                    font-family: 'Plus-Jakarta-Sans';
                    font-weight: medium;
                    font-size: 20px;
                }
            """)
            info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # Layout oluştur
            layout = QVBoxLayout(info_frame)
            layout.addWidget(info_label)
            layout.setContentsMargins(25, 22, 25, 22)
            
            # Frame'i konumlandır
            frame_count = len(self._crack_info_frames)
            y_position = 94 + (frame_count * 80)  # Her frame 80 piksel aşağıda
            info_frame.setGeometry(31, y_position, 443, 60)
            
            # Listeye ekle
            self._crack_info_frames.append(info_frame)
            self._crack_info_labels.append(info_label)
            
            info_frame.show()
            
            # Çatlak tespit edildiğinde okey icon'ını gizle
            self._hide_crack_okey_icon()
            
        except Exception as e:
            print(f"Bordo crack frame oluşturma hatası: {e}")
    
    def _create_green_crack_info_frame(self, message: str) -> None:
        """Yeşil renkli çatlak tespiti frame'i oluşturur (çatlak tespit edilmediğinde)"""
        try:
            # Frame oluştur
            info_frame = QFrame(self.ui.CatlakTespitiFrame)
            info_frame.setStyleSheet("""
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
            """)
            
            # Label oluştur
            info_label = QLabel(info_frame)
            info_label.setText(message)
            info_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #F4F6FC;
                    font-family: 'Plus-Jakarta-Sans';
                    font-weight: medium;
                    font-size: 20px;
                }
            """)
            info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # Layout oluştur
            layout = QVBoxLayout(info_frame)
            layout.addWidget(info_label)
            layout.setContentsMargins(25, 22, 25, 22)
            
            # Frame'i konumlandır
            frame_count = len(self._crack_info_frames)
            y_position = 94 + (frame_count * 80)  # Her frame 80 piksel aşağıda
            info_frame.setGeometry(31, y_position, 443, 60)
            
            # Listeye ekle
            self._crack_info_frames.append(info_frame)
            self._crack_info_labels.append(info_label)
            
            info_frame.show()
            
            # Eğer "Çatlak tespit edilmedi" mesajı varsa okey icon'ını göster
            if "Çatlak tespit edilmedi" in message:
                self._show_crack_okey_icon()
            else:
                self._hide_crack_okey_icon()
            
        except Exception as e:
            print(f"Yeşil crack frame oluşturma hatası: {e}")
    
 