from typing import Callable, Dict, Optional
from PySide6.QtCore import QTimer, QDateTime, Qt
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QIcon
import os

from gui.ui_files.positioning_widget_ui import Ui_Form


class PositioningPage(QWidget):
    def __init__(self, main_ref=None, get_data_callback: Optional[Callable[[], Dict]] = None) -> None:
        super().__init__(None)  # top-level window, not a child of main_ref
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

        # Timers (date/time)
        self._datetime_timer = QTimer(self)
        self._datetime_timer.timeout.connect(self._update_datetime_labels)
        self._datetime_timer.start(1000)
        self._update_datetime_labels()
        
        # Periodic data update timer
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self._on_data_tick)
        self._data_timer.start(200)
        self._on_data_tick()

        # Set positioning page as active initially
        self.set_active_nav('btnPositioning_2')

        # Connect positioning control buttons
        self._connect_positioning_buttons()

    def set_active_nav(self, active_btn_name: str):
        """Navigation butonlarının aktif/pasif durumunu ayarla"""
        try:
            # Aktif ve pasif icon'ları tanımla
            nav_buttons = {
                'btnControlPanel_2': ('control-panel-icon2.svg', 'control-panel-icon2-active.svg'),
                'btnPositioning_2': ('positioning-icon2.svg', 'positioning-icon2-active.svg'),
                'btnCamera_2': ('camera-icon2.svg', 'camera-icon-active.svg'),
                'btnSensor_2': ('sensor-icon2.svg', 'sensor-icon2-active.svg'),
                'btnTracking_2': ('tracking-icon2.svg', 'tracking-icon2-active.svg'),
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
            if hasattr(self.ui, 'btnControlPanel_2'):
                self.ui.btnControlPanel_2.setIcon(self._icon("control-panel-icon2.svg"))
            if hasattr(self.ui, 'btnPositioning_2'):
                self.ui.btnPositioning_2.setIcon(self._icon("positioning-icon2.svg"))
            if hasattr(self.ui, 'btnCamera_2'):
                self.ui.btnCamera_2.setIcon(self._icon("camera-icon2.svg"))
            if hasattr(self.ui, 'btnSensor_2'):
                self.ui.btnSensor_2.setIcon(self._icon("sensor-icon2.svg"))
            if hasattr(self.ui, 'btnTracking_2'):
                self.ui.btnTracking_2.setIcon(self._icon("tracking-icon2.svg"))
        except Exception:
            pass

    def _connect_navigation(self) -> None:
        if hasattr(self.ui, 'btnControlPanel_2'):
            self.ui.btnControlPanel_2.clicked.connect(self._open_control_panel)
        if hasattr(self.ui, 'btnPositioning_2'):
            self.ui.btnPositioning_2.clicked.connect(self._open_positioning)
        if hasattr(self.ui, 'btnCamera_2'):
            self.ui.btnCamera_2.clicked.connect(self._open_camera)
        if hasattr(self.ui, 'btnSensor_2'):
            self.ui.btnSensor_2.clicked.connect(self._open_sensor)
        if hasattr(self.ui, 'btnTracking_2'):
            self.ui.btnTracking_2.clicked.connect(self._open_monitoring)

    def _connect_positioning_buttons(self) -> None:
        """Konumlandırma kontrol butonlarını bağla"""
        try:
            # Mengene kontrol butonları (tıklayınca aktif, tekrar tıklayınca pasif)
            if hasattr(self.ui, 'btnArkaMengeneAc'):
                btn = self.ui.btnArkaMengeneAc
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, b=btn: self._on_toggle_button(b, "arka_mengene_ac", checked))
            if hasattr(self.ui, 'btnMengeneKapat'):
                btn = self.ui.btnMengeneKapat
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, b=btn: self._on_toggle_button(b, "mengene_kapat", checked))
            if hasattr(self.ui, 'btnOnMengeneAc'):
                btn = self.ui.btnOnMengeneAc
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, b=btn: self._on_toggle_button(b, "on_mengene_ac", checked))

            # Malzeme konumlandırma butonları (basılı tutarken aktif)
            if hasattr(self.ui, 'btnMalzemeGeri'):
                btn = self.ui.btnMalzemeGeri
                btn.setCheckable(True)
                btn.pressed.connect(lambda b=btn: self._on_hold_button(b, "malzeme_geri", True))
                btn.released.connect(lambda b=btn: self._on_hold_button(b, "malzeme_geri", False))
            if hasattr(self.ui, 'btnMalzemeIleri'):
                btn = self.ui.btnMalzemeIleri
                btn.setCheckable(True)
                btn.pressed.connect(lambda b=btn: self._on_hold_button(b, "malzeme_ileri", True))
                btn.released.connect(lambda b=btn: self._on_hold_button(b, "malzeme_ileri", False))

            # Testere konumlandırma butonları (basılı tutarken aktif)
            if hasattr(self.ui, 'btnTestereYukari'):
                btn = self.ui.btnTestereYukari
                btn.setCheckable(True)
                btn.pressed.connect(lambda b=btn: self._on_hold_button(b, "testere_yukari", True))
                btn.released.connect(lambda b=btn: self._on_hold_button(b, "testere_yukari", False))
            if hasattr(self.ui, 'btnTestereAsagi'):
                btn = self.ui.btnTestereAsagi
                btn.setCheckable(True)
                btn.pressed.connect(lambda b=btn: self._on_hold_button(b, "testere_asagi", True))
                btn.released.connect(lambda b=btn: self._on_hold_button(b, "testere_asagi", False))
        except Exception as e:
            print(f"Konumlandırma buton bağlantı hatası: {e}")

    def _on_toggle_button(self, button, command: str, checked: bool) -> None:
        """Toggle çalışan butonlar için tek noktadan handler"""
        try:
            state_text = "AKTIF" if checked else "PASIF"
            print(f"{command} => {state_text}")
            self.send_modbus_command(command, checked)
        except Exception as e:
            print(f"Toggle buton hata: {e}")

    def _on_hold_button(self, button, command: str, is_pressed: bool) -> None:
        """Basılı tutma ile çalışan butonlar için handler"""
        try:
            # Görsel geri bildirim için butonu checked göster (stil :checked kullanıyorsa)
            if hasattr(button, 'setChecked'):
                button.setChecked(is_pressed)
            else:
                button.setDown(is_pressed)
            state_text = "BASILI" if is_pressed else "BOSALDI"
            print(f"{command} => {state_text}")
            self.send_modbus_command(command, is_pressed)
        except Exception as e:
            print(f"Hold buton hata: {e}")

    def _open_control_panel(self) -> None:
        if self.main_ref:
            # Timer'ları yeniden başlat ve control panel'e dön
            self.hide()
            self.main_ref.set_active_nav("btnControlPanel")
            self.main_ref.showFullScreen()
            self.main_ref.raise_()
            self.main_ref.activateWindow()
            self.main_ref.setFocus()

    def _open_positioning(self) -> None:
        # already here
        self.showFullScreen()

    def _open_camera(self) -> None:
        if self.main_ref:
            self.hide()
            if not hasattr(self.main_ref, '_camera_page') or self.main_ref._camera_page is None:
                from .pyside_camera import CameraPage
                self.main_ref._camera_page = CameraPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            self.main_ref._camera_page.set_active_nav("btnCamera")
            self.main_ref._camera_page.showFullScreen()

    def _open_sensor(self) -> None:
        if self.main_ref:
            self.hide()
            if not hasattr(self.main_ref, '_sensor_page') or self.main_ref._sensor_page is None:
                from .pyside_sensor import SensorPage
                self.main_ref._sensor_page = SensorPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            self.main_ref._sensor_page.set_active_nav("btnSensor")
            self.main_ref._sensor_page.showFullScreen()

    def _open_monitoring(self) -> None:
        if self.main_ref:
            self.hide()
            if not hasattr(self.main_ref, '_monitoring_page') or self.main_ref._monitoring_page is None:
                from .pyside_monitoring import MonitoringPage
                self.main_ref._monitoring_page = MonitoringPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            self.main_ref._monitoring_page.set_active_nav("btnTracking")
            self.main_ref._monitoring_page.showFullScreen()

    def _update_datetime_labels(self) -> None:
        now = QDateTime.currentDateTime()
        if hasattr(self.ui, 'labelDate'):
            self.ui.labelDate.setText(now.toString('dd.MM.yyyy dddd'))
        if hasattr(self.ui, 'labelTime'):
            self.ui.labelTime.setText(now.toString('HH:mm'))

    def _on_data_tick(self) -> None:
        try:
            data = self.get_data_callback() if self.get_data_callback else None
            if not data or not bool(data.get('modbus_connected', False)):
                # No data or not connected: show placeholders
                self.update_ui({})
            else:
                self.update_ui(data)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            if hasattr(self, '_bg_label') and self._bg_label:
                self._bg_label.setGeometry(0, 0, self.width(), self.height())
        except Exception:
            pass

    # Mengene kontrol fonksiyonları
    def _on_arka_mengene_ac(self) -> None:
        """Arka mengene aç butonuna basıldığında"""
        try:
            print("Arka mengene açılıyor...")
            # Burada Modbus komutu gönderilecek
            # self.send_modbus_command("arka_mengene_ac", True)
        except Exception as e:
            print(f"Arka mengene açma hatası: {e}")

    def _on_mengene_kapat(self) -> None:
        """Mengene kapat butonuna basıldığında"""
        try:
            print("Mengene kapatılıyor...")
            # Burada Modbus komutu gönderilecek
            # self.send_modbus_command("mengene_kapat", True)
        except Exception as e:
            print(f"Mengene kapatma hatası: {e}")

    def _on_on_mengene_ac(self) -> None:
        """Ön mengene aç butonuna basıldığında"""
        try:
            print("Ön mengene açılıyor...")
            # Burada Modbus komutu gönderilecek
            # self.send_modbus_command("on_mengene_ac", True)
        except Exception as e:
            print(f"Ön mengene açma hatası: {e}")

    # Malzeme konumlandırma fonksiyonları
    def _on_malzeme_geri(self) -> None:
        """Malzeme geri butonuna basıldığında"""
        try:
            print("Malzeme geri hareket ettiriliyor...")
            # Burada Modbus komutu gönderilecek
            # self.send_modbus_command("malzeme_geri", True)
        except Exception as e:
            print(f"Malzeme geri hareket hatası: {e}")

    def _on_malzeme_ileri(self) -> None:
        """Malzeme ileri butonuna basıldığında"""
        try:
            print("Malzeme ileri hareket ettiriliyor...")
            # Burada Modbus komutu gönderilecek
            # self.send_modbus_command("malzeme_ileri", True)
        except Exception as e:
            print(f"Malzeme ileri hareket hatası: {e}")

    # Testere konumlandırma fonksiyonları
    def _on_testere_yukari(self) -> None:
        """Testere yukarı butonuna basınunu bağlldığında"""
        try:
            print("Testere yukarı hareket ettiriliyor...")
            # Burada Modbus komutu gönderilecek
            # self.send_modbus_command("testere_yukari", True)
        except Exception as e:
            print(f"Testere yukarı hareket hatası: {e}")

    def _on_testere_asagi(self) -> None:
        """Testere aşağı butonuna basıldığında"""
        try:
            print("Testere aşağı hareket ettiriliyor...")
            # Burada Modbus komutu gönderilecek
            # self.send_modbus_command("testere_asagi", True)
        except Exception as e:
            print(f"Testere aşağı hareket hatası: {e}")

    def update_ui(self, processed_data: Dict):
        """UI'yi güncel verilerle güncelle"""
        try:
            # Burada positioning ile ilgili verileri UI'ya yansıtabilirsiniz
            # Örneğin mengene durumu, motor durumları vs.
            pass
        except Exception as e:
            print(f"Positioning UI güncelleme hatası: {e}")

    def send_modbus_command(self, command: str, value: bool):
        """Modbus komutu gönder (placeholder)"""
        try:
            # Burada gerçek Modbus komutları gönderilecek
            print(f"Modbus komutu gönderiliyor: {command} = {value}")
            if self.get_data_callback:
                # Ana sistemdeki Modbus handler'a komut gönder
                pass
        except Exception as e:
            print(f"Modbus komut gönderme hatası: {e}")