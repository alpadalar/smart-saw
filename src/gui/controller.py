# src/gui/controller.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
from datetime import datetime
from typing import Dict, Optional
from queue import Queue
import logging
import threading
import sys
import queue
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from tkhtmlview import HTMLLabel
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import webbrowser
from tkwebview2.tkwebview2 import WebView2

from core.logger import logger
from core.constants import TestereState, KATSAYI
from control import ControllerType, get_controller_factory
from models import ProcessedData
from utils.helpers import reverse_calculate_value
from core.camera import CameraModule

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
            # GUI hazır olana kadar bekle
            self.gui.gui_ready.wait()
            self.handler_ready.set()
            
            while True:
                try:
                    message, level = self.log_queue.get()
                    if message and level:
                        if self.gui and self.gui.root:
                            self.gui.root.after(0, self.gui.add_log, message, level)
                except Exception as e:
                    # Log hatalarını standart error'a yaz
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
        
        # Veritabanı bağlantısı
        try:
            import sqlite3
            self.db = sqlite3.connect('data/total.db')
            logger.info("Veritabanı bağlantısı başarılı: data/total.db")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            self.db = None
        
        # Kamera modülünü başlat
        self.camera = CameraModule()
        
        # Ana pencere
        self.root = tk.Tk()
        self.root.title("Smart Saw Control Panel")
        self.root.geometry("1366x720")
        
        # Değişkenler
        self.current_values = {
            # Temel bilgiler
            'makine_id': tk.StringVar(value="-"),
            'serit_id': tk.StringVar(value="-"),
            'serit_dis_mm': tk.StringVar(value="-"),
            'serit_tip': tk.StringVar(value="-"),
            'serit_marka': tk.StringVar(value="-"),
            'serit_malz': tk.StringVar(value="-"),
            
            # Malzeme bilgileri
            'malzeme_cinsi': tk.StringVar(value="-"),
            'malzeme_sertlik': tk.StringVar(value="-"),
            'kesit_yapisi': tk.StringVar(value="-"),
            'a_mm': tk.StringVar(value="-"),
            'b_mm': tk.StringVar(value="-"),
            'c_mm': tk.StringVar(value="-"),
            'd_mm': tk.StringVar(value="-"),
            
            # Motor ve hareket bilgileri
            'kafa_yuksekligi_mm': tk.StringVar(value="-"),
            'serit_motor_akim_a': tk.StringVar(value="-"),
            'serit_motor_tork_percentage': tk.StringVar(value="-"),
            'inme_motor_akim_a': tk.StringVar(value="-"),
            'inme_motor_tork_percentage': tk.StringVar(value="-"),
            'serit_kesme_hizi': tk.StringVar(value="-"),
            'serit_inme_hizi': tk.StringVar(value="-"),
            
            # Basınç ve sıcaklık bilgileri
            'mengene_basinc_bar': tk.StringVar(value="-"),
            'serit_gerginligi_bar': tk.StringVar(value="-"),
            'serit_sapmasi': tk.StringVar(value="-"),
            'ortam_sicakligi_c': tk.StringVar(value="-"),
            'ortam_nem_percentage': tk.StringVar(value="-"),
            'sogutma_sivi_sicakligi_c': tk.StringVar(value="-"),
            'hidrolik_yag_sicakligi_c': tk.StringVar(value="-"),
            
            # İvme ölçer bilgileri
            'ivme_olcer_x': tk.StringVar(value="-"),
            'ivme_olcer_y': tk.StringVar(value="-"),
            'ivme_olcer_z': tk.StringVar(value="-"),
            'ivme_olcer_x_hz': tk.StringVar(value="-"),
            'ivme_olcer_y_hz': tk.StringVar(value="-"),
            'ivme_olcer_z_hz': tk.StringVar(value="-"),
            
            # Kesim bilgileri
            'kesilen_parca_adeti': tk.StringVar(value="-"),
            'testere_durumu': tk.StringVar(value="-"),
            'alarm_status': tk.StringVar(value="-"),
            'alarm_bilgisi': tk.StringVar(value="-"),
            'kesim_baslama': tk.StringVar(value="-"),
            'kesim_sure': tk.StringVar(value="-"),
            'cutting_time': tk.StringVar(value="00:00"),
            'modbus_status': tk.StringVar(value="Bağlantı Yok"),
            
            # Kamera durumu için değişkenler
            'camera_status': tk.StringVar(value="Hazır"),
            'camera_frame_count': tk.StringVar(value="0")
        }
        
        self.current_controller = tk.StringVar(value="Kontrol Sistemi Kapalı")
        self._last_update_time = None
        self._cutting_start_time = None
        self.kesim_baslama_zamani = None
        self.value_labels = {}
        self.log_queue = Queue()
        self.last_update = time.time()
        self.update_interval = 0.1  # 100ms
        
        # GUI bileşenlerini oluştur
        self._create_widgets()
        self._setup_update_loop()
        
        # Log handler'ı başlat
        self.log_handler = GUILogHandler(self)
        logger.addHandler(self.log_handler)
        self._process_logs()
        
        # GUI hazır olduğunu bildir
        self.gui_ready.set()

    def _process_logs(self):
        """Log kuyruğunu işler"""
        try:
            while not self.log_queue.empty():
                message, level = self.log_queue.get_nowait()
                if message and level:
                    self.add_log(message, level)
        except Exception as e:
            print(f"Log işleme hatası: {e}", file=sys.stderr)
        finally:
            # Her 100ms'de bir tekrar kontrol et
            self.root.after(100, self._process_logs)

    def _create_widgets(self):
        """GUI bileşenlerini oluşturur"""
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sol panel (Kontrol ve Bilgiler)
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Üst kısım - Kontrol ve Modbus Durumu
        top_frame = ttk.Frame(left_panel)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Testere Durum Göstergesi
        testere_frame = ttk.LabelFrame(top_frame, text="Testere Durumu", padding=(5, 5))
        testere_frame.pack(fill=tk.X, pady=(0, 5))
        
        testere_status_frame = ttk.Frame(testere_frame)
        testere_status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(testere_status_frame, text="Durum:").pack(side=tk.LEFT, padx=5)
        self.testere_status_label = ttk.Label(
            testere_status_frame,
            textvariable=self.current_values['testere_durumu'],
            font=('TkDefaultFont', 10, 'bold')
        )
        self.testere_status_label.pack(side=tk.LEFT, padx=5)
        
        # Modbus Durum Göstergesi
        status_control_frame = ttk.Frame(top_frame)
        status_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Modbus Durum Göstergesi
        modbus_frame = ttk.LabelFrame(status_control_frame, text="Modbus Durumu", padding=(5, 5))
        modbus_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        modbus_status_frame = ttk.Frame(modbus_frame)
        modbus_status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.modbus_status = ttk.Label(modbus_status_frame, textvariable=self.current_values['modbus_status'])
        self.modbus_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Kontrol Sistemi
        control_frame = ttk.LabelFrame(top_frame, text="Kontrol Sistemi", padding=(5, 5))
        control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(control_frame, text="Aktif Sistem:").pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, textvariable=self.current_controller).pack(side=tk.LEFT, padx=5)
        
        # Manuel kontrol butonu
        ttk.Button(
            control_frame,
            text="Manuel",
            command=lambda: self._switch_controller(None)
        ).pack(side=tk.LEFT, padx=2)
        
        # Otomatik kontrol butonları
        ttk.Button(
            control_frame,
            text="Fuzzy",
            command=lambda: self._switch_controller(ControllerType.FUZZY)
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="Lineer",
            command=lambda: self._switch_controller(ControllerType.LINEAR)
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="Expert",
            command=lambda: self._switch_controller(ControllerType.EXPERT)
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="ML",
            command=lambda: self._switch_controller(ControllerType.ML)
        ).pack(side=tk.LEFT, padx=2)

        # Katsayı Ayarı Frame'i
        coefficient_frame = ttk.LabelFrame(left_panel, text="Katsayı Ayarı", padding=(5, 5))
        coefficient_frame.pack(fill=tk.X, pady=5)
        
        # Katsayı değeri için Entry ve Label
        ttk.Label(coefficient_frame, text="Katsayı:").pack(side=tk.LEFT, padx=5)
        self.coefficient_var = tk.StringVar(value="1.0")
        self.coefficient_entry = ttk.Entry(coefficient_frame, textvariable=self.coefficient_var, width=8)
        self.coefficient_entry.pack(side=tk.LEFT, padx=5)
        
        # Uygula butonu
        ttk.Button(
            coefficient_frame,
            text="Uygula",
            command=lambda: self._on_coefficient_change(self.coefficient_var.get())
        ).pack(side=tk.LEFT, padx=5)
        
        # Kesim Bilgileri
        cut_frame = ttk.LabelFrame(left_panel, text="Kesim Bilgileri", padding=(5, 5))
        cut_frame.pack(fill=tk.X, pady=5)
        
        # Mevcut Kesim Bilgileri
        current_cut_frame = ttk.Frame(cut_frame)
        current_cut_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(current_cut_frame, text="Mevcut Kesim:").pack(side=tk.LEFT, padx=2)
        self.current_cut_start = ttk.Label(current_cut_frame, text="-")
        self.current_cut_start.pack(side=tk.LEFT, padx=5)
        
        # Önceki Kesim Bilgileri
        prev_cut_frame = ttk.Frame(cut_frame)
        prev_cut_frame.pack(fill=tk.X, pady=2)
        
        # Başlangıç
        ttk.Label(prev_cut_frame, text="Önceki Başlangıç:").pack(side=tk.LEFT, padx=2)
        self.prev_cut_start = ttk.Label(prev_cut_frame, text="-")
        self.prev_cut_start.pack(side=tk.LEFT, padx=5)
        
        # Bitiş
        ttk.Label(prev_cut_frame, text="Önceki Bitiş:").pack(side=tk.LEFT, padx=2)
        self.prev_cut_end = ttk.Label(prev_cut_frame, text="-")
        self.prev_cut_end.pack(side=tk.LEFT, padx=5)
        
        # Toplam Süre
        ttk.Label(prev_cut_frame, text="Toplam Süre:").pack(side=tk.LEFT, padx=2)
        self.prev_cut_duration = ttk.Label(prev_cut_frame, text="-")
        self.prev_cut_duration.pack(side=tk.LEFT, padx=5)
        
        # Kesim Özeti Butonu - son satırın sağına ekle
        self.summary_button = ttk.Button(prev_cut_frame, text="Kesim Özeti", command=self.show_cutting_summary)
        self.summary_button.pack(side=tk.RIGHT, padx=5)
        
        # Sensör Değerleri Grid'i
        values_frame = ttk.Frame(left_panel)
        values_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Sol grid (Motor ve Hareket)
        left_grid = ttk.LabelFrame(values_frame, text="Motor ve Hareket", padding=(5, 5))
        left_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        self._create_value_grid(left_grid, [
            ('serit_motor_akim_a', 'Motor Akım (A)'),
            ('serit_motor_tork_percentage', 'Motor Tork (%)'),
            ('serit_kesme_hizi', 'Kesme Hızı (mm/s)'),
            ('serit_inme_hizi', 'İnme Hızı (mm/s)'),
            ('serit_sapmasi', 'Sapma (mm)'),
            ('kafa_yuksekligi_mm', 'Kafa Yüksekliği (mm)')
        ])
        
        # Orta grid (Basınç ve Sıcaklık)
        middle_grid = ttk.LabelFrame(values_frame, text="Basınç ve Sıcaklık", padding=(5, 5))
        middle_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        self._create_value_grid(middle_grid, [
            ('mengene_basinc_bar', 'Mengene Basınç (bar)'),
            ('serit_gerginligi_bar', 'Şerit Gerginlik (bar)'),
            ('ortam_sicakligi_c', 'Ortam Sıcaklık (°C)'),
            ('ortam_nem_percentage', 'Ortam Nem (%)'),
            ('sogutma_sivi_sicakligi_c', 'Soğutma Sıvı (°C)'),
            ('hidrolik_yag_sicakligi_c', 'Hidrolik Yağ (°C)')
        ])
        
        # Sağ grid (İvme Ölçer)
        right_grid = ttk.LabelFrame(values_frame, text="İvme Ölçer", padding=(5, 5))
        right_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        self._create_value_grid(right_grid, [
            ('ivme_olcer_x', 'X İvme (g)'),
            ('ivme_olcer_y', 'Y İvme (g)'),
            ('ivme_olcer_z', 'Z İvme (g)'),
            ('ivme_olcer_x_hz', 'X Frekans (Hz)'),
            ('ivme_olcer_y_hz', 'Y Frekans (Hz)'),
            ('ivme_olcer_z_hz', 'Z Frekans (Hz)')
        ])
        
        # Kamera Kontrolleri
        camera_frame = ttk.LabelFrame(left_panel, text="Kamera Kontrolleri", padding=(5, 5))
        camera_frame.pack(fill=tk.X, pady=5)
        
        # Kamera durum bilgisi
        camera_status_frame = ttk.Frame(camera_frame)
        camera_status_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(camera_status_frame, text="Durum:").pack(side=tk.LEFT, padx=5)
        ttk.Label(camera_status_frame, textvariable=self.current_values['camera_status']).pack(side=tk.LEFT, padx=5)
        ttk.Label(camera_status_frame, text="Frame:").pack(side=tk.LEFT, padx=5)
        ttk.Label(camera_status_frame, textvariable=self.current_values['camera_frame_count']).pack(side=tk.LEFT, padx=5)
        
        # Kamera kontrol butonları
        camera_buttons_frame = ttk.Frame(camera_frame)
        camera_buttons_frame.pack(fill=tk.X, pady=2)
        
        self.record_button = ttk.Button(
            camera_buttons_frame,
            text="Kayıt Başlat",
            command=self._toggle_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        self.view_button = ttk.Button(
            camera_buttons_frame,
            text="Kamera İzle",
            command=self._toggle_viewing
        )
        self.view_button.pack(side=tk.LEFT, padx=5)
        
        # Sağ panel (Log Görüntüleyici)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Log alanı
        log_frame = ttk.LabelFrame(right_panel, text="Log Görüntüleyici", padding=(5, 5))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text widget'ı
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, width=50, height=30)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Tag'leri tanımla
        self.log_text.tag_configure('INFO', foreground='black')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        
        # Alt durum çubuğu
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        self.status_label = ttk.Label(
            status_frame,
            text=f"Son güncelleme: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}"
        )
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(
            status_frame,
            text="Uygulamayı Kapat",
            command=self._quit
        ).pack(side=tk.RIGHT)

    def _create_value_grid(self, parent, fields):
        """Değer grid'ini oluşturur"""
        for i, (field, label) in enumerate(fields):
            # Etiket ve değer göstergesini oluştur
            ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.E, padx=5, pady=2)
            value_label = ttk.Label(parent, textvariable=self.current_values[field])
            value_label.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.value_labels[field] = value_label

    def _switch_controller(self, controller_type: ControllerType):
        """Kontrol sistemini değiştirir"""
        try:
            # Önce mevcut kontrolcüyü kapat
            self.controller_factory.set_controller(None)
            time.sleep(0.1)  # Kısa bir bekleme
            
            # Yeni kontrolcüyü etkinleştir
            if controller_type == ControllerType.FUZZY:
                self.controller_factory.set_controller(ControllerType.FUZZY)
                self.current_controller.set("Fuzzy Kontrol Aktif")
                logger.info("Fuzzy kontrol aktif edildi")
                
            elif controller_type == ControllerType.LINEAR:
                self.controller_factory.set_controller(ControllerType.LINEAR)
                self.current_controller.set("Lineer Kontrol Aktif")
                logger.info("Lineer kontrol aktif edildi")
                
            elif controller_type == ControllerType.EXPERT:
                self.controller_factory.set_controller(ControllerType.EXPERT)
                self.current_controller.set("Expert Kontrol Aktif")
                logger.info("Expert kontrol aktif edildi")
                
            elif controller_type == ControllerType.ML:
                self.controller_factory.set_controller(ControllerType.ML)
                self.current_controller.set("ML Kontrol Aktif")
                logger.info("ML kontrol aktif edildi")
                
            else:
                self.current_controller.set("Kontrol Sistemi Kapalı")
                logger.info("Manuel kontrol aktif edildi")
                
        except Exception as e:
            logger.error(f"Kontrol sistemi değiştirme hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            self._disable_controller()

    def _disable_controller(self):
        """Kontrol sistemini kapatır"""
        try:
            self.controller_factory.set_controller(None)  # Aktif kontrolcüyü kaldır
            self.current_controller.set("Kontrol Sistemi Kapalı")
            logger.info("Kontrol sistemi kapatıldı")
        except Exception as e:
            logger.error(f"Kontrol sistemi kapatılamadı: {str(e)}")

    def _update_values(self, processed_data: Dict):
        """Gösterilen değerleri günceller"""
        # Temel bilgiler
        self.current_values['makine_id'].set(str(processed_data.get('makine_id', '-')))
        self.current_values['serit_id'].set(str(processed_data.get('serit_id', '-')))
        self.current_values['serit_dis_mm'].set(str(processed_data.get('serit_dis_mm', '-')))
        self.current_values['serit_tip'].set(str(processed_data.get('serit_tip', '-')))
        self.current_values['serit_marka'].set(str(processed_data.get('serit_marka', '-')))
        self.current_values['serit_malz'].set(str(processed_data.get('serit_malz', '-')))
        
        # Malzeme bilgileri
        self.current_values['malzeme_cinsi'].set(str(processed_data.get('malzeme_cinsi', '-')))
        self.current_values['malzeme_sertlik'].set(str(processed_data.get('malzeme_sertlik', '-')))
        self.current_values['kesit_yapisi'].set(str(processed_data.get('kesit_yapisi', '-')))
        self.current_values['a_mm'].set(str(processed_data.get('a_mm', '-')))
        self.current_values['b_mm'].set(str(processed_data.get('b_mm', '-')))
        self.current_values['c_mm'].set(str(processed_data.get('c_mm', '-')))
        self.current_values['d_mm'].set(str(processed_data.get('d_mm', '-')))
        
        # Motor ve hareket bilgileri
        self.current_values['kafa_yuksekligi_mm'].set(f"{processed_data.get('kafa_yuksekligi_mm', 0):.1f} mm")
        self.current_values['serit_motor_akim_a'].set(f"{processed_data.get('serit_motor_akim_a', 0):.1f} A")
        self.current_values['serit_motor_tork_percentage'].set(f"{processed_data.get('serit_motor_tork_percentage', 0):.1f} %")
        self.current_values['inme_motor_akim_a'].set(f"{processed_data.get('inme_motor_akim_a', 0):.1f} A")
        self.current_values['inme_motor_tork_percentage'].set(f"{processed_data.get('inme_motor_tork_percentage', 0):.1f} %")
        
        # Basınç ve sıcaklık bilgileri
        self.current_values['mengene_basinc_bar'].set(f"{processed_data.get('mengene_basinc_bar', 0):.1f} bar")
        self.current_values['serit_gerginligi_bar'].set(f"{processed_data.get('serit_gerginligi_bar', 0):.1f} bar")
        self.current_values['serit_sapmasi'].set(f"{processed_data.get('serit_sapmasi', 0):.2f} mm")
        self.current_values['ortam_sicakligi_c'].set(f"{processed_data.get('ortam_sicakligi_c', 0):.1f} °C")
        self.current_values['ortam_nem_percentage'].set(f"{processed_data.get('ortam_nem_percentage', 0):.1f} %")
        self.current_values['sogutma_sivi_sicakligi_c'].set(f"{processed_data.get('sogutma_sivi_sicakligi_c', 0):.1f} °C")
        self.current_values['hidrolik_yag_sicakligi_c'].set(f"{processed_data.get('hidrolik_yag_sicakligi_c', 0):.1f} °C")
        
        # İvme ölçer bilgileri
        self.current_values['ivme_olcer_x'].set(f"{processed_data.get('ivme_olcer_x', 0):.3f} g")
        self.current_values['ivme_olcer_y'].set(f"{processed_data.get('ivme_olcer_y', 0):.3f} g")
        self.current_values['ivme_olcer_z'].set(f"{processed_data.get('ivme_olcer_z', 0):.3f} g")
        self.current_values['ivme_olcer_x_hz'].set(f"{processed_data.get('ivme_olcer_x_hz', 0):.1f} Hz")
        self.current_values['ivme_olcer_y_hz'].set(f"{processed_data.get('ivme_olcer_y_hz', 0):.1f} Hz")
        self.current_values['ivme_olcer_z_hz'].set(f"{processed_data.get('ivme_olcer_z_hz', 0):.1f} Hz")
        
        # Hız bilgileri
        self.current_values['serit_kesme_hizi'].set(f"{processed_data.get('serit_kesme_hizi', 0):.1f} mm/s")
        self.current_values['serit_inme_hizi'].set(f"{processed_data.get('serit_inme_hizi', 0):.1f} mm/s")
        
        # Kesim bilgileri
        self.current_values['kesilen_parca_adeti'].set(str(processed_data.get('kesilen_parca_adeti', 0)))
        
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
        
        self.current_values['testere_durumu'].set(durum_text)
        self.current_values['alarm_status'].set(str(processed_data.get('alarm_status', '-')))
        self.current_values['alarm_bilgisi'].set(str(processed_data.get('alarm_bilgisi', '-')))
        
        # Kesim durumunu kontrol et
        if testere_durumu == TestereState.KESIM_YAPILIYOR.value:  # Kesim yapılıyor
            if not self.kesim_baslama_zamani:
                self.kesim_baslama_zamani = datetime.now()
                self.current_values['kesim_baslama'].set(
                    self.kesim_baslama_zamani.strftime("%H:%M:%S.%f")[:-3]
                )
            
            # Kesim süresini güncelle
            if self.kesim_baslama_zamani:
                sure = datetime.now() - self.kesim_baslama_zamani
                self.current_values['kesim_sure'].set(
                    f"{int(sure.total_seconds())} saniye"
                )
        elif testere_durumu != TestereState.KESIM_YAPILIYOR.value and self.kesim_baslama_zamani:
            # Kesim bitti, süreyi sıfırla
            self.kesim_baslama_zamani = None
            self.current_values['kesim_baslama'].set("-")
            self.current_values['kesim_sure'].set("-")
        
        # Son güncelleme zamanını kaydet
        self._last_update_time = datetime.now()
        self.status_label.config(
            text=f"Son güncelleme: {self._last_update_time.strftime('%H:%M:%S.%f')[:-3]}"
        )

    def _setup_update_loop(self):
        """Güncelleme döngüsünü başlatır"""
        def update_loop():
            # Son güncelleme zamanını kontrol et
            if self._last_update_time:
                gecen_sure = datetime.now() - self._last_update_time
                if gecen_sure.total_seconds() > 1:
                    self.status_label.config(
                        text=f"Son güncelleme: {self._last_update_time.strftime('%H:%M:%S.%f')[:-3]} (Veri alınamıyor)"
                    )
            
            # Her 100ms'de bir güncelle
            self.root.after(100, update_loop)
        
        update_loop()

    def _quit(self):
        """Uygulamayı kapatır"""
        # Kamera modülünü kapat
        if hasattr(self, 'camera'):
            self.camera.close()
        
        # Log handler'ı kaldır
        logger.removeHandler(self.log_handler)
        self.root.quit()

    def start(self):
        """GUI'yi başlat ve thread'lerin hazır olmasını bekle"""
        # Log handler'ı ekle
        logger.addHandler(self.log_handler)
        
        def check_threads():
            if not self.threads_ready.is_set():
                # Her 100ms'de bir kontrol et
                self.root.after(100, check_threads)
                return
            # Thread'ler hazır, normal güncelleme döngüsünü başlat
            self._start_normal_operation()
        
        # Thread'leri kontrol etmeye başla
        self.root.after(0, check_threads)
        # Ana döngüyü başlat
        self.root.mainloop()

    def _start_normal_operation(self):
        """Normal GUI operasyonlarını başlat"""
        logger.info("Tüm thread'ler hazır, GUI normal operasyona geçiyor")
        # Normal operasyonları başlat...

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
            
            self.current_values['testere_durumu'].set(durum_text)
            
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
            self.testere_status_label.configure(foreground=durum_renkleri.get(testere_durumu, 'black'))
            
            # Kesim durumunu kontrol et
            if testere_durumu == TestereState.KESIM_YAPILIYOR.value:  # Kesim yapılıyor
                if not self._cutting_start_time:
                    self._cutting_start_time = datetime.now()
                    self.current_cut_start.config(text=self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3])
                
                # Geçen süreyi hesapla ve göster
                elapsed = datetime.now() - self._cutting_start_time
                minutes = int(elapsed.total_seconds() // 60)
                seconds = int(elapsed.total_seconds() % 60)
                milliseconds = int(elapsed.total_seconds() * 1000) % 1000
                self.current_values['cutting_time'].set(f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}")
                
            elif testere_durumu != TestereState.KESIM_YAPILIYOR.value and self._cutting_start_time:
                # Kesim bitti, süreleri kaydet
                end_time = datetime.now()
                elapsed = end_time - self._cutting_start_time
                
                # Önceki kesim bilgilerini güncelle
                self.prev_cut_start.config(text=self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3])
                self.prev_cut_end.config(text=end_time.strftime('%H:%M:%S.%f')[:-3])
                self.prev_cut_duration.config(text=f"{int(elapsed.total_seconds() // 60):02d}:{int(elapsed.total_seconds() % 60):02d}")
                
                # Kesim bilgilerini sıfırla
                self._cutting_start_time = None
                self.current_cut_start.config(text="-")
                self.current_values['cutting_time'].set("00:00")
            
            # Diğer değerleri güncelle
            self._update_values(processed_data)
            
            # Kritik değerleri kontrol et
            self._check_critical_values(processed_data)
            
            # Kamera frame sayısını güncelle
            if hasattr(self, 'camera') and self.camera.is_recording:
                self.current_values['camera_frame_count'].set(str(self.camera.frame_count))
            
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

    def _send_manual_speed(self, speed_type: str):
        """Tek bir hızı gönderir"""
        try:
            # Modbus client'ı al
            if not self.controller_factory or not self.controller_factory.modbus_client:
                logger.error("Modbus bağlantısı bulunamadı")
                return
            
            modbus_client = self.controller_factory.modbus_client
            
            if speed_type == 'inme':
                # İnme hızını gönder
                inme_hizi_str = self.inme_hizi_entry.get().strip()
                if inme_hizi_str:
                    try:
                        inme_hizi = float(inme_hizi_str)
                        inme_hizi_is_negative = inme_hizi < 0
                        reverse_calculate_value(modbus_client, inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
                        logger.info(f"İnme hızı gönderildi: {inme_hizi:.2f} mm/s")
                    except ValueError:
                        logger.error("Geçersiz inme hızı değeri")
                
            elif speed_type == 'kesme':
                # Kesme hızını gönder
                kesme_hizi_str = self.kesme_hizi_entry.get().strip()
                if kesme_hizi_str:
                    try:
                        kesme_hizi = float(kesme_hizi_str)
                        kesme_hizi_is_negative = kesme_hizi < 0
                        reverse_calculate_value(modbus_client, kesme_hizi, 'serit_kesme_hizi', kesme_hizi_is_negative)
                        logger.info(f"Kesme hızı gönderildi: {kesme_hizi:.2f} mm/s")
                    except ValueError:
                        logger.error("Geçersiz kesme hızı değeri")
            
        except Exception as e:
            logger.error(f"Hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")

    def _send_all_speeds(self):
        """Tüm hızları gönderir"""
        try:
            # Önce kesme hızını gönder
            self._send_manual_speed('kesme')
            
            # Modbus yazma işlemleri arasında biraz bekle
            self.root.after(110)  # 110ms bekle
            
            # Sonra inme hızını gönder
            self._send_manual_speed('inme')
            
        except Exception as e:
            logger.error(f"Toplu hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")

    def update_modbus_status(self, is_connected: bool, ip_address: str = None):
        """Modbus bağlantı durumunu günceller"""
        try:
            if is_connected:
                self.current_values['modbus_status'].set(f"Bağlı - {ip_address}")
            else:
                self.current_values['modbus_status'].set("Bağlantı Yok")
        except Exception as e:
            logger.error(f"Modbus durum güncelleme hatası: {str(e)}")
            logger.exception("Detaylı hata:")

    def add_log(self, message: str, level: str = 'INFO'):
        """Thread-safe log ekleme"""
        try:
            if not hasattr(self, 'log_text'):
                return
                
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            log_message = f"{timestamp} [{level}] {message}\n"
            
            self.log_text.insert(tk.END, log_message, level)
            self.log_text.see(tk.END)
            
            # Maksimum 1000 satır tut
            line_count = int(self.log_text.index('end-1c').split('.')[0])
            if line_count > 1000:
                self.log_text.delete('1.0', '2.0')
        except Exception as e:
            logger.error(f"Log ekleme hatası: {e}")

    def update_coefficient(self, new_value: float):
        """Katsayı değerini günceller"""
        try:
            # constants.py dosyasındaki KATSAYI değerini güncelle
            import core.constants
            core.constants.KATSAYI = float(new_value)
            logger.info(f"Katsayı değeri güncellendi: {new_value}")
            return True
        except ValueError as e:
            logger.error(f"Katsayı güncellenirken hata oluştu: {e}")
            return False

    def _on_coefficient_change(self, new_value: str):
        """GUI'den katsayı değişikliği olduğunda çağrılır"""
        try:
            value = float(new_value)
            if value <= 0:
                logger.error("Katsayı değeri 0'dan büyük olmalıdır")
                return
            
            if self.update_coefficient(value):
                self.add_log(f"Katsayı başarıyla güncellendi: {value}", "INFO")
            else:
                self.add_log("Katsayı güncellenirken bir hata oluştu", "ERROR")
        except ValueError:
            self.add_log("Geçersiz katsayı değeri", "ERROR")

    def get_last_cut_data(self):
        """Son kesimin verilerini döndürür"""
        try:
            if hasattr(self, 'db'):
                # Son kesimin verilerini veritabanından al
                # testere_durumu = 3 kesim yapılıyor anlamına geliyor
                query = """
                    WITH kesim_baslangic_bitis AS (
                        SELECT 
                            timestamp,
                            testere_durumu,
                            LAG(testere_durumu) OVER (ORDER BY timestamp) as prev_durum,
                            LEAD(testere_durumu) OVER (ORDER BY timestamp) as next_durum
                        FROM testere_data
                        ORDER BY timestamp DESC
                    ),
                    kesim_gruplari AS (
                        SELECT 
                            timestamp,
                            CASE 
                                WHEN testere_durumu = 3 AND (prev_durum IS NULL OR prev_durum != 3) THEN 1 -- Kesim başlangıcı
                                WHEN testere_durumu = 3 AND (next_durum IS NULL OR next_durum != 3) THEN 2 -- Kesim bitişi
                                ELSE 0
                            END as kesim_noktasi
                        FROM kesim_baslangic_bitis
                    ),
                    son_kesim_baslangic AS (
                        SELECT timestamp
                        FROM kesim_gruplari
                        WHERE kesim_noktasi = 1
                        ORDER BY timestamp DESC
                        LIMIT 1
                    ),
                    son_kesim_bitis AS (
                        SELECT timestamp
                        FROM kesim_gruplari
                        WHERE kesim_noktasi = 2 AND timestamp > (SELECT timestamp FROM son_kesim_baslangic)
                        ORDER BY timestamp ASC
                        LIMIT 1
                    )
                    SELECT 
                        timestamp,
                        serit_motor_akim_a,
                        inme_motor_akim_a,
                        kafa_yuksekligi_mm,
                        serit_kesme_hizi,
                        serit_inme_hizi,
                        serit_sapmasi
                    FROM testere_data
                    WHERE timestamp >= (SELECT timestamp FROM son_kesim_baslangic)
                    AND (
                        timestamp <= (SELECT timestamp FROM son_kesim_bitis)
                        OR (SELECT COUNT(*) FROM son_kesim_bitis) = 0
                    )
                    AND testere_durumu = 3
                    AND serit_motor_akim_a IS NOT NULL
                    AND kafa_yuksekligi_mm IS NOT NULL
                    ORDER BY timestamp ASC
                """
                result = self.db.execute(query).fetchall()
                
                if result:
                    # Verileri sözlük formatına dönüştür
                    data = {
                        'timestamp': [row[0] for row in result],
                        'serit_motor_akim_a': [row[1] for row in result],
                        'inme_motor_akim_a': [row[2] for row in result],
                        'kafa_yuksekligi_mm': [row[3] for row in result],
                        'serit_kesme_hizi': [row[4] for row in result],
                        'serit_inme_hizi': [row[5] for row in result],
                        'serit_sapmasi': [row[6] for row in result]
                    }
                    return data
            return None
        except Exception as e:
            logger.error(f"Son kesim verilerini alırken hata: {e}")
            return None

    def show_cutting_summary(self):
        """Son kesimin akım değerlerini gösteren pencereyi açar"""
        try:
            # Son kesim verilerini al
            last_cut_data = self.get_last_cut_data()
            
            if last_cut_data:
                # Yeni pencere oluştur
                summary_window = tk.Toplevel(self.root)
                summary_window.title("Kesim Özeti")
                summary_window.geometry("1000x600")
                
                # Plotly figure oluştur
                fig = make_subplots(rows=1, cols=1)
                
                # Ana grafik - Kafa yüksekliği vs Akım
                fig.add_trace(
                    go.Scatter(
                        x=last_cut_data['kafa_yuksekligi_mm'],
                        y=last_cut_data['serit_motor_akim_a'],
                        mode='lines',
                        name='Şerit Motor Akım',
                        hovertemplate='Zaman: %{customdata[3]}<br>' +
                                    'Kafa Yüksekliği: %{x:.1f} mm<br>' +
                                    'Akım: %{y:.2f} A<br>' +
                                    'Kesme Hızı: %{customdata[0]:.1f} mm/s<br>' +
                                    'İnme Hızı: %{customdata[1]:.1f} mm/s<br>' +
                                    'Sapma: %{customdata[2]:.2f} mm<br>' +
                                    '<extra></extra>',
                        customdata=list(zip(
                            last_cut_data['serit_kesme_hizi'],
                            last_cut_data['serit_inme_hizi'],
                            last_cut_data['serit_sapmasi'],
                            last_cut_data['timestamp'],
                            last_cut_data['f']
                        ))
                    )
                )
                
                # Grafik düzeni
                fig.update_layout(
                    title='Kesim Özeti - Kafa Yüksekliği vs Akım',
                    xaxis_title='Kafa Yüksekliği (mm)',
                    yaxis_title='Motor Akımı (A)',
                    hovermode='closest',
                    showlegend=True,
                    width=1600,
                    height=900
                )
                
                # Geçici dosya adı oluştur
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = os.path.join(os.getcwd(), "temp")
                os.makedirs(temp_dir, exist_ok=True)
                html_file = os.path.join(temp_dir, f"kesim_ozeti_{timestamp}.html")
                
                # HTML dosyasını kaydet
                fig.write_html(
                    html_file,
                    include_plotlyjs='cdn',
                    full_html=True,
                    config={'displayModeBar': True}
                )
                
                # HTML dosyasını varsayılan tarayıcıda aç
                webbrowser.open(f'file://{html_file}')
                logger.info(f"Kesim özeti grafiği oluşturuldu: {html_file}")
                
                # Pencereyi kapat
                summary_window.destroy()
                
            else:
                messagebox.showinfo("Bilgi", "Son kesim verisi bulunamadı")
                
        except Exception as e:
            logger.error(f"Kesim özeti gösterilirken hata: {e}")
            logger.exception("Detaylı hata:")
            messagebox.showerror("Hata", "Kesim özeti gösterilirken bir hata oluştu")

    def _toggle_recording(self):
        """Kamera kaydını başlatır/durdurur"""
        if not self.camera.is_recording:
            if self.camera.start_recording():
                self.record_button.config(text="Kayıt Durdur")
                self.current_values['camera_status'].set("Kayıt Yapılıyor")
                # Frame sayacı callback'ini ayarla
                self.camera.set_frame_count_callback(
                    lambda count: self.current_values['camera_frame_count'].set(str(count))
                )
        else:
            if self.camera.stop_recording():
                self.record_button.config(text="Kayıt Başlat")
                self.current_values['camera_status'].set("Hazır")
                self.current_values['camera_frame_count'].set("0")

    def _toggle_viewing(self):
        """Kamera görüntüsünü başlatır/durdurur"""
        if not self.camera.is_viewing:
            if self.camera.start_viewing():
                self.view_button.config(text="Kamera Kapat")
        else:
            if self.camera.stop_viewing():
                self.view_button.config(text="Kamera İzle")

