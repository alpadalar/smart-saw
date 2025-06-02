from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTextEdit, QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QTextCursor
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

from .qt_control_panel_interface import Ui_MainWindow

class WorkerSignals(QObject):
    """İşçi thread'leri için sinyal sınıfı"""
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QObject):
    """Arka plan işleri için worker sınıfı"""
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit((type(e), str(e), sys.exc_info()))
        finally:
            self.signals.finished.emit()

class SimpleGUI(QMainWindow):
    """Qt tabanlı kontrol paneli ana sınıfı"""
    
    # Sinyaller
    update_values_signal = pyqtSignal(dict)
    update_log_signal = pyqtSignal(str, str)
    update_modbus_status_signal = pyqtSignal(bool, str)
    update_camera_status_signal = pyqtSignal(str)
    update_camera_frame_count_signal = pyqtSignal(int)
    
    def __init__(self, controller_factory=None):
        # QApplication kontrolü
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        
        super().__init__()
        
        # UI'ı yükle
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Controller factory'yi başlat
        self.controller_factory = controller_factory or get_controller_factory()
        
        # Thread senkronizasyonu için değişkenler
        self.threads_ready = threading.Event()
        self.gui_ready = threading.Event()
        
        # Veritabanı bağlantısı
        try:
            self.db = sqlite3.connect('data/total.db')
            logger.info("Veritabanı bağlantısı başarılı: data/total.db")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            self.db = None
        
        # Kamera modülünü başlat
        self.camera = CameraModule()
        
        # Log kuyruğu
        self.log_queue = Queue()
        
        # Değişkenler
        self.current_values = {
            # Temel bilgiler
            'makine_id': "-",
            'serit_id': "-",
            'serit_dis_mm': "-",
            'serit_tip': "-",
            'serit_marka': "-",
            'serit_malz': "-",
            
            # Malzeme bilgileri
            'malzeme_cinsi': "-",
            'malzeme_sertlik': "-",
            'kesit_yapisi': "-",
            'a_mm': "-",
            'b_mm': "-",
            'c_mm': "-",
            'd_mm': "-",
            
            # Motor ve hareket bilgileri
            'kafa_yuksekligi_mm': "-",
            'serit_motor_akim_a': "-",
            'serit_motor_tork_percentage': "-",
            'inme_motor_akim_a': "-",
            'inme_motor_tork_percentage': "-",
            'serit_kesme_hizi': "-",
            'serit_inme_hizi': "-",
            
            # Basınç ve sıcaklık bilgileri
            'mengene_basinc_bar': "-",
            'serit_gerginligi_bar': "-",
            'serit_sapmasi': "-",
            'ortam_sicakligi_c': "-",
            'ortam_nem_percentage': "-",
            'sogutma_sivi_sicakligi_c': "-",
            'hidrolik_yag_sicakligi_c': "-",
            
            # İvme ölçer bilgileri
            'ivme_olcer_x': "-",
            'ivme_olcer_y': "-",
            'ivme_olcer_z': "-",
            'ivme_olcer_x_hz': "-",
            'ivme_olcer_y_hz': "-",
            'ivme_olcer_z_hz': "-",
            
            # Kesim bilgileri
            'kesilen_parca_adeti': "-",
            'testere_durumu': "-",
            'alarm_status': "-",
            'alarm_bilgisi': "-",
            'kesim_baslama': "-",
            'kesim_sure': "-",
            'cutting_time': "00:00",
            'modbus_status': "Bağlantı Yok",
            
            # Kamera durumu için değişkenler
            'camera_status': "Hazır",
            'camera_frame_count': "0"
        }
        
        self._last_update_time = None
        self._cutting_start_time = None
        self.kesim_baslama_zamani = None
        self.last_update = time.time()
        self.update_interval = 0.1  # 100ms
        
        # Timer'ları başlat
        self.setup_timers()
        
        # Sinyal bağlantılarını kur
        self.setup_connections()
        
        # GUI'yi başlat
        self.setup_gui()
        
        # GUI hazır olduğunu bildir
        self.gui_ready.set()

        # Hız Değerleri Tanımları
        self.speed_values = {
            "slow": {"cutting": 50, "descent": 25},
            "normal": {"cutting": 80, "descent": 50},
            "fast": {"cutting": 100, "descent": 65},
        }

    def setup_timers(self):
        """Timer'ları başlatır"""
        # Güncelleme timer'ı
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_loop)
        self.update_timer.start(int(self.update_interval * 1000))  # ms cinsinden
        
        # Log işleme timer'ı
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self._process_logs)
        self.log_timer.start(100)  # 100ms

    def setup_connections(self):
        """Sinyal bağlantılarını kurar"""
        # Değer güncelleme sinyali
        self.update_values_signal.connect(self._update_values)
        
        # Log sinyali
        self.update_log_signal.connect(self.add_log)
        
        # Modbus durum sinyali
        self.update_modbus_status_signal.connect(self.update_modbus_status)
        
        # Kamera durum sinyalleri
        self.update_camera_status_signal.connect(self.update_camera_status)
        self.update_camera_frame_count_signal.connect(self.update_camera_frame_count)

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
            
            # Log widget'ı
            self.ui.log_text = QTextEdit()
            self.ui.logViewerScroll.widget().layout().addWidget(self.ui.log_text)
            self.ui.log_text.setReadOnly(True)
            
            # Başlangıç değerlerini ayarla
            self.ui.labelBandCuttingSpeedValue.setText("NULL")
            self.ui.labelBandDescentSpeedValue.setText("NULL")
            
            # Başlangıç değerlerini ayarla
            self.update_ui()
            
        except Exception as e:
            logger.error(f"GUI başlatma hatası: {e}")
            logger.exception("Detaylı hata:")

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
            elif clicked_button == self.ui.btnFuzzyMode:
                self._switch_controller(ControllerType.FUZZY)
            elif clicked_button == self.ui.btnExpertSystemMode:
                self._switch_controller(ControllerType.EXPERT)
            elif clicked_button == self.ui.btnAiMode:
                self._switch_controller(ControllerType.ML)
                
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
                if clicked_button == self.ui.btnSlowSpeed:
                    self._send_manual_speed("slow")
                elif clicked_button == self.ui.btnNormalSpeed:
                    self._send_manual_speed("normal")
                elif clicked_button == self.ui.btnFastSpeed:
                    self._send_manual_speed("fast")
                
        except Exception as e:
            logger.error(f"Kesim hızı buton yönetimi hatası: {e}")
            self.add_log(f"Kesim hızı değiştirme hatası: {str(e)}", "ERROR")

    def _switch_controller(self, controller_type: Optional[ControllerType]):
        """Kontrol sistemini değiştirir"""
        try:
            if controller_type is None:
                self.controller_factory.set_controller(None)
                logger.info("Kontrol sistemi kapatıldı")
            else:
                self.controller_factory.set_controller(controller_type)
                logger.info(f"Kontrol sistemi değiştirildi: {controller_type.value}")
        except Exception as e:
            logger.error(f"Kontrol sistemi değiştirme hatası: {e}")
            logger.exception("Detaylı hata:")
            
    def show_cutting_summary(self):
        """Kesim özetini gösterir"""
        try:
            if not self.db:
                logger.error("Veritabanı bağlantısı yok")
                return
                
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_cuts,
                    AVG(cutting_time) as avg_time,
                    MIN(cutting_time) as min_time,
                    MAX(cutting_time) as max_time,
                    AVG(motor_current) as avg_current,
                    AVG(deviation) as avg_deviation
                FROM cutting_data
                WHERE cutting_time > 0
            """)
            
            result = cursor.fetchone()
            if result:
                summary = f"""
                Kesim Özeti:
                -------------
                Toplam Kesim: {result[0]}
                Ortalama Süre: {result[1]:.1f} saniye
                En Kısa Süre: {result[2]:.1f} saniye
                En Uzun Süre: {result[3]:.1f} saniye
                Ortalama Akım: {result[4]:.1f} A
                Ortalama Sapma: {result[5]:.2f} mm
                """
                
                self.add_log(summary, "INFO")
            else:
                self.add_log("Kesim verisi bulunamadı", "WARNING")
                
        except Exception as e:
            logger.error(f"Kesim özeti gösterme hatası: {e}")
            logger.exception("Detaylı hata:")

    def update_loop(self):
        """Güncelleme döngüsü"""
        # Son güncelleme zamanını kontrol et
        if self._last_update_time:
            gecen_sure = datetime.now() - self._last_update_time
            if gecen_sure.total_seconds() > 1:
                self.ui.last_update_label.setText(
                    f"Son güncelleme: {self._last_update_time.strftime('%H:%M:%S.%f')[:-3]} (Veri alınamıyor)"
                )

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
        try:
            # Temel bilgiler
            self.current_values['makine_id'] = str(processed_data.get('makine_id', '-'))
            self.current_values['serit_id'] = str(processed_data.get('serit_id', '-'))
            self.current_values['serit_dis_mm'] = str(processed_data.get('serit_dis_mm', '-'))
            self.current_values['serit_tip'] = str(processed_data.get('serit_tip', '-'))
            self.current_values['serit_marka'] = str(processed_data.get('serit_marka', '-'))
            self.current_values['serit_malz'] = str(processed_data.get('serit_malz', '-'))
            
            # Malzeme bilgileri
            self.current_values['malzeme_cinsi'] = str(processed_data.get('malzeme_cinsi', '-'))
            self.current_values['malzeme_sertlik'] = str(processed_data.get('malzeme_sertlik', '-'))
            self.current_values['kesit_yapisi'] = str(processed_data.get('kesit_yapisi', '-'))
            self.current_values['a_mm'] = str(processed_data.get('a_mm', '-'))
            self.current_values['b_mm'] = str(processed_data.get('b_mm', '-'))
            self.current_values['c_mm'] = str(processed_data.get('c_mm', '-'))
            self.current_values['d_mm'] = str(processed_data.get('d_mm', '-'))
            
            # Motor ve hareket bilgileri
            self.current_values['kafa_yuksekligi_mm'] = f"{processed_data.get('kafa_yuksekligi_mm', 0):.1f} mm"
            self.current_values['serit_motor_akim_a'] = f"{processed_data.get('serit_motor_akim_a', 0):.1f} A"
            self.current_values['serit_motor_tork_percentage'] = f"{processed_data.get('serit_motor_tork_percentage', 0):.1f} %"
            self.current_values['inme_motor_akim_a'] = f"{processed_data.get('inme_motor_akim_a', 0):.1f} A"
            self.current_values['inme_motor_tork_percentage'] = f"{processed_data.get('inme_motor_tork_percentage', 0):.1f} %"
            
            # Basınç ve sıcaklık bilgileri
            self.current_values['mengene_basinc_bar'] = f"{processed_data.get('mengene_basinc_bar', 0):.1f} bar"
            self.current_values['serit_gerginligi_bar'] = f"{processed_data.get('serit_gerginligi_bar', 0):.1f} bar"
            self.current_values['serit_sapmasi'] = f"{processed_data.get('serit_sapmasi', 0):.2f} mm"
            self.current_values['ortam_sicakligi_c'] = f"{processed_data.get('ortam_sicakligi_c', 0):.1f} °C"
            self.current_values['ortam_nem_percentage'] = f"{processed_data.get('ortam_nem_percentage', 0):.1f} %"
            self.current_values['sogutma_sivi_sicakligi_c'] = f"{processed_data.get('sogutma_sivi_sicakligi_c', 0):.1f} °C"
            self.current_values['hidrolik_yag_sicakligi_c'] = f"{processed_data.get('hidrolik_yag_sicakligi_c', 0):.1f} °C"
            
            # İvme ölçer bilgileri
            self.current_values['ivme_olcer_x'] = f"{processed_data.get('ivme_olcer_x', 0):.3f} g"
            self.current_values['ivme_olcer_y'] = f"{processed_data.get('ivme_olcer_y', 0):.3f} g"
            self.current_values['ivme_olcer_z'] = f"{processed_data.get('ivme_olcer_z', 0):.3f} g"
            self.current_values['ivme_olcer_x_hz'] = f"{processed_data.get('ivme_olcer_x_hz', 0):.1f} Hz"
            self.current_values['ivme_olcer_y_hz'] = f"{processed_data.get('ivme_olcer_y_hz', 0):.1f} Hz"
            self.current_values['ivme_olcer_z_hz'] = f"{processed_data.get('ivme_olcer_z_hz', 0):.1f} Hz"
            
            # Hız bilgileri
            self.current_values['serit_kesme_hizi'] = f"{processed_data.get('serit_kesme_hizi', 0):.1f} mm/s"
            self.current_values['serit_inme_hizi'] = f"{processed_data.get('serit_inme_hizi', 0):.1f} mm/s"
            
            # Şerit kesme hızı değerini güncelle
            cutting_speed = processed_data.get('serit_kesme_hizi')
            if cutting_speed is not None:
                self.ui.labelBandCuttingSpeedValue.setText(f"{cutting_speed:.1f}")
            else:
                self.ui.labelBandCuttingSpeedValue.setText("NULL")
                
            # Şerit inme hızı değerini güncelle
            descent_speed = processed_data.get('serit_inme_hizi')
            if descent_speed is not None:
                self.ui.labelBandDescentSpeedValue.setText(f"{descent_speed:.1f}")
            else:
                self.ui.labelBandDescentSpeedValue.setText("NULL")
            
            # Kesim bilgileri
            self.current_values['kesilen_parca_adeti'] = str(processed_data.get('kesilen_parca_adeti', 0))
            
            # Durum ve alarm bilgileri
            testere_durumu = processed_data.get('testere_durumu', 0)
            durum_text = {
                TestereState.BOSTA.value: "BOŞTA",
                TestereState.HIDROLIK_AKTIF.value: "HİDROLİK AKTİF",
                TestereState.SERIT_MOTOR_CALISIYOR.value: "ŞERİT MOTOR ÇALIŞIYOR",
                TestereState.KESIM_YAPILIYOR.value: "KESİM YAPILIYOR",
                TestereState.KESIM_BITTI.value: "KESİM BİTTİ",
                TestereState.SERIT_YUKARI_CIKIYOR.value: "ŞERİT YUKARI ÇIKIYOR",
                TestereState.MALZEME_BESLEME.value: "MALZEME BESLEME"
            }.get(testere_durumu, "BİLİNMİYOR")
            
            self.current_values['testere_durumu'] = durum_text
            self.current_values['alarm_status'] = str(processed_data.get('alarm_status', '-'))
            self.current_values['alarm_bilgisi'] = str(processed_data.get('alarm_bilgisi', '-'))
            
            # Kesim durumunu kontrol et
            if testere_durumu == TestereState.KESIM_YAPILIYOR.value:  # Kesim yapılıyor
                if not self.kesim_baslama_zamani:
                    self.kesim_baslama_zamani = datetime.now()
                    self.current_values['kesim_baslama'] = self.kesim_baslama_zamani.strftime("%H:%M:%S.%f")[:-3]
                
                # Kesim süresini güncelle
                if self.kesim_baslama_zamani:
                    sure = datetime.now() - self.kesim_baslama_zamani
                    self.current_values['kesim_sure'] = f"{int(sure.total_seconds())} saniye"
            elif testere_durumu != TestereState.KESIM_YAPILIYOR.value and self.kesim_baslama_zamani:
                # Kesim bitti, süreyi sıfırla
                self.kesim_baslama_zamani = None
                self.current_values['kesim_baslama'] = "-"
                self.current_values['kesim_sure'] = "-"
            
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
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            log_message = f"{timestamp} [{level}] {message}\n"
            
            # Log widget'ına ekle
            self.ui.log_text.append(log_message)
            
            # Maksimum 1000 satır tut
            if self.ui.log_text.document().blockCount() > 1000:
                cursor = self.ui.log_text.textCursor()
                cursor.movePosition(QTextCursor.Start)
                cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
        except Exception as e:
            logger.error(f"Log ekleme hatası: {e}")

    def update_modbus_status(self, connected: bool, ip: str):
        """Modbus durumunu günceller"""
        try:
            if connected:
                self.current_values['modbus_status'] = f"Bağlı ({ip})"
                self.ui.modbus_status_label.setStyleSheet("color: green")
            else:
                self.current_values['modbus_status'] = f"Bağlantı Yok ({ip})"
                self.ui.modbus_status_label.setStyleSheet("color: red")
        except Exception as e:
            logger.error(f"Modbus durum güncelleme hatası: {e}")

    def update_camera_status(self, status: str):
        """Kamera durumunu günceller"""
        try:
            self.current_values['camera_status'] = status
            self.ui.camera_status_label.setText(status)
        except Exception as e:
            logger.error(f"Kamera durum güncelleme hatası: {e}")

    def update_camera_frame_count(self, count: int):
        """Kamera frame sayısını günceller"""
        try:
            self.current_values['camera_frame_count'] = str(count)
            self.ui.camera_frame_count_label.setText(str(count))
        except Exception as e:
            logger.error(f"Kamera frame sayısı güncelleme hatası: {e}")

    def _toggle_recording(self):
        """Kamera kaydını başlatır/durdurur"""
        try:
            if not self.camera.is_recording:
                if self.camera.start_recording():
                    self.ui.btn_record.setText("Kayıt Durdur")
                    self.update_camera_status("Kayıt Yapılıyor")
                    self.camera.set_frame_count_callback(
                        lambda count: self.update_camera_frame_count_signal.emit(count)
                    )
            else:
                if self.camera.stop_recording():
                    self.ui.btn_record.setText("Kayıt Başlat")
                    self.update_camera_status("Hazır")
                    self.update_camera_frame_count(0)
        except Exception as e:
            logger.error(f"Kamera kayıt değiştirme hatası: {e}")

    def _toggle_viewing(self):
        """Kamera görüntüsünü başlatır/durdurur"""
        try:
            if not self.camera.is_viewing:
                if self.camera.start_viewing():
                    self.ui.btn_view.setText("Kamera Kapat")
            else:
                if self.camera.stop_viewing():
                    self.ui.btn_view.setText("Kamera İzle")
        except Exception as e:
            logger.error(f"Kamera görüntüleme değiştirme hatası: {e}")

    def update_ui(self):
        """UI bileşenlerini günceller"""
        try:
            # Temel bilgiler
            self.ui.makine_id_label.setText(self.current_values['makine_id'])
            self.ui.serit_id_label.setText(self.current_values['serit_id'])
            self.ui.serit_dis_label.setText(self.current_values['serit_dis_mm'])
            self.ui.serit_tip_label.setText(self.current_values['serit_tip'])
            self.ui.serit_marka_label.setText(self.current_values['serit_marka'])
            self.ui.serit_malz_label.setText(self.current_values['serit_malz'])
            
            # Malzeme bilgileri
            self.ui.malzeme_cinsi_label.setText(self.current_values['malzeme_cinsi'])
            self.ui.malzeme_sertlik_label.setText(self.current_values['malzeme_sertlik'])
            self.ui.kesit_yapisi_label.setText(self.current_values['kesit_yapisi'])
            self.ui.a_mm_label.setText(self.current_values['a_mm'])
            self.ui.b_mm_label.setText(self.current_values['b_mm'])
            self.ui.c_mm_label.setText(self.current_values['c_mm'])
            self.ui.d_mm_label.setText(self.current_values['d_mm'])
            
            # Motor ve hareket bilgileri
            self.ui.kafa_yuksekligi_label.setText(self.current_values['kafa_yuksekligi_mm'])
            self.ui.serit_motor_akim_label.setText(self.current_values['serit_motor_akim_a'])
            self.ui.serit_motor_tork_label.setText(self.current_values['serit_motor_tork_percentage'])
            self.ui.inme_motor_akim_label.setText(self.current_values['inme_motor_akim_a'])
            self.ui.inme_motor_tork_label.setText(self.current_values['inme_motor_tork_percentage'])
            self.ui.serit_kesme_hizi_label.setText(self.current_values['serit_kesme_hizi'])
            self.ui.serit_inme_hizi_label.setText(self.current_values['serit_inme_hizi'])
            
            # Basınç ve sıcaklık bilgileri
            self.ui.mengene_basinc_label.setText(self.current_values['mengene_basinc_bar'])
            self.ui.serit_gerginlik_label.setText(self.current_values['serit_gerginligi_bar'])
            self.ui.serit_sapma_label.setText(self.current_values['serit_sapmasi'])
            self.ui.ortam_sicaklik_label.setText(self.current_values['ortam_sicakligi_c'])
            self.ui.ortam_nem_label.setText(self.current_values['ortam_nem_percentage'])
            self.ui.sogutma_sivi_sicaklik_label.setText(self.current_values['sogutma_sivi_sicakligi_c'])
            self.ui.hidrolik_yag_sicaklik_label.setText(self.current_values['hidrolik_yag_sicakligi_c'])
            
            # İvme ölçer bilgileri
            self.ui.ivme_olcer_x_label.setText(self.current_values['ivme_olcer_x'])
            self.ui.ivme_olcer_y_label.setText(self.current_values['ivme_olcer_y'])
            self.ui.ivme_olcer_z_label.setText(self.current_values['ivme_olcer_z'])
            self.ui.ivme_olcer_x_hz_label.setText(self.current_values['ivme_olcer_x_hz'])
            self.ui.ivme_olcer_y_hz_label.setText(self.current_values['ivme_olcer_y_hz'])
            self.ui.ivme_olcer_z_hz_label.setText(self.current_values['ivme_olcer_z_hz'])
            
            # Kesim bilgileri
            self.ui.kesilen_parca_adet_label.setText(self.current_values['kesilen_parca_adeti'])
            self.ui.testere_durum_label.setText(self.current_values['testere_durumu'])
            self.ui.alarm_status_label.setText(self.current_values['alarm_status'])
            self.ui.alarm_bilgi_label.setText(self.current_values['alarm_bilgisi'])
            self.ui.kesim_baslama_label.setText(self.current_values['kesim_baslama'])
            self.ui.kesim_sure_label.setText(self.current_values['kesim_sure'])
            self.ui.cutting_time_label.setText(self.current_values['cutting_time'])
            self.ui.modbus_status_label.setText(self.current_values['modbus_status'])
            
            # Kamera durumu
            self.ui.camera_status_label.setText(self.current_values['camera_status'])
            self.ui.camera_frame_count_label.setText(self.current_values['camera_frame_count'])
            
            # Son güncelleme zamanı
            if self._last_update_time:
                self.ui.last_update_label.setText(
                    f"Son güncelleme: {self._last_update_time.strftime('%H:%M:%S.%f')[:-3]}"
                )
            
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
                    processed_data.get('modbus_ip', '192.168.11.186')
                )
            
            # Testere durumunu güncelle
            testere_durumu = int(processed_data.get('testere_durumu', 0))
            durum_text = {
                TestereState.BOSTA.value: "BOŞTA",
                TestereState.HIDROLIK_AKTIF.value: "HİDROLİK AKTİF",
                TestereState.SERIT_MOTOR_CALISIYOR.value: "ŞERİT MOTOR ÇALIŞIYOR",
                TestereState.KESIM_YAPILIYOR.value: "KESİM YAPILIYOR",
                TestereState.KESIM_BITTI.value: "KESİM BİTTİ",
                TestereState.SERIT_YUKARI_CIKIYOR.value: "ŞERİT YUKARI ÇIKIYOR",
                TestereState.MALZEME_BESLEME.value: "MALZEME BESLEME"
            }.get(testere_durumu, "BİLİNMİYOR")
            
            self.current_values['testere_durumu'] = durum_text
            
            # Duruma göre label rengini güncelle
            durum_renkleri = {
                TestereState.BOSTA.value: 'gray',      # BOŞTA
                TestereState.HIDROLIK_AKTIF.value: 'orange',    # HİDROLİK AKTİF
                TestereState.SERIT_MOTOR_CALISIYOR.value: 'blue',      # ŞERİT MOTOR ÇALIŞIYOR
                TestereState.KESIM_YAPILIYOR.value: 'red',       # KESİM YAPILIYOR
                TestereState.KESIM_BITTI.value: 'green',     # KESİM BİTTİ
                TestereState.SERIT_YUKARI_CIKIYOR.value: 'purple',    # ŞERİT YUKARI ÇIKIYOR
                TestereState.MALZEME_BESLEME.value: 'brown'      # MALZEME BESLEME
            }
            self.ui.testere_durum_label.setStyleSheet(f"color: {durum_renkleri.get(testere_durumu, 'black')}")
            
            # Kesim durumunu kontrol et
            if testere_durumu == TestereState.KESIM_YAPILIYOR.value:  # Kesim yapılıyor
                if not self._cutting_start_time:
                    self._cutting_start_time = datetime.now()
                    self.current_values['kesim_baslama'] = self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3]
                
                # Geçen süreyi hesapla ve göster
                elapsed = datetime.now() - self._cutting_start_time
                minutes = int(elapsed.total_seconds() // 60)
                seconds = int(elapsed.total_seconds() % 60)
                milliseconds = int(elapsed.total_seconds() * 1000) % 1000
                self.current_values['cutting_time'] = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
                
            elif testere_durumu != TestereState.KESIM_YAPILIYOR.value and self._cutting_start_time:
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
        if testere_durumu == TestereState.KESIM_YAPILIYOR.value:  # Kesim yapılıyor
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

    def start(self):
        """GUI'yi başlatır ve gösterir"""
        try:
            # GUI'yi göster
            self.show()
            
            # GUI hazır olduğunu bildir
            self.gui_ready.set()
            
            # QApplication event döngüsünü başlat
            if QApplication.instance():
                QApplication.instance().exec_()
            
        except Exception as e:
            logger.error(f"GUI başlatma hatası: {e}")
            logger.exception("Detaylı hata:") 

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
            logger.info(f"Kesme hızı gönderildi ({speed_level}): {cutting_speed:.1f} mm/s")
            self.add_log(f"Kesme hızı ayarlandı ({speed_level}): {cutting_speed:.1f} mm/s", "INFO")
            
            # İnme hızını gönder
            reverse_calculate_value(modbus_client, descent_speed, 'serit_inme_hizi', False)
            logger.info(f"İnme hızı gönderildi ({speed_level}): {descent_speed:.1f} mm/s")
            self.add_log(f"İnme hızı ayarlandı ({speed_level}): {descent_speed:.1f} mm/s", "INFO")

        except Exception as e:
            logger.error(f"Hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            self.add_log(f"Hız ayarlama hatası: {str(e)}", "ERROR") 