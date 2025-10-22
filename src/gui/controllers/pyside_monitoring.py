from typing import Callable, Dict, Optional
from PySide6.QtCore import QTimer, QDateTime, Qt
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QIcon
import os

from gui.ui_files.monitoring_widget_ui import Ui_Form


class MonitoringPage(QWidget):
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

        # Set monitoring page as active initially
        self.set_active_nav('btnTracking')

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

    def _open_control_panel(self) -> None:
        if self.main_ref:
            # Check if main_ref has navigation lock
            if hasattr(self.main_ref, '_navigation_lock') and hasattr(self.main_ref, '_is_switching'):
                if not self.main_ref._navigation_lock.acquire(blocking=False):
                    logger.warning("Navigation already in progress, ignoring request")
                    return
                
                try:
                    self.main_ref._is_switching = True
                    
                    # Control panel'i direkt göster
                    self.main_ref.set_active_nav("btnControlPanel")
                    self.main_ref.showFullScreen()
                    self.main_ref.raise_()
                    self.main_ref.activateWindow()
                    self.main_ref.setFocus()
                    
                    # Monitoring page'i 500ms sonra gizle (flaş efektini engellemek için)
                    def safe_hide():
                        try:
                            if self.isVisible():
                                self.hide()
                        except Exception as e:
                            logger.debug(f"Hide işlemi hatası: {e}")
                        finally:
                            if hasattr(self.main_ref, '_is_switching'):
                                self.main_ref._is_switching = False
                            if hasattr(self.main_ref, '_navigation_lock'):
                                self.main_ref._navigation_lock.release()
                    
                    QTimer.singleShot(500, safe_hide)
                except Exception as e:
                    logger.error(f"Control panel açma hatası: {e}")
                    self.main_ref._is_switching = False
                    self.main_ref._navigation_lock.release()
            else:
                # Legacy behavior if navigation lock not available
                self.main_ref.set_active_nav("btnControlPanel")
                self.main_ref.showFullScreen()
                self.main_ref.raise_()
                self.main_ref.activateWindow()
                self.main_ref.setFocus()
                
                def safe_hide():
                    try:
                        if self.isVisible():
                            self.hide()
                    except Exception as e:
                        logger.debug(f"Hide işlemi hatası: {e}")
                
                QTimer.singleShot(500, safe_hide)

    def _open_positioning(self) -> None:
        if self.main_ref:
            if not hasattr(self.main_ref, '_positioning_page') or self.main_ref._positioning_page is None:
                from .pyside_positioning import PositioningPage
                self.main_ref._positioning_page = PositioningPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            
            # Positioning widget'ını direkt göster
            self.main_ref._positioning_page.set_active_nav("btnPositioning_2")
            self.main_ref._positioning_page.showFullScreen()
            
            # Monitoring page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    logger.debug(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _open_monitoring(self) -> None:
        # already here
        self.showFullScreen()

    def _open_camera(self) -> None:
        if self.main_ref:
            if not hasattr(self.main_ref, '_camera_page') or self.main_ref._camera_page is None:
                from .pyside_camera import CameraPage
                self.main_ref._camera_page = CameraPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            
            # Camera widget'ını direkt göster
            self.main_ref._camera_page.set_active_nav("btnCamera")
            self.main_ref._camera_page.showFullScreen()
            
            # Monitoring page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    logger.debug(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

    def _open_sensor(self) -> None:
        if self.main_ref:
            if not hasattr(self.main_ref, '_sensor_page') or self.main_ref._sensor_page is None:
                from .pyside_sensor import SensorPage
                self.main_ref._sensor_page = SensorPage(main_ref=self.main_ref, get_data_callback=self.get_data_callback)
            
            # Sensor widget'ını direkt göster
            self.main_ref._sensor_page.set_active_nav("btnSensor")
            self.main_ref._sensor_page.showFullScreen()
            
            # Monitoring page'i 500ms sonra gizle (flaş efektini engellemek için)
            # Timer'ı güvenli hale getir
            def safe_hide():
                try:
                    if self.isVisible():
                        self.hide()
                except Exception as e:
                    logger.debug(f"Hide işlemi hatası: {e}")
            
            QTimer.singleShot(500, safe_hide)

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
                # Replace default '16.35' placeholders if no data
                if value == '-' or value is None or value == '':
                    value = '—'
                else:
                    # Format serit_sapmasi consistently with control panel
                    if data_key == 'serit_sapmasi':
                        try:
                            value = f"{float(value):.2f}"
                        except (ValueError, TypeError):
                            value = '—'
                label_widget = getattr(self.ui, label_name, None)
                if label_widget:
                    label_widget.setText(str(value))
        except Exception as e:
            logger.debug(f"Monitoring _update_values hata: {e}")

    def update_ui(self, processed_data: Dict):
        self._update_values(processed_data) 