from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTextEdit, QWidget, QVBoxLayout, QLabel, QApplication, QInputDialog, QFrame, QScrollArea
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, Qt, QRect
from PyQt5.QtGui import QTextCursor, QColor, QFont, QPalette, QTextCharFormat, QIcon
import logging
import time
from datetime import datetime
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from typing import Dict, Optional, Tuple
from queue import Queue
import threading

from core.logger import logger
from core.constants import TestereState, KATSAYI, ControllerType
from control.factory import get_controller_factory
from models import ProcessedData
from utils.helpers import reverse_calculate_value
from core.camera import CameraModule
from .monitoring_controller import MonitoringWindow
from .camera_controller import CameraWindow

from .qt_sensor_interface import Ui_MainWindow

class SensorWindow(QMainWindow):
    """Sensör verileri sayfası için ana sınıf"""
    
    def __init__(self, parent=None, get_data_callback=None):
        super().__init__(parent)
        
        # UI'ı yükle
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Parent ve callback referansları
        self.parent = parent
        self.get_data_callback = get_data_callback
        
        # Timer referansları
        self.datetime_timer = None
        self.data_timer = None
        
        # Veritabanı bağlantısı
        try:
            self.db = sqlite3.connect('data/total.db')
            logger.info("Sensör sayfası - Veritabanı bağlantısı başarılı: data/total.db")
        except Exception as e:
            logger.error(f"Sensör sayfası - Veritabanı bağlantı hatası: {e}")
            self.db = None
        
        # Timer'ları başlat
        self.setup_timers()
        
        # GUI'yi başlat
        self.setup_gui()
        
        # Başlangıç değerlerini ayarla
        self.update_ui()

        self.set_active_nav("btnSensor")

        # Anomali durumlarını tutan sözlük
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
        # toolButton sinyalini bağla
        if hasattr(self.ui, 'toolButton'):
            self.ui.toolButton.clicked.connect(self.reset_anomaly_states)

    def setup_timers(self):
        """Timer'ları başlatır"""
        try:
            # Tarih ve saat güncelleme timer'ı (her saniye)
            self.datetime_timer = QTimer(self)
            self.datetime_timer.timeout.connect(self._update_datetime_labels)
            self.datetime_timer.start(1000)  # 1000ms = 1 saniye
            
            # Veri güncelleme timer'ı
            self.data_timer = QTimer(self)
            self.data_timer.timeout.connect(self.update_data)
            self.data_timer.start(100)  # 100ms
            
        except Exception as e:
            logger.error(f"Sensör sayfası timer başlatma hatası: {e}")

    def setup_gui(self):
        """GUI bileşenlerini başlatır"""
        try:
            # Pencere başlığı
            self.setWindowTitle("Akıllı Testere - Sensör Verileri")
            
            # Sidebar buton bağlantıları
            self.ui.btnControlPanel.clicked.connect(self.open_control_panel)
            self.ui.btnPositioning.clicked.connect(self.open_positioning)
            self.ui.btnCamera.clicked.connect(self.open_camera_window)
            self.ui.btnSensor.clicked.connect(self.open_sensor_window)
            self.ui.btnTracking.clicked.connect(self.open_monitoring_window)
            
            # X ekseni butonları için bağlantılar
            # self.ui.btnKesmeHizi.clicked.connect(lambda: self._handle_x_axis_buttons(self.ui.btnKesmeHizi))
            # self.ui.btnIlerlemeHizi.clicked.connect(lambda: self._handle_x_axis_buttons(self.ui.btnIlerlemeHizi))
            # self.ui.btnSeritAkim.clicked.connect(lambda: self._handle_x_axis_buttons(self.ui.btnSeritAkim))
            # self.ui.btnSeritSapmasi.clicked.connect(lambda: self._handle_x_axis_buttons(self.ui.btnSeritSapmasi))
            
            # # Y ekseni butonları için bağlantılar
            # self.ui.btnZaman.clicked.connect(lambda: self._handle_y_axis_buttons(self.ui.btnZaman))
            # self.ui.btnYukseklik.clicked.connect(lambda: self._handle_y_axis_buttons(self.ui.btnYukseklik))
            
            # Başlangıç değerlerini ayarla
            self._update_datetime_labels()
            
        except Exception as e:
            logger.error(f"Sensör sayfası GUI başlatma hatası: {e}")
            logger.exception("Detaylı hata:")

    def _update_datetime_labels(self):
        """Tarih ve saat etiketlerini günceller"""
        try:
            now = datetime.now()
            # Qt arayüzünde kullanılacak format
            date_str = now.strftime('%d.%m.%Y %A') 
            time_str = now.strftime('%H:%M')      
            
            self.ui.labelDate.setText(date_str)
            self.ui.labelTime.setText(time_str)
            
        except Exception as e:
            logger.error(f"Sensör sayfası - Tarih/Saat güncelleme hatası: {e}")

    def update_data(self):
        """Sensör verilerini günceller"""
        try:
            if self.get_data_callback and callable(self.get_data_callback):
                current_data = self.get_data_callback()
                if current_data and isinstance(current_data, dict):
                    self.update_sensor_values(current_data)
        except Exception as e:
            logger.error(f"Sensör veri güncelleme hatası: {e}")

    def update_sensor_values(self, data: Dict):
        """Sensör değerlerini günceller"""
        try:
            if not data or not isinstance(data, dict):
                return
            # Sadece anomali olmayan frame'ler güncellenir
            self._check_anomalies(data)
        except Exception as e:
            logger.error(f"Sensör değer güncelleme hatası: {e}")

    def _check_anomalies(self, data: Dict):
        """Anomali durumlarını kontrol eder"""
        try:
            if not data or not isinstance(data, dict):
                return
            current_time = datetime.now().strftime('%d.%m.%Y')
            # Şerit akım kontrolü
            serit_akim = float(data.get('serit_motor_akim_a', 0))
            if serit_akim > 25 or self.anomaly_states['KesmeHizi']:
                self.anomaly_states['KesmeHizi'] = True
                self.ui.KesmeHiziFrame.setStyleSheet("""
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
                self.ui.labelKesmeHiziInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.KesmeHiziFrame.setStyleSheet("""
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
                self.ui.labelKesmeHiziInfo.setText("Her şey yolunda.")
            # İlerleme hızı kontrolü
            ilerleme_hizi = float(data.get('serit_inme_hizi', 0))
            if ilerleme_hizi < 10 or self.anomaly_states['IlerlemeHizi']:
                self.anomaly_states['IlerlemeHizi'] = True
                self.ui.IlerlemeHiziFrame.setStyleSheet("""
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
                self.ui.labelIlerlemeHiziInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.IlerlemeHiziFrame.setStyleSheet("""
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
                self.ui.labelIlerlemeHiziInfo.setText("Her şey yolunda.")
            # Şerit akım kontrolü (kritik)
            if serit_akim > 30 or self.anomaly_states['SeritAkim']:
                self.anomaly_states['SeritAkim'] = True
                self.ui.SeritAkimFrame.setStyleSheet("""
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
                self.ui.labelSeritAkimInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.SeritAkimFrame.setStyleSheet("""
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
                self.ui.labelSeritAkimInfo.setText("Her şey yolunda.")
            # Sıcaklık kontrolü
            sicaklik = float(data.get('ortam_sicakligi_c', 0))
            if sicaklik > 40 or self.anomaly_states['Sicaklik']:
                self.anomaly_states['Sicaklik'] = True
                self.ui.SicaklikFrame.setStyleSheet("""
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
                self.ui.labelSicaklikInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.SicaklikFrame.setStyleSheet("""
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
                self.ui.labelSicaklikInfo.setText("Her şey yolunda.")
            # Nem kontrolü
            nem = float(data.get('ortam_nem_percentage', 0))
            if nem > 80 or self.anomaly_states['Nem']:
                self.anomaly_states['Nem'] = True
                self.ui.NemFrame.setStyleSheet("""
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
                self.ui.labelNemInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.NemFrame.setStyleSheet("""
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
                self.ui.labelNemInfo.setText("Her şey yolunda.")
            # Şerit sapması kontrolü
            serit_sapmasi = float(data.get('serit_sapmasi', 0))
            if abs(serit_sapmasi) > 0.5 or self.anomaly_states['SeritSapmasi']:
                self.anomaly_states['SeritSapmasi'] = True
                self.ui.SeritSapmasiFrame.setStyleSheet("""
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
                self.ui.labelSeritSapmasiInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.SeritSapmasiFrame.setStyleSheet("""
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
                self.ui.labelSeritSapmasiInfo.setText("Her şey yolunda.")
            # Titreşim kontrolü
            vib_x = float(data.get('ivme_olcer_x_hz', 0))
            vib_y = float(data.get('ivme_olcer_y_hz', 0))
            vib_z = float(data.get('ivme_olcer_z_hz', 0))
            if vib_x > 200 or self.anomaly_states['TitresimX']:
                self.anomaly_states['TitresimX'] = True
                self.ui.TitresimXFrame.setStyleSheet("""
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
                self.ui.labelTitresimXInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.TitresimXFrame.setStyleSheet("""
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
                self.ui.labelTitresimXInfo.setText("Her şey yolunda.")
            if vib_y > 200 or self.anomaly_states['TitresimY']:
                self.anomaly_states['TitresimY'] = True
                self.ui.TitresimYFrame.setStyleSheet("""
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
                self.ui.labelTitresimYInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.TitresimYFrame.setStyleSheet("""
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
                self.ui.labelTitresimYInfo.setText("Her şey yolunda.")
            if vib_z > 200 or self.anomaly_states['TitresimZ']:
                self.anomaly_states['TitresimZ'] = True
                self.ui.TitresimZFrame.setStyleSheet("""
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
                self.ui.labelTitresimZInfo.setText(f"{current_time} tarihinde anomali tespit edildi.")
            else:
                self.ui.TitresimZFrame.setStyleSheet("""
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
                self.ui.labelTitresimZInfo.setText("Her şey yolunda.")
        except Exception as e:
            if not hasattr(self, '_anomaly_error_logged'):
                logger.warning(f"Anomali kontrol hatası (bir kere uyarı): {e}")
                self._anomaly_error_logged = True

    def update_ui(self):
        """UI bileşenlerini günceller"""
        try:
            # Başlangıçta tüm frame'leri yeşil yap ve "Her şey yolunda." mesajını göster
            green_style = """
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
            
            # Tüm frame'leri yeşil yap
            self.ui.KesmeHiziFrame.setStyleSheet(green_style)
            self.ui.IlerlemeHiziFrame.setStyleSheet(green_style)
            self.ui.SeritAkimFrame.setStyleSheet(green_style)
            self.ui.SicaklikFrame.setStyleSheet(green_style)
            self.ui.NemFrame.setStyleSheet(green_style)
            self.ui.SeritSapmasiFrame.setStyleSheet(green_style)
            self.ui.TitresimXFrame.setStyleSheet(green_style)
            self.ui.TitresimYFrame.setStyleSheet(green_style)
            self.ui.TitresimZFrame.setStyleSheet(green_style)
            
            # Tüm label'lara "Her şey yolunda." mesajını yaz
            self.ui.labelKesmeHiziInfo.setText("Her şey yolunda.")
            self.ui.labelIlerlemeHiziInfo.setText("Her şey yolunda.")
            self.ui.labelSeritAkimInfo.setText("Her şey yolunda.")
            self.ui.labelSicaklikInfo.setText("Her şey yolunda.")
            self.ui.labelNemInfo.setText("Her şey yolunda.")
            self.ui.labelSeritSapmasiInfo.setText("Her şey yolunda.")
            self.ui.labelTitresimXInfo.setText("Her şey yolunda.")
            self.ui.labelTitresimYInfo.setText("Her şey yolunda.")
            self.ui.labelTitresimZInfo.setText("Her şey yolunda.")
            
        except Exception as e:
            logger.error(f"Sensör sayfası UI güncelleme hatası: {e}")

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
        """Kontrol paneli sayfasını açar"""
        if self.parent:
            self.parent.set_active_nav("btnControlPanel")
            self.parent.showFullScreen()
            self.hide()
        else:
            from .qt_controller import SimpleGUI
            self.control_panel = SimpleGUI()
            self.control_panel.set_active_nav("btnControlPanel")
            self.control_panel.showFullScreen()
            self.hide()

    def open_positioning(self):
        """Konumlandırma sayfasını açar"""
        self.set_active_nav("btnPositioning")
        self.open_control_panel()

    def open_camera_window(self):
        """Kamera sayfasını açar"""
        if self.parent:
            if hasattr(self.parent, 'camera_window'):
                if self.parent.camera_window is None:
                    from .camera_controller import CameraWindow
                    self.parent.camera_window = CameraWindow(parent=self.parent, get_data_callback=self.get_data_callback)
                self.parent.camera_window.set_active_nav("btnCamera")
                self.parent.camera_window.showFullScreen()
                self.hide()
            else:
                from .camera_controller import CameraWindow
                self.camera_window = CameraWindow(parent=self, get_data_callback=self.get_data_callback)
                self.camera_window.set_active_nav("btnCamera")
                self.camera_window.showFullScreen()
                self.hide()
        else:
            from .camera_controller import CameraWindow
            self.camera_window = CameraWindow(parent=self, get_data_callback=self.get_data_callback)
            self.camera_window.set_active_nav("btnCamera")
            self.camera_window.showFullScreen()
            self.hide()

    def open_sensor_window(self):
        """Sensör sayfasını açar (zaten açık)"""
        self.set_active_nav("btnSensor")
        pass

    def open_monitoring_window(self):
        """İzleme sayfasını açar"""
        if self.parent:
            if hasattr(self.parent, 'monitoring_window'):
                if self.parent.monitoring_window is None:
                    from .monitoring_controller import MonitoringWindow
                    self.parent.monitoring_window = MonitoringWindow(parent=self.parent, get_data_callback=self.get_data_callback)
                self.parent.monitoring_window.set_active_nav("btnTracking")
                self.parent.monitoring_window.showFullScreen()
                self.hide()
            else:
                from .monitoring_controller import MonitoringWindow
                self.monitoring_window = MonitoringWindow(parent=self, get_data_callback=self.get_data_callback)
                self.monitoring_window.set_active_nav("btnTracking")
                self.monitoring_window.showFullScreen()
                self.hide()
        else:
            from .monitoring_controller import MonitoringWindow
            self.monitoring_window = MonitoringWindow(parent=self, get_data_callback=self.get_data_callback)
            self.monitoring_window.set_active_nav("btnTracking")
            self.monitoring_window.showFullScreen()
            self.hide()

    def reset_anomaly_states(self):
        """Tüm anomali durumlarını sıfırlar ve UI'yı günceller"""
        for key in self.anomaly_states:
            self.anomaly_states[key] = False
        self.update_ui() 