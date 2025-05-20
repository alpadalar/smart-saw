import sys
import logging
import threading
import time
from queue import Queue
from typing import Dict
from datetime import datetime
import sqlite3
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from core.logger import logger
from core.constants import TestereState
from control import ControllerType, get_controller_factory
from .control_panel_window import ControlPanelWindow

class GUILogHandler(logging.Handler):
    """GUI için özel log handler"""
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.log_queue = Queue()
        self.handler_ready = threading.Event()
        self._start_queue_handler()
    
    def emit(self, record):
        try:
            level = record.levelname
            self.log_queue.put((record.getMessage(), level))
        except Exception:
            self.handleError(record)
    
    def _start_queue_handler(self):
        def handle_logs():
            self.gui.gui_ready.wait()
            self.handler_ready.set()
            
            while True:
                try:
                    message, level = self.log_queue.get()
                    if message and level:
                        self.gui.add_log(message, level)
                except Exception as e:
                    print(f"Log queue handler error: {e}", file=sys.stderr)
                time.sleep(0.1)
        
        thread = threading.Thread(target=handle_logs, daemon=True)
        thread.start()

class SimpleGUI:
    def __init__(self, controller_factory=None):
        self.controller_factory = controller_factory or get_controller_factory()
        
        # Thread senkronizasyonu için event'ler
        self.threads_ready = threading.Event()
        self.gui_ready = threading.Event()
        
        # PyQt5 uygulamasını başlat
        self.app = QtWidgets.QApplication(sys.argv)
        self.window = ControlPanelWindow(controller=self)
        
        # Log handler'ı başlat
        self.log_handler = GUILogHandler(self)
        logger.addHandler(self.log_handler)
        
        # Veritabanı bağlantısı
        try:
            self.db = sqlite3.connect('data/total.db')
            logger.info("Veritabanı bağlantısı başarılı: data/total.db")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            self.db = None
        
        # Değişkenler
        self._last_update_time = None
        self._cutting_start_time = None
        self.last_update = time.time()
        self.update_interval = 0.1  # 100ms
        
        # Timer'ı başlat
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_loop)
        self.update_timer.start(100)  # 100ms
        
        # GUI hazır olduğunu bildir
        self.gui_ready.set()

    def start(self):
        """GUI'yi başlatır"""
        self.window.show()
        return self.app.exec_()

    def _update_loop(self):
        """Periyodik güncelleme döngüsü"""
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.last_update = current_time
            # Gerekli güncellemeleri yap

    def update_data(self, processed_data: Dict):
        """Verileri günceller"""
        if not processed_data:
            return
            
        try:
            # Kafa yüksekliği
            if 'kafa_yuksekligi_mm' in processed_data:
                self.window.ui.labelValue.setText(str(processed_data['kafa_yuksekligi_mm']))
            
            # Şerit sapması
            if 'serit_sapmasi' in processed_data:
                self.window.ui.label_2.setText(str(processed_data['serit_sapmasi']))
            
            # Şerit motor akım
            if 'serit_motor_akim_a' in processed_data:
                self.window.ui.label_7.setText(str(processed_data['serit_motor_akim_a']))
                self.window.ui.label_9.setText(str(processed_data['serit_motor_akim_a']))
            
            # Sistem durumu
            testere_durumu = processed_data.get('testere_durumu', 0)
            if testere_durumu == TestereState.KESIM_YAPILIYOR.value:
                self.window.ui.label_3.setText("Kesim Yapılıyor")
            elif testere_durumu == TestereState.BOSTA.value:
                self.window.ui.label_3.setText("Hazır")
            else:
                self.window.ui.label_3.setText("Durum Bilinmiyor")
                
        except Exception as e:
            logger.error(f"Veri güncelleme hatası: {e}")

    def add_log(self, message: str, level: str = 'INFO'):
        """Log mesajı ekler"""
        try:
            # Log mesajını pencereye ekle
            self.window.add_log_message(message, level)
        except Exception as e:
            print(f"Log ekleme hatası: {e}", file=sys.stderr) 