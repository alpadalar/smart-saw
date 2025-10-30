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

import sqlite3
import pandas as pd

from core.logger import logger
from core.constants import TestereState, KATSAYI
from control import ControllerType, get_controller_factory
from models import ProcessedData
from utils.helpers import reverse_calculate_value
from core.camera import CameraModule
import tkinter.font as tkFont


# Linux için güvenli font yönetimi
class SafeFontManager:
    """Linux'ta tutarlı font rendering için font yöneticisi"""
    
    def __init__(self):
        self._fonts = {}
        self._initialized = False
    
    def _init_fonts(self):
        """Güvenli fontları başlatır (lazy initialization)"""
        if self._initialized:
            return
            
        try:
            # Önce root window var mı kontrol et
            try:
                root = tk._get_default_root()
                has_root = True
            except:
                has_root = False
            
            if not has_root:
                # Root window yoksa basit tuple fontlar kullan
                self._fonts = {
                    'small': ('Liberation Sans', 8, 'normal'),
                    'small_bold': ('Liberation Sans', 8, 'bold'),
                    'normal': ('Liberation Sans', 10, 'normal'),
                    'normal_bold': ('Liberation Sans', 10, 'bold'),
                    'medium': ('Liberation Sans', 12, 'normal'),
                    'medium_bold': ('Liberation Sans', 12, 'bold'),
                    'large': ('Liberation Sans', 16, 'normal'),
                    'large_bold': ('Liberation Sans', 16, 'bold'),
                    'xlarge': ('Liberation Sans', 18, 'normal'),
                    'xlarge_bold': ('Liberation Sans', 18, 'bold'),
                }
            else:
                # Root window varsa Font nesneleri oluştur ve ttk style'ları ayarla
                base_family = "Liberation Sans"
                self._fonts = {
                    'small': tkFont.Font(family=base_family, size=8, weight='normal'),
                    'small_bold': tkFont.Font(family=base_family, size=8, weight='bold'),
                    'normal': tkFont.Font(family=base_family, size=10, weight='normal'),
                    'normal_bold': tkFont.Font(family=base_family, size=10, weight='bold'),
                    'medium': tkFont.Font(family=base_family, size=12, weight='normal'),
                    'medium_bold': tkFont.Font(family=base_family, size=12, weight='bold'),
                    'large': tkFont.Font(family=base_family, size=16, weight='normal'),
                    'large_bold': tkFont.Font(family=base_family, size=16, weight='bold'),
                    'xlarge': tkFont.Font(family=base_family, size=18, weight='normal'),
                    'xlarge_bold': tkFont.Font(family=base_family, size=18, weight='bold'),
                }
                
                # ttk widget'ları için global style ayarları
                try:
                    style = ttk.Style()
                    
                    # Tüm ttk widget'lar için Liberation Sans fontunu ayarla
                    style.configure('.', font=(base_family, 10, 'normal'))
                    style.configure('TLabel', font=(base_family, 10, 'normal'))
                    style.configure('TButton', font=(base_family, 10, 'normal'))
                    style.configure('TEntry', font=(base_family, 10, 'normal'))
                    style.configure('TFrame', font=(base_family, 10, 'normal'))
                    style.configure('TLabelFrame', font=(base_family, 10, 'bold'))
                    style.configure('TLabelFrame.Label', font=(base_family, 10, 'bold'))
                    
                    # tk widget'lar için default font'u değiştir
                    root.option_add('*Font', (base_family, 10, 'normal'))
                    root.option_add('*Label.Font', (base_family, 10, 'normal'))
                    root.option_add('*Button.Font', (base_family, 10, 'normal'))
                    root.option_add('*Entry.Font', (base_family, 10, 'normal'))
                    
                except Exception as style_error:
                    print(f"Style ayarlama hatası: {style_error}")
                    
        except:
            # Her durumda fallback
            self._fonts = {
                'small': ('Liberation Sans', 8, 'normal'),
                'small_bold': ('Liberation Sans', 8, 'bold'),
                'normal': ('Liberation Sans', 10, 'normal'),
                'normal_bold': ('Liberation Sans', 10, 'bold'),
                'medium': ('Liberation Sans', 12, 'normal'),
                'medium_bold': ('Liberation Sans', 12, 'bold'),
                'large': ('Liberation Sans', 16, 'normal'),
                'large_bold': ('Liberation Sans', 16, 'bold'),
                'xlarge': ('Liberation Sans', 18, 'normal'),
                'xlarge_bold': ('Liberation Sans', 18, 'bold'),
            }
        
        self._initialized = True
    
    def get(self, font_key):
        """Font nesnesini döndürür"""
        self._init_fonts()  # Lazy initialization
        return self._fonts.get(font_key, self._fonts['normal'])


# Global font manager - GUI başladığında hazırlanacak
font_manager = None






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
        
        # Global font manager'ı başlat (lazy initialization ile güvenli)
        global font_manager
        font_manager = SafeFontManager()
        
        # Thread senkronizasyonu için event'ler
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
        
        # Ana pencere
        self.root = tk.Tk()
        self.root.title("Smart Saw Control Panel")
        
        # Tam ekran ayarları
        self.root.geometry("1920x1080")  # Fallback boyut
        try:
            # Linux için tam ekran (maximize)
            self.root.attributes('-zoomed', True)
        except tk.TclError:
            try:
                # Windows için tam ekran (maximize)
                self.root.state('zoomed')
            except tk.TclError:
                # Fallback: Manuel tam ekran boyutu
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
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
            'malzeme_genisligi': tk.StringVar(value="-"),
            'fark_hz_x': tk.StringVar(value="-"),
            'fark_hz_y': tk.StringVar(value="-"),
            'fark_hz_z': tk.StringVar(value="-"),
            
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
        
        # Placeholder güncelleme zamanlaması
        self.last_placeholder_update = 0
        
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
        top_frame.pack(fill=tk.X, pady=5)
        
        # Testere Durum Göstergesi
        testere_frame = ttk.LabelFrame(top_frame, text="Testere Durumu", padding=(5, 5))
        testere_frame.pack(fill=tk.X, pady=(0, 5))
        
        testere_status_frame = ttk.Frame(testere_frame)
        testere_status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(testere_status_frame, text="Durum:").pack(side=tk.LEFT, padx=5)
        self.testere_status_label = ttk.Label(
            testere_status_frame,
            textvariable=self.current_values['testere_durumu'],
            font=font_manager.get('normal_bold')
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
        # Enter tuşu ile uygulama
        self.coefficient_entry.bind('<Return>', lambda e: self._on_coefficient_change(self.coefficient_var.get()))
        
        # Uygula butonu
        ttk.Button(
            coefficient_frame,
            text="Uygula",
            command=lambda: self._on_coefficient_change(self.coefficient_var.get())
        ).pack(side=tk.LEFT, padx=5)

        # Manuel Hız Kontrolü ve Ana Metrikler için ortak container
        controls_container = ttk.Frame(left_panel)
        controls_container.pack(fill=tk.X, pady=5)
        
        # İki sütun için grid ayarları
        controls_container.grid_columnconfigure(0, weight=1)  # Sol sütun (manuel kontrol)
        controls_container.grid_columnconfigure(1, weight=1)  # Sağ sütun (ana metrikler)
        
        # Manuel Hız Kontrolü Frame'i (Sol sütun)
        manual_speed_frame = ttk.LabelFrame(controls_container, text="Manuel Hız Kontrolü", padding=(5, 5))
        manual_speed_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Manuel kontrol bilgisi (grid ile)
        ttk.Label(manual_speed_frame, 
                 text="Manuel Kontrol: Sınır kontrolü yok, istediğiniz değeri girin", 
                 font=font_manager.get('small'), foreground='red').grid(row=0, column=0, columnspan=4, sticky="ew", pady=2)
        
        # Grid Layout ile Hız Kontrolleri (2 satır x 4 sütun) - Artık satır 1'den başlıyor
        manual_speed_frame.grid_columnconfigure(0, weight=0)  # Hız girişi sütunu sabit boyut
        manual_speed_frame.grid_columnconfigure(1, weight=0)  # Gönder butonları
        manual_speed_frame.grid_columnconfigure(2, weight=0)  # Tüm hızları gönder
        manual_speed_frame.grid_columnconfigure(3, weight=1)  # ACİL DURDUR genişleyebilir
        
        # Satır 1: Kesme Hızı
        kesme_container = ttk.Frame(manual_speed_frame)
        kesme_container.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        ttk.Label(kesme_container, text="Kesme Hızı:").pack(side=tk.LEFT, padx=(0,5))
        self.kesme_hizi_var = tk.StringVar(value="")
        self.kesme_hizi_entry = ttk.Entry(kesme_container, textvariable=self.kesme_hizi_var, width=12)
        self.kesme_hizi_entry.pack(side=tk.LEFT, padx=(0,5))
        # Enter tuşu ile gönderme
        self.kesme_hizi_entry.bind('<Return>', lambda e: self._send_manual_speed('kesme'))
        # Focus eventi ile placeholder temizleme
        self.kesme_hizi_entry.bind('<FocusIn>', lambda e: self._on_focus_in(e, 'kesme'))
        self.kesme_hizi_entry.bind('<FocusOut>', lambda e: self._on_focus_out(e, 'kesme'))
        ttk.Label(kesme_container, text="mm/dakika").pack(side=tk.LEFT)
        
        # Kesme hızı gönder butonu
        ttk.Button(
            manual_speed_frame,
            text="Gönder",
            command=lambda: self._send_manual_speed('kesme')
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Satır 2: İnme Hızı
        inme_container = ttk.Frame(manual_speed_frame)
        inme_container.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        ttk.Label(inme_container, text="İnme Hızı:").pack(side=tk.LEFT, padx=(0,5))
        self.inme_hizi_var = tk.StringVar(value="")
        self.inme_hizi_entry = ttk.Entry(inme_container, textvariable=self.inme_hizi_var, width=12)
        self.inme_hizi_entry.pack(side=tk.LEFT, padx=(0,5))
        # Enter tuşu ile gönderme
        self.inme_hizi_entry.bind('<Return>', lambda e: self._send_manual_speed('inme'))
        # Focus eventi ile placeholder temizleme
        self.inme_hizi_entry.bind('<FocusIn>', lambda e: self._on_focus_in(e, 'inme'))
        self.inme_hizi_entry.bind('<FocusOut>', lambda e: self._on_focus_out(e, 'inme'))
        ttk.Label(inme_container, text="mm/dakika").pack(side=tk.LEFT)
        
        # İnme hızı gönder butonu
        ttk.Button(
            manual_speed_frame,
            text="Gönder",
            command=lambda: self._send_manual_speed('inme')
        ).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Tüm hızları gönder butonu (2 satır boyutunda)
        ttk.Button(
            manual_speed_frame,
            text="Tüm Hızları\nGönder",
            command=self._send_all_speeds
        ).grid(row=1, column=2, rowspan=2, sticky="w", padx=5, pady=2)
        
        # ACİL DURDUR butonu (2 satır boyutunda, kırmızı)
        self.emergency_stop_button = tk.Button(
            manual_speed_frame,
            text="ACİL\nDURDUR",
            command=self._emergency_stop,
            bg='red',
            fg='white',
            font=font_manager.get('medium_bold'),
            relief='raised',
            borderwidth=4,
            activebackground='darkred',
            activeforeground='white'
        )
        self.emergency_stop_button.grid(row=1, column=3, rowspan=2, sticky="nsew", padx=5, pady=2)
        
        # Dinamik placeholder textleri ayarla
        self._update_speed_placeholders()
        
        # Ana Metrikler (Büyük Gösterim) - Sağ sütun
        main_metrics_frame = ttk.LabelFrame(controls_container, text="Ana Metrikler", padding=(10, 10))
        main_metrics_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # 2x2 grid layout için ana metrikler
        main_metrics_frame.grid_columnconfigure(0, weight=1)
        main_metrics_frame.grid_columnconfigure(1, weight=1)
        main_metrics_frame.grid_rowconfigure(0, weight=1)
        main_metrics_frame.grid_rowconfigure(1, weight=1)
        
        # Akım ve Tork (Sol üst ve sağ üst)
        current_frame = ttk.Frame(main_metrics_frame)
        current_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(current_frame, text="Motor Akım:", font=font_manager.get('medium_bold')).pack(side=tk.LEFT)
        self.main_current_label = ttk.Label(current_frame, textvariable=self.current_values['serit_motor_akim_a'], 
                                           font=font_manager.get('xlarge_bold'), foreground='blue')
        self.main_current_label.pack(side=tk.LEFT, padx=(10,5))
        ttk.Label(current_frame, text="A", font=font_manager.get('medium_bold')).pack(side=tk.LEFT)
        
        torque_frame = ttk.Frame(main_metrics_frame)
        torque_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(torque_frame, text="Motor Tork:", font=font_manager.get('medium_bold')).pack(side=tk.LEFT)
        self.main_torque_label = ttk.Label(torque_frame, textvariable=self.current_values['serit_motor_tork_percentage'], 
                                          font=font_manager.get('xlarge_bold'), foreground='green')
        self.main_torque_label.pack(side=tk.LEFT, padx=(10,5))
        ttk.Label(torque_frame, text="%", font=font_manager.get('medium_bold')).pack(side=tk.LEFT)
        
        # Hızlar ve Sapma (Sol alt ve sağ alt)
        speeds_frame = ttk.Frame(main_metrics_frame)
        speeds_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(speeds_frame, text="Kesme:", font=font_manager.get('normal_bold')).pack(side=tk.LEFT)
        self.main_cut_speed_label = ttk.Label(speeds_frame, textvariable=self.current_values['serit_kesme_hizi'], 
                                             font=font_manager.get('large_bold'), foreground='red')
        self.main_cut_speed_label.pack(side=tk.LEFT, padx=(5,3))
        ttk.Label(speeds_frame, text="İnme:", font=font_manager.get('normal_bold')).pack(side=tk.LEFT, padx=(10,5))
        self.main_feed_speed_label = ttk.Label(speeds_frame, textvariable=self.current_values['serit_inme_hizi'], 
                                              font=font_manager.get('large_bold'), foreground='orange')
        self.main_feed_speed_label.pack(side=tk.LEFT, padx=(0,3))
        ttk.Label(speeds_frame, text="mm/s", font=font_manager.get('normal_bold')).pack(side=tk.LEFT)
        
        deviation_frame = ttk.Frame(main_metrics_frame)
        deviation_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(deviation_frame, text="Şerit Sapması:", font=font_manager.get('medium_bold')).pack(side=tk.LEFT)
        self.main_deviation_label = ttk.Label(deviation_frame, textvariable=self.current_values['serit_sapmasi'], 
                                             font=font_manager.get('xlarge_bold'), foreground='purple')
        self.main_deviation_label.pack(side=tk.LEFT, padx=(10,5))
        ttk.Label(deviation_frame, text="mm", font=font_manager.get('medium_bold')).pack(side=tk.LEFT)
        
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
            ('malzeme_genisligi', 'Malzeme Genişliği (mm)'),
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
        
        # Sağ grid (İvme Ölçer ve Fark Frekansları)
        right_grid = ttk.LabelFrame(values_frame, text="İvme Ölçer ve Fark Frekansları", padding=(5, 5))
        right_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        self._create_value_grid(right_grid, [
            ('ivme_olcer_x', 'X İvme (g)'),
            ('ivme_olcer_y', 'Y İvme (g)'),
            ('ivme_olcer_z', 'Z İvme (g)'),
            ('ivme_olcer_x_hz', 'X Frekans (Hz)'),
            ('ivme_olcer_y_hz', 'Y Frekans (Hz)'),
            ('ivme_olcer_z_hz', 'Z Frekans (Hz)'),
            ('fark_hz_x', 'Fark X (Hz)'),
            ('fark_hz_y', 'Fark Y (Hz)'),
            ('fark_hz_z', 'Fark Z (Hz)')
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
            # Placeholder'ları güncelle (5 saniyede bir)
            current_time = time.time()
            if current_time - self.last_placeholder_update > 5.0:
                self._update_speed_placeholders()
                self.last_placeholder_update = current_time
            
            # Modbus durumunu güncelle
            if 'modbus_connected' in processed_data:
                self.update_modbus_status(
                    processed_data['modbus_connected'],
                    processed_data.get('modbus_ip', '192.168.1.103')
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
        
        # Testere durumu 'kesim yapılıyor' ise kontroller
        if testere_durumu == TestereState.KESIM_YAPILIYOR.value:  # Kesim yapılıyor
            # Akım kontrolü
            current = float(data.get('serit_motor_akim_a', 0))
            if current > 13:
                self.add_log(f"Yüksek motor akımı: {current:.2f}A", "WARNING")
            elif current > 14:
                self.add_log(f"Kritik motor akımı: {current:.2f}A", "ERROR")
            
            # Tork kontrolü
            torque = float(data.get('serit_motor_tork_percentage', 0))
            if current > 70:
                self.add_log(f"Yüksek şerit motor torku: {torque:.2f}A", "WARNING")
            elif current > 100:
                self.add_log(f"Kritik şerit motor torku: {torque:.2f}A", "ERROR")

            # Sapma kontrolü 
            deviation = float(data.get('serit_sapmasi', 0))
            if abs(deviation) > 0.4:
                self.add_log(f"Yüksek şerit sapması: {deviation:.2f}mm", "WARNING")
            elif abs(deviation) > 0.6:
                self.add_log(f"Kritik şerit sapması: {deviation:.2f}mm", "ERROR")

            # şerit Gerginliği Bar kontrolü
            bar = float(data.get('serit_gerginligi_bar', 0))
            if 145 <= bar <= 155:
                pass  # Normal aralık
            elif (140 <= bar < 145) or (155 < bar <= 160):
                self.add_log(f"Şerit gerginliği uyarı seviyesinde: {bar:.2f} Bar", "WARNING")
            elif bar < 140 or bar > 160:
                self.add_log(f"Kritik şerit gerginliği: {bar:.2f} Bar", "ERROR")
            
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
                inme_hizi_str = self.inme_hizi_var.get().strip()
                # Placeholder kontrolü
                if hasattr(self.inme_hizi_entry, 'placeholder') and inme_hizi_str == self.inme_hizi_entry.placeholder:
                    self.add_log("İnme hızı değeri giriniz", "WARNING")
                    return
                if inme_hizi_str:
                    try:
                        inme_hizi = float(inme_hizi_str)
                        # Sınır kontrolü kaldırıldı - manuel kontrol
                        inme_hizi_is_negative = inme_hizi < 0
                        reverse_calculate_value(modbus_client, inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
                        self.add_log(f"İnme hızı gönderildi: {inme_hizi:.2f} mm/dakika", "INFO")
                        # Entry'yi temizle ve placeholder'ı geri koy
                        self.inme_hizi_var.set("")
                        self._set_placeholder(self.inme_hizi_entry, "mm/dakika")
                    except ValueError:
                        self.add_log("Geçersiz inme hızı değeri", "ERROR")
                else:
                    self.add_log("İnme hızı değeri boş", "WARNING")
                
            elif speed_type == 'kesme':
                # Kesme hızını gönder
                kesme_hizi_str = self.kesme_hizi_var.get().strip()
                # Placeholder kontrolü
                if hasattr(self.kesme_hizi_entry, 'placeholder') and kesme_hizi_str == self.kesme_hizi_entry.placeholder:
                    self.add_log("Kesme hızı değeri giriniz", "WARNING")
                    return
                if kesme_hizi_str:
                    try:
                        kesme_hizi = float(kesme_hizi_str)
                        # Sınır kontrolü kaldırıldı - manuel kontrol
                        kesme_hizi_is_negative = kesme_hizi < 0
                        reverse_calculate_value(modbus_client, kesme_hizi, 'serit_kesme_hizi', kesme_hizi_is_negative)
                        self.add_log(f"Kesme hızı gönderildi: {kesme_hizi:.2f} mm/dakika", "INFO")
                        # Entry'yi temizle ve placeholder'ı geri koy
                        self.kesme_hizi_var.set("")
                        self._set_placeholder(self.kesme_hizi_entry, "mm/dakika")
                    except ValueError:
                        self.add_log("Geçersiz kesme hızı değeri", "ERROR")
                else:
                    self.add_log("Kesme hızı değeri boş", "WARNING")
            
        except Exception as e:
            logger.error(f"Hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")

    def _send_all_speeds(self):
        """Tüm hızları gönderir (aralarında 110ms senkron gecikme ile)"""
        try:
            # Önce kesme hızını gönder
            self._send_manual_speed('kesme')
            
            # Modbus yazma işlemleri arasında senkron bekleme (110ms)
            # İkinci hızın doğru gitmesi için kritik!
            time.sleep(0.11)  
            
            # Sonra inme hızını gönder
            self._send_manual_speed('inme')
            
            self.add_log("İki hız başarıyla gönderildi (110ms gecikme ile)", "INFO")
            
        except Exception as e:
            logger.error(f"Toplu hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            self.add_log(f"Toplu hız gönderme hatası: {str(e)}", "ERROR")

    def _set_placeholder(self, entry_widget, placeholder_text):
        """Entry widget'ına placeholder text ekler"""
        entry_widget.placeholder = placeholder_text
        entry_widget.insert(0, placeholder_text)
        entry_widget.config(foreground='gray')

    def _on_focus_in(self, event, speed_type):
        """Entry'ye focus geldiğinde placeholder'ı temizler"""
        entry_widget = event.widget
        if hasattr(entry_widget, 'placeholder') and entry_widget.get() == entry_widget.placeholder:
            entry_widget.delete(0, tk.END)
            entry_widget.config(foreground='black')

    def _on_focus_out(self, event, speed_type):
        """Entry'den focus çıktığında boşsa placeholder'ı geri koyar"""
        entry_widget = event.widget
        if hasattr(entry_widget, 'placeholder') and entry_widget.get() == '':
            entry_widget.insert(0, entry_widget.placeholder)
            entry_widget.config(foreground='gray')

    def _update_speed_placeholders(self):
        """Register'lardan okunan değerleri placeholder olarak ayarlar"""
        try:
            if not self.controller_factory or not self.controller_factory.modbus_client:
                # Modbus bağlantısı yoksa varsayılan değerler
                self._set_placeholder(self.kesme_hizi_entry, "Reg:2066")
                self._set_placeholder(self.inme_hizi_entry, "Reg:2041")
                return
            
            modbus_client = self.controller_factory.modbus_client
            
            try:
                # Kesme hızı register'ını oku (2066) ve /10 yap
                kesme_registers = modbus_client.read_holding_registers(2066, 1)
                if kesme_registers and not kesme_registers.isError():
                    kesme_hizi = kesme_registers.registers[0] / 10.0
                    self._set_placeholder(self.kesme_hizi_entry, f"{kesme_hizi:.1f}")
                else:
                    self._set_placeholder(self.kesme_hizi_entry, "Reg:2066")
            except Exception as e:
                logger.debug(f"Kesme hızı placeholder okuma hatası: {e}")
                self._set_placeholder(self.kesme_hizi_entry, "Reg:2066")
            
            try:
                # İnme hızı register'ını oku (2041)
                inme_registers = modbus_client.read_holding_registers(2041, 1)
                if inme_registers and not inme_registers.isError():
                    inme_hizi = inme_registers.registers[0]
                    self._set_placeholder(self.inme_hizi_entry, f"{inme_hizi}")
                else:
                    self._set_placeholder(self.inme_hizi_entry, "Reg:2041")
            except Exception as e:
                logger.debug(f"İnme hızı placeholder okuma hatası: {e}")
                self._set_placeholder(self.inme_hizi_entry, "Reg:2041")
                
        except Exception as e:
            logger.error(f"Placeholder güncelleme hatası: {e}")
            # Hata durumunda varsayılan değerler
            self._set_placeholder(self.kesme_hizi_entry, "Reg:2066")
            self._set_placeholder(self.inme_hizi_entry, "Reg:2041")

    def _emergency_stop(self):
        """ACİL DURDUR - İki hıza da sıfır gönderir"""
        try:
            if not self.controller_factory or not self.controller_factory.modbus_client:
                self.add_log("Modbus bağlantısı bulunamadı - ACİL DURDUR başarısız!", "ERROR")
                return
            
            modbus_client = self.controller_factory.modbus_client
            
            # Kesme hızını sıfıra ayarla
            reverse_calculate_value(modbus_client, 0.0, 'serit_kesme_hizi', False)
            time.sleep(0.11)  # 110ms gecikme
            
            # İnme hızını sıfıra ayarla  
            reverse_calculate_value(modbus_client, 0.0, 'serit_inme_hizi', False)
            
            self.add_log("⚠️ ACİL DURDUR AKTİF - Tüm hızlar sıfırlandı!", "WARNING")
            logger.warning("ACİL DURDUR - Kesme ve İnme hızları sıfırlandı")
            
            # Entry'leri temizle
            self.kesme_hizi_var.set("")
            self.inme_hizi_var.set("")
            self._update_speed_placeholders()
            
        except Exception as e:
            logger.error(f"ACİL DURDUR hatası: {str(e)}")
            self.add_log(f"ACİL DURDUR HATASI: {str(e)}", "ERROR")

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
            if not hasattr(self, 'db') or self.db is None:
                logger.error("Veritabanı bağlantısı bulunamadı")
                return None

            # Son kesimin verilerini veritabanından al
            query = """
                WITH kesim_baslangic_bitis AS (
                    SELECT 
                        timestamp,
                        testere_durumu,
                        LAG(testere_durumu) OVER (ORDER BY timestamp) as prev_durum,
                        LEAD(testere_durumu) OVER (ORDER BY timestamp) as next_durum
                    FROM testere_data
                    WHERE testere_durumu = 3  -- Kesim yapılıyor durumu
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
            
            cursor = self.db.cursor()
            result = cursor.execute(query).fetchall()
            
            if not result:
                logger.warning("Son kesim verisi bulunamadı")
                return None

            # Verileri sözlük formatına dönüştür
            data = {
                'timestamp': [row[0] for row in result],
                'serit_motor_akim_a': [float(row[1]) for row in result],
                'inme_motor_akim_a': [float(row[2]) for row in result],
                'kafa_yuksekligi_mm': [float(row[3]) for row in result],
                'serit_kesme_hizi': [float(row[4]) for row in result],
                'serit_inme_hizi': [float(row[5]) for row in result],
                'serit_sapmasi': [float(row[6]) for row in result]
            }
            
            logger.info(f"Son kesim verisi başarıyla alındı: {len(result)} kayıt")
            return data

        except sqlite3.Error as e:
            logger.error(f"Veritabanı hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Son kesim verilerini alırken hata: {e}")
            logger.exception("Detaylı hata:")
            return None
    def get_cutting_data_by_date(self, date_str):
        try:
            if not hasattr(self, 'db') or self.db is None:
                logger.error("Veritabanı bağlantısı bulunamadı")
                return None

            query = """
                WITH kesim_durumlari AS (
                    SELECT 
                        timestamp,
                        testere_durumu,
                        LAG(testere_durumu) OVER (ORDER BY timestamp) as prev_durum,
                        LEAD(testere_durumu) OVER (ORDER BY timestamp) as next_durum
                    FROM testere_data
                    WHERE date(timestamp) = ?
                    AND (testere_durumu = 3 OR testere_durumu = 4)
                    ORDER BY timestamp
                ),
                kesim_baslangic_bitis AS (
                    SELECT 
                        timestamp,
                        testere_durumu,
                        CASE 
                            WHEN testere_durumu = 3 AND (prev_durum IS NULL OR prev_durum != 3) THEN 1
                            WHEN testere_durumu = 4 AND prev_durum = 3 THEN 2
                            ELSE 0
                        END as kesim_noktasi
                    FROM kesim_durumlari
                ),
                kesim_id_atanan AS (
                    SELECT 
                        t.timestamp,
                        t.serit_motor_akim_a,
                        t.inme_motor_akim_a,
                        t.kafa_yuksekligi_mm,
                        t.serit_kesme_hizi,
                        t.serit_inme_hizi,
                        t.serit_sapmasi,
                        t.ivme_olcer_x_hz,
                        t.ivme_olcer_y_hz,
                        t.ivme_olcer_z_hz,
                        t.fuzzy_output,
                        SUM(CASE WHEN k.kesim_noktasi = 1 THEN 1 ELSE 0 END) 
                            OVER (ORDER BY t.timestamp) as kesim_id
                    FROM testere_data t
                    LEFT JOIN kesim_baslangic_bitis k ON t.timestamp = k.timestamp
                    WHERE date(t.timestamp) = ?
                    AND t.testere_durumu IN (3, 4)
                )
                SELECT * FROM kesim_id_atanan
                WHERE kesim_id > 0
                ORDER BY timestamp ASC
            """

            cursor = self.db.cursor()
            result = cursor.execute(query, (date_str, date_str)).fetchall()

            if not result:
                return None

            data = {
                'timestamp': [row[0] for row in result],
                'serit_motor_akim_a': [float(row[1]) for row in result],
                'inme_motor_akim_a': [float(row[2]) for row in result],
                'kafa_yuksekligi_mm': [float(row[3]) for row in result],
                'serit_kesme_hizi': [float(row[4]) for row in result],
                'serit_inme_hizi': [float(row[5]) for row in result],
                'serit_sapmasi': [float(row[6]) for row in result],
                'ivme_olcer_x_hz': [float(row[7]) for row in result],
                'ivme_olcer_y_hz': [float(row[8]) for row in result],
                'ivme_olcer_z_hz': [float(row[9]) for row in result],
                'fuzzy_output': [float(row[10]) for row in result],
                'kesim_id': [int(row[11]) for row in result]
            }

            return data

        except Exception as e:
            logger.error(f"Tarih bazlı veri alma hatası: {e}")
            return None

    def show_all_summary_table(self):
        try:
            date_str = self.daily_date_entry.get()
            data = self.get_cutting_data_by_date(date_str)
            if data is None:
                self.daily_warning_label.config(text=f"{date_str} tarihli veri bulunamadı.")
                return

            self.daily_warning_label.config(text="")  # varsa eski uyarıyı temizle
            df = pd.DataFrame(data)
            numeric_columns = [
                'serit_motor_akim_a', 'serit_sapmasi', 'serit_kesme_hizi',
                'serit_inme_hizi', 'fuzzy_output'
            ]
            rows = []
            for kesim_id, group in df.groupby('kesim_id'):
                for col in numeric_columns:
                    desc = group[col].describe()
                    rows.append({
                        'kesim_id': kesim_id,
                        'nitelik': col,
                        'count': round(desc['count'], 2),
                        'mean': round(desc['mean'], 2),
                        'std': round(desc['std'], 2),
                        'min': round(desc['min'], 2),
                        '25%': round(desc['25%'], 2),
                        '50%': round(desc['50%'], 2),
                        '75%': round(desc['75%'], 2),
                        'max': round(desc['max'], 2)
                    })

            summary_df = pd.DataFrame(rows)
            self.show_table(summary_df, parent_frame=self.table_frame1, title="Tüm Kesim Özeti")

        except Exception as e:
            logger.error(f"Tüm tablo gösterim hatası: {e}")
            messagebox.showerror("Hata", str(e))

    def show_last_cut_summary_table(self):
        try:
            data = self.get_last_cut_data()
            if data is None:
                messagebox.showwarning("Uyarı", "Son kesim verisi bulunamadı")
                return

            df = pd.DataFrame(data)
            columns = [
                'serit_motor_akim_a', 'serit_kesme_hizi',
                'serit_inme_hizi', 'serit_sapmasi'
            ]
            rows = []
            for col in columns:
                desc = df[col].describe()
                rows.append({
                    'nitelik': col,
                    'count': round(desc['count'], 2),
                    'mean': round(desc['mean'], 2),
                    'std': round(desc['std'], 2),
                    'min': round(desc['min'], 2),
                    '25%': round(desc['25%'], 2),
                    '50%': round(desc['50%'], 2),
                    '75%': round(desc['75%'], 2),
                    'max': round(desc['max'], 2)
                })

            summary_df = pd.DataFrame(rows)
            self.show_table(summary_df, parent_frame=self.plot_frame2, title="Son Kesim Özeti")

        except Exception as e:
            logger.error(f"Son kesim tablo hatası: {e}")
            messagebox.showerror("Hata", str(e))

    def plot_kesim_grafigi(self, df, x_column, y_column, hover_columns, smooth_window, smooth_method, title=""):
        import plotly.graph_objects as go

        fig = go.Figure()
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        color_index = 0

        for kesim_id in df['kesim_id'].unique():
            kesim_data = df[df['kesim_id'] == kesim_id].copy()

            # Smoothing işlemi
            if smooth_window and smooth_window > 1:
                if smooth_method == "avg":
                    kesim_data[y_column] = kesim_data[y_column].rolling(window=smooth_window, min_periods=1).mean()
                elif smooth_method == "median":
                    kesim_data[y_column] = kesim_data[y_column].rolling(window=smooth_window, min_periods=1).median()

            custom_data = kesim_data[hover_columns].values

            fig.add_trace(
                go.Scatter(
                    x=kesim_data[x_column],
                    y=kesim_data[y_column],
                    mode='lines',
                    name=f"Kesim ID: {kesim_id} ({smooth_method} {smooth_window})" if smooth_window > 1 else f"Kesim ID: {kesim_id}",
                    line=dict(color=colors[color_index % len(colors)]),
                    customdata=custom_data,
                    hovertemplate=(
                        f"<b>{x_column.replace('_', ' ').title()}:</b> %{{x}}<br>"
                        f"<b>{y_column.replace('_', ' ').title()}:</b> %{{y:.2f}}<br>"
                        + "<br>".join([
                            f"<b>{col.replace('_', ' ').title()}:</b> %{{customdata[{i}]}}"
                            for i, col in enumerate(hover_columns)
                        ]) + "<extra></extra>"
                    ),
                    visible=True
                )
            )
            color_index += 1

        fig.update_layout(
            title=title or f"{y_column.replace('_', ' ').title()} vs {x_column.replace('_', ' ').title()}",
            xaxis_title=x_column.replace('_', ' ').title(),
            yaxis_title=y_column.replace('_', ' ').title(),
            xaxis=dict(
                autorange='reversed' if x_column == "kafa_yuksekligi_mm" else True,
                showgrid=True,
                gridcolor='lightgray',
                zeroline=False,
                showline=True,
                mirror=True,
                linewidth=1
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                zeroline=False,
                showline=True,
                mirror=True,
                linewidth=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='black'),
            hovermode='x',
            autosize=True,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=800
        )
        return fig

    def plot_all_cuts_timeseries(self, df, x_column, y_column, hover_columns, smooth_window, smooth_method, title=""):
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig = go.Figure()
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        if smooth_window and smooth_window > 1:
            if smooth_method == "avg":
                df[y_column] = df[y_column].rolling(window=smooth_window, min_periods=1).mean()
            elif smooth_method == "median":
                df[y_column] = df[y_column].rolling(window=smooth_window, min_periods=1).median()

        custom_data = df[hover_columns].values

        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df[y_column],
                mode='lines',
                name=f"Tüm Kesimler",
                line=dict(width=1.5),
                customdata=custom_data,
                hovertemplate=(
                    f"<b>{x_column.replace('_', ' ').title()}:</b> %{{x}}<br>"
                    f"<b>{y_column.replace('_', ' ').title()}:</b> %{{y:.2f}}<br>"
                    + "<br>".join([
                        f"<b>{col.replace('_', ' ').title()}:</b> %{{customdata[{i}]}}"
                        for i, col in enumerate(hover_columns)
                    ]) + "<extra></extra>"
                )
            )
        )
        fig.update_layout(
            title=title or f"Tüm Kesimler Zaman Serisi ({y_column})",
            xaxis_title=x_column,
            yaxis_title=y_column,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='black'),
            hovermode='x',
            height=800,
            showlegend=False,
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray'
            )
        )
        return fig
    
    def _show_all_cuts_timeseries_plot(self, data, x_column, y_column, hover_columns, smooth_window, smooth_method):
        try:
            if data is None:
                self.daily_warning_label.config(text="Veri bulunamadı.")
                return
            self.daily_warning_label.config(text="")  # Önceki uyarıyı temizle

            df = pd.DataFrame(data)
            fig = self.plot_all_cuts_timeseries(df, x_column, y_column, hover_columns, smooth_window, smooth_method)
            self.show_plot(fig, title="Tüm Kesimler Zaman Serisi")

        except Exception as e:
            logger.error(f"Tüm kesim zaman serisi hatası: {e}")
            messagebox.showerror("Hata", str(e))

    def get_data_by_kesim_ids(self, df, kesim_ids):
        """DataFrame'den kesim_id listesine göre filtrelenmiş veri döndürür"""
        try:
            if kesim_ids:
                return df[df['kesim_id'].isin(kesim_ids)].copy()
            else:
                return df.copy()
        except Exception as e:
            logger.error(f"Veri filtreleme hatası: {e}")
            return df

    #Son gün verilerini al
    def get_last_date_cutting_data(self):
        return self.get_cutting_data()

    def get_today_cutting_data(self):
        """Bugünün tarihine ait kesim verilerini getirir"""
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")  # bugünün tarihi
            return self.get_cutting_data_by_date(today_str)
        except Exception as e:
            logger.error(f"Bugünkü kesim verisi alınamadı: {e}")
            return None

    def get_cutting_data_by_date(self, date_str):
        try:
            if not hasattr(self, 'db') or self.db is None:
                return None

            query = """
                SELECT * FROM testere_data
                WHERE date(timestamp) = ?
                ORDER BY timestamp ASC
            """
            cursor = self.db.cursor()
            result = cursor.execute(query, (date_str,)).fetchall()
            if not result:
                return None

            # Kolonları uygun şekilde ayrıştır
            columns = [desc[0] for desc in cursor.description]
            data = {col: [] for col in columns}
            for row in result:
                for col, val in zip(columns, row):
                    data[col].append(val)
            return data

        except Exception as e:
            logger.error(f"{date_str} tarihli veri alınamadı: {e}")
            return None

    def show_cutting_summary(self):
        """Kesim özeti penceresini açar"""
        try:
            # Veritabanı bağlantısını kontrol et
            if not hasattr(self, 'db') or self.db is None:
                logger.error("Veritabanı bağlantısı bulunamadı")
                messagebox.showerror("Hata", "Veritabanı bağlantısı bulunamadı")
                return

            # Yeni pencere oluştur
            summary_window = tk.Toplevel(self.root)
            summary_window.title("Kesim Özeti")
            summary_window.geometry("1920x1080")

            # Ana frame
            main_frame = ttk.Frame(summary_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Sol panel - Parametre ayarları
            left_panel = ttk.LabelFrame(main_frame, text="Parametre Ayarları", padding="5")
            left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

            # Parametre giriş alanları
            param_frame = ttk.Frame(left_panel)
            param_frame.pack(fill=tk.X, pady=5)

            # X ekseni seçimi
            ttk.Label(param_frame, text="X Ekseni:").pack(anchor=tk.W)
            x_column_var = tk.StringVar(value="kafa_yuksekligi_mm")
            x_column_combo = ttk.Combobox(param_frame, textvariable=x_column_var, 
                                        values=["timestamp", "kafa_yuksekligi_mm", "serit_motor_akim_a", 
                                               "serit_sapmasi", "serit_kesme_hizi", "serit_inme_hizi", 
                                               "fuzzy_output"])
            x_column_combo.pack(fill=tk.X, pady=(0, 5))

            # Y ekseni seçimi
            ttk.Label(param_frame, text="Y Ekseni:").pack(anchor=tk.W)
            y_column_var = tk.StringVar(value="serit_motor_akim_a")
            y_column_combo = ttk.Combobox(param_frame, textvariable=y_column_var,
                                        values=["serit_motor_akim_a", "serit_sapmasi", 
                                               "serit_kesme_hizi", "serit_inme_hizi", "fuzzy_output",
                                               "ivme_olcer_x_hz", "ivme_olcer_y_hz", "ivme_olcer_z_hz"])
            y_column_combo.pack(fill=tk.X, pady=(0, 5))

            # Hover kolonları seçimi
            ttk.Label(param_frame, text="Hover Kolonları:").pack(anchor=tk.W)
            hover_columns_var = tk.StringVar(value="serit_kesme_hizi,serit_inme_hizi,fuzzy_output,serit_sapmasi")
            hover_columns_entry = ttk.Entry(param_frame, textvariable=hover_columns_var)
            hover_columns_entry.pack(fill=tk.X, pady=(0, 5))

            # Kesim ID'leri seçimi
            ttk.Label(param_frame, text="Kesim ID'leri:").pack(anchor=tk.W)
            kesim_ids_var = tk.StringVar()
            kesim_ids_entry = ttk.Entry(param_frame, textvariable=kesim_ids_var)
            kesim_ids_entry.pack(fill=tk.X, pady=(0, 5))

            # Smoothing ayarları
            ttk.Label(param_frame, text="Smoothing Penceresi:").pack(anchor=tk.W)
            smooth_window_var = tk.StringVar(value="0")
            smooth_window_entry = ttk.Entry(param_frame, textvariable=smooth_window_var)
            smooth_window_entry.pack(fill=tk.X, pady=(0, 5))

            ttk.Label(param_frame, text="Smoothing Metodu:").pack(anchor=tk.W)
            smooth_method_var = tk.StringVar(value="avg")
            smooth_method_combo = ttk.Combobox(param_frame, textvariable=smooth_method_var,
                                             values=["avg", "median"])
            smooth_method_combo.pack(fill=tk.X, pady=(0, 5))

            # Grafik oluşturma butonu
            def create_plots():
                try:
                    # Parametreleri al
                    x_column = x_column_var.get()
                    y_column = y_column_var.get()
                    hover_columns = [col.strip() for col in hover_columns_var.get().split(",")]
                    kesim_ids = [int(id.strip()) for id in kesim_ids_var.get().split(",") if id.strip()]
                    smooth_window = int(smooth_window_var.get())
                    smooth_method = smooth_method_var.get()

                    # Veriyi al (o güne ait tüm kesimler)
                    # all_data = self.get_cutting_data()
                    all_data = self.get_today_cutting_data()

                    if all_data is None:
                        logger.warning("Bugünün verisi bulunamadı")
                        self.add_log("Bugünün verisi bulunamadı", "WARNING")
                        return

                    # DataFrame'e çevir
                    df = pd.DataFrame(all_data)

                    # Kesim ID'lerine göre filtrele
                    df_filtered = self.get_data_by_kesim_ids(df, kesim_ids)

                    # Grafiği çiz
                    fig = self.plot_kesim_grafigi(
                        df_filtered,
                        x_column=x_column,
                        y_column=y_column,
                        hover_columns=hover_columns,
                        smooth_window=smooth_window,
                        smooth_method=smooth_method,
                        title="Kesim Grafiği")
                    self.show_plot(fig, title="Kesim Grafiği")

                except Exception as e:
                    logger.error(f"Grafikleri oluşturma hatası: {e}")
                    messagebox.showerror("Hata", f"Grafik oluşturulurken hata oluştu: {str(e)}")

            def on_all_cuts_plot_button_click(daily_date_var, x_column_var, y_column_var,
                                   hover_columns_var, smooth_window_var, smooth_method_var):
                try:
                    date_str = daily_date_var.get().strip()
                    data = self.get_cutting_data_by_date(date_str) if date_str else self.get_cutting_data_by_date(datetime.now().strftime("%Y-%m-%d"))

                    if data is None:
                        logger.warning("Tüm kesim grafiği oluşturulamadı: Veri bulunamadı.")
                        self.add_log("Tüm kesim grafiği oluşturulamadı: Veri bulunamadı.", "WARNING")
                        return

                    self._show_all_cuts_timeseries_plot(
                        data,
                        x_column_var.get(), y_column_var.get(),
                        [col.strip() for col in hover_columns_var.get().split(",")],
                        int(smooth_window_var.get()), smooth_method_var.get()
                    )
                except Exception as e:
                    logger.error(f"Tüm kesim grafiği oluşturma hatası: {e}")
                    self.add_log(f"Tüm kesim grafiği oluşturma hatası: {e}", "ERROR")

            ttk.Button(param_frame, text="Kesim Grafiğini Oluştur", 
                      command=create_plots).pack(fill=tk.X, pady=10)
            ttk.Button(
                    param_frame,
                    text="Tüm Kesim Grafiği Oluştur",
                    command=lambda: on_all_cuts_plot_button_click(
                        tk.StringVar(value=datetime.now().strftime("%Y-%m-%d")),  # Gün Analizi alanından bağımsız tarih ver
                        x_column_var, y_column_var,
                        hover_columns_var, smooth_window_var, smooth_method_var
                    )
                ).pack(fill=tk.X, pady=5)


            # Sağ panel - Grafikler ve tablolar için
            right_panel = ttk.Frame(main_frame)
            right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Grafik ve tablo alanları
            self.plot_frame1 = ttk.LabelFrame(right_panel, text="Tüm Kesimler")
            self.plot_frame1.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

            self.table_frame1 = ttk.LabelFrame(right_panel, text="Genel İstatistikler")
            self.table_frame1.pack(fill=tk.X, pady=(0, 5))

            self.plot_frame2 = ttk.LabelFrame(right_panel, text="Son Kesim")
            self.plot_frame2.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

            self.table_frame2 = ttk.LabelFrame(right_panel, text="Kesim Detayları")
            self.table_frame2.pack(fill=tk.X, pady=(0, 5))

            # Gün Analizi Alanı
            daily_analysis_frame = ttk.LabelFrame(left_panel, text="Gün Analizi", padding="5")
            daily_analysis_frame.pack(fill=tk.X, pady=10)

            # Grafik parametreleri
            param_frame = ttk.Frame(daily_analysis_frame)
            param_frame.pack(fill=tk.X, pady=5)

            # Tarih seçimi alanı
            ttk.Label(param_frame, text="Tarih (YYYY-MM-DD):").pack(anchor=tk.W)
            daily_date_var = tk.StringVar()
            daily_date_entry = ttk.Entry(param_frame, textvariable=daily_date_var)
            daily_date_entry.pack(fill=tk.X, pady=(0, 5))
            
            # X ekseni seçimi
            ttk.Label(param_frame, text="X Ekseni:").pack(anchor=tk.W)
            daily_x_column_var = tk.StringVar(value="kafa_yuksekligi_mm")
            daily_x_column_combo = ttk.Combobox(param_frame, textvariable=daily_x_column_var, 
                                              values=["timestamp", "kafa_yuksekligi_mm", "serit_motor_akim_a", 
                                                     "serit_sapmasi", "serit_kesme_hizi", "serit_inme_hizi", 
                                                     "fuzzy_output"])
            daily_x_column_combo.pack(fill=tk.X, pady=(0, 5))

            # Y ekseni seçimi
            ttk.Label(param_frame, text="Y Ekseni:").pack(anchor=tk.W)
            daily_y_column_var = tk.StringVar(value="serit_motor_akim_a")
            daily_y_column_combo = ttk.Combobox(param_frame, textvariable=daily_y_column_var,
                                              values=["serit_motor_akim_a", "serit_sapmasi", 
                                                     "serit_kesme_hizi", "serit_inme_hizi", "fuzzy_output",
                                                     "ivme_olcer_x_hz", "ivme_olcer_y_hz", "ivme_olcer_z_hz"])
            daily_y_column_combo.pack(fill=tk.X, pady=(0, 5))

            # Hover kolonları seçimi
            ttk.Label(param_frame, text="Hover Kolonları:").pack(anchor=tk.W)
            daily_hover_columns_var = tk.StringVar(value="serit_kesme_hizi,serit_inme_hizi,fuzzy_output,serit_sapmasi")
            daily_hover_columns_entry = ttk.Entry(param_frame, textvariable=daily_hover_columns_var)
            daily_hover_columns_entry.pack(fill=tk.X, pady=(0, 5))

            # Smoothing ayarları
            ttk.Label(param_frame, text="Smoothing Penceresi:").pack(anchor=tk.W)
            daily_smooth_window_var = tk.StringVar(value="0")
            daily_smooth_window_entry = ttk.Entry(param_frame, textvariable=daily_smooth_window_var)
            daily_smooth_window_entry.pack(fill=tk.X, pady=(0, 5))

            ttk.Label(param_frame, text="Smoothing Metodu:").pack(anchor=tk.W)
            daily_smooth_method_var = tk.StringVar(value="avg")
            daily_smooth_method_combo = ttk.Combobox(param_frame, textvariable=daily_smooth_method_var,
                                                   values=["avg", "median"])
            daily_smooth_method_combo.pack(fill=tk.X, pady=(0, 5))

            def show_daily_analysis():
                try:
                    date_str = daily_date_var.get().strip()
                    self.daily_warning_label.config(text="")  # Önceki uyarıyı temizle

                    if date_str:
                        data = self.get_cutting_data_by_date(date_str)
                        if data is None:
                            self.daily_warning_label.config(text=f"{date_str} tarihli veri bulunamadı.")
                            return
                    else:
                        data = self.get_last_date_cutting_data()
                        if data is None:
                            self.daily_warning_label.config(text="Son gün verisi bulunamadı.")
                            return

                    df = pd.DataFrame(data)
                    x_column = daily_x_column_var.get()
                    y_column = daily_y_column_var.get()
                    hover_columns = [col.strip() for col in daily_hover_columns_var.get().split(",")]
                    smooth_window = int(daily_smooth_window_var.get())
                    smooth_method = daily_smooth_method_var.get()

                    fig = self.plot_kesim_grafigi(df, x_column, y_column, hover_columns, smooth_window, smooth_method, title="Günlük Analiz Grafiği")
                    self.show_plot(fig, "Günlük Analiz Grafiği")

                except Exception as e:
                    logger.error(f"Günlük analiz grafiği hatası: {e}")
                    self.daily_warning_label.config(text=f"Hata: {str(e)}")

            ttk.Button(param_frame, text="Günlük Kesim Grafiğini Göster", 
                      command=show_daily_analysis).pack(fill=tk.X, pady=10)
            ttk.Button(param_frame, text="Günlük Tüm Kesim Grafiği", command=lambda: self._show_all_cuts_timeseries_plot(
                    self.get_cutting_data_by_date(daily_date_var.get().strip()) if daily_date_var.get().strip() else self.get_last_date_cutting_data(),
                    daily_x_column_var.get(), daily_y_column_var.get(),
                    [col.strip() for col in daily_hover_columns_var.get().split(",")],
                    int(daily_smooth_window_var.get()), daily_smooth_method_var.get()
                )).pack(fill=tk.X, pady=5)

            ttk.Button(param_frame, text="Tüm Tabloyu Göster", command=self.show_all_summary_table).pack(pady=(0, 5))
            ttk.Button(param_frame, text="Son Kesim Tablo Göster", command=self.show_last_cut_summary_table).pack(pady=(0, 5))
            
            self.daily_warning_label = ttk.Label(daily_analysis_frame, text="", foreground="red")
            self.daily_warning_label.pack()


        except Exception as e:
            logger.error(f"Kesim özeti penceresi oluşturulurken hata: {e}")
            logger.exception("Detaylı hata:")
            messagebox.showerror("Hata", f"Kesim özeti penceresi oluşturulurken hata oluştu: {str(e)}")
    
    def create_timeseries_plot(self, data, x_axis, y_axis, hover_cols, kesim_ids=None):
        """Zaman serisi grafiği oluşturur"""
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Verileri DataFrame'e dönüştür
            df = pd.DataFrame(data)
            
            # Kesim ID'lerine göre filtrele
            if kesim_ids:
                df = df[df['kesim_id'].isin(kesim_ids)]
            
            # Alt grafikleri oluştur
            fig = make_subplots(rows=len(y_axis), cols=1,
                              shared_xaxes=True,
                              vertical_spacing=0.05)
            
            # Her bir y ekseni için grafik ekle
            for i, y_col in enumerate(y_axis, 1):
                for kesim_id in df['kesim_id'].unique():
                    kesim_data = df[df['kesim_id'] == kesim_id]
                    
                    # Hover bilgilerini hazırla
                    hover_text = []
                    for _, row in kesim_data.iterrows():
                        text = f"Kesim ID: {row['kesim_id']}<br>"
                        for col in hover_cols:
                            text += f"{col}: {row[col]:.2f}<br>"
                        hover_text.append(text)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=kesim_data[x_axis],
                            y=kesim_data[y_col],
                            name=f"Kesim {kesim_id}",
                            hovertext=hover_text,
                            hoverinfo='text',
                            mode='lines',
                            line=dict(width=1)
                        ),
                        row=i, col=1
                    )
                
                # Y ekseni başlığını ayarla
                fig.update_yaxes(title_text=y_col, row=i, col=1)
            
            # X ekseni başlığını ayarla
            fig.update_xaxes(title_text=x_axis, row=len(y_axis), col=1)
            
            # Grafik düzenini ayarla
            fig.update_layout(
                height=300 * len(y_axis),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Grafik oluşturulurken hata: {e}")
            logger.exception("Detaylı hata:")
            return None

    def create_kesim_timeseries_plot(self, dataset, kesim_ids, x_column, y_column, hover_columns):
        """Belirli kesimler için zaman serisi grafiği oluşturur"""
        try:
            import plotly.graph_objects as go
            
            # Verileri DataFrame'e dönüştür
            df = pd.DataFrame(dataset)
            
            # Kesim ID'lerine göre filtrele
            df = df[df['kesim_id'].isin(kesim_ids)]
            
            # Grafik oluştur
            fig = go.Figure()
            
            # Her kesim için ayrı çizgi ekle
            for kesim_id in kesim_ids:
                kesim_data = df[df['kesim_id'] == kesim_id]
                
                # Hover bilgilerini hazırla
                hover_text = []
                for _, row in kesim_data.iterrows():
                    text = f"Kesim ID: {row['kesim_id']}<br>"
                    for col in hover_columns:
                        text += f"{col}: {row[col]:.2f}<br>"
                    hover_text.append(text)
                
                fig.add_trace(
                    go.Scatter(
                        x=kesim_data[x_column],
                        y=kesim_data[y_column],
                        name=f"Kesim {kesim_id}",
                        hovertext=hover_text,
                        hoverinfo='text',
                        mode='lines',
                        line=dict(width=1)
                    )
                )
            
            # Grafik düzenini ayarla
            fig.update_layout(
                title=f"{y_column} Zamanla Değişimi",
                xaxis_title=x_column,
                yaxis_title=y_column,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Kesim grafiği oluşturulurken hata: {e}")
            logger.exception("Detaylı hata:")
            return None

    def show_plot(self, fig, title=""):
        try:
            if fig is None:
                logger.error("Gösterilecek grafik bulunamadı")
                return
            fig.show()  # sadece tarayıcıda aç
        except Exception as e:
            logger.error(f"Grafik gösterilirken hata: {e}")
            logger.exception("Detaylı hata:")

    def create_summary_tables(self, df, kesim_ids):
        """Özet tabloları oluşturur"""
        try:
            if df is None or df.empty:
                logger.error("Veri seti boş veya None")
                return None
                
            # Kesim ID'lerine göre filtrele
            filtered_df = df[df['kesim_id'].isin(kesim_ids)]
            
            if filtered_df.empty:
                logger.error("Filtrelenmiş veri seti boş")
                return None
            
            # Genel istatistikler
            general_stats = filtered_df.describe()
            
            # Kesim bazlı istatistikler
            kesim_stats = filtered_df.groupby('kesim_id').agg({
                'kesim_suresi': ['mean', 'std', 'min', 'max'],
                'kesim_hizi': ['mean', 'std', 'min', 'max'],
                'kesim_derinligi': ['mean', 'std', 'min', 'max']
            })
            
            return {
                'general_stats': general_stats,
                'kesim_stats': kesim_stats
            }
            
        except Exception as e:
            logger.error(f"Özet tabloları oluşturulurken hata: {e}")
            logger.exception("Detaylı hata:")
            return None

    def show_summary_tables(self, df, kesim_ids, parent_frame):
        """Özet tabloları gösterir"""
        try:
            # Özet tabloları oluştur
            summary_tables = self.create_summary_tables(df, kesim_ids)
            if summary_tables is None:
                return
                
            # Mevcut içeriği temizle
            for widget in parent_frame.winfo_children():
                widget.destroy()
                
            # Genel istatistikler tablosu
            general_frame = ttk.LabelFrame(parent_frame, text="Genel İstatistikler")
            general_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.show_table(summary_tables['general'], general_frame, "Genel İstatistikler")
            
            # Kesim bazlı istatistikler tablosu
            kesim_frame = ttk.LabelFrame(parent_frame, text="Kesim Bazlı İstatistikler")
            kesim_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.show_table(summary_tables['kesim'], kesim_frame, "Kesim Bazlı İstatistikler")
            
        except Exception as e:
            logger.error(f"Özet tabloları gösterimi hatası: {e}")
            logger.exception("Detaylı hata:")

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

    def get_cutting_data(self):
        """Veritabanındaki en son tarihe ait kesim verilerini alır"""
        try:
            if not hasattr(self, 'db') or self.db is None:
                logger.error("Veritabanı bağlantısı bulunamadı")
                return None

            # En son tarihi al
            query_last_date = """
                SELECT date(timestamp) as last_date
                FROM testere_data
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            cursor = self.db.cursor()
            last_date = cursor.execute(query_last_date).fetchone()[0]
            
            if not last_date:
                logger.warning("Veritabanında veri bulunamadı")
                return None

            # Son tarihteki kesimleri al
            query = """
                WITH kesim_durumlari AS (
                    SELECT 
                        timestamp,
                        testere_durumu,
                        LAG(testere_durumu) OVER (ORDER BY timestamp) as prev_durum,
                        LEAD(testere_durumu) OVER (ORDER BY timestamp) as next_durum
                    FROM testere_data
                    WHERE date(timestamp) = ?
                    AND (testere_durumu = 3 OR testere_durumu = 4)  -- Kesim yapılıyor veya kesim bitti
                    ORDER BY timestamp
                ),
                kesim_baslangic_bitis AS (
                    SELECT 
                        timestamp,
                        testere_durumu,
                        CASE 
                            WHEN testere_durumu = 3 AND (prev_durum IS NULL OR prev_durum != 3) THEN 1  -- Kesim başlangıcı
                            WHEN testere_durumu = 4 AND prev_durum = 3 THEN 2  -- Kesim bitişi
                            ELSE 0
                        END as kesim_noktasi
                    FROM kesim_durumlari
                ),
                kesim_id_atanan AS (
                    SELECT 
                        t.timestamp,
                        t.serit_motor_akim_a,
                        t.inme_motor_akim_a,
                        t.kafa_yuksekligi_mm,
                        t.serit_kesme_hizi,
                        t.serit_inme_hizi,
                        t.serit_sapmasi,
                        t.ivme_olcer_x_hz,
                        t.ivme_olcer_y_hz,
                        t.ivme_olcer_z_hz,
                        t.fuzzy_output,
                        SUM(CASE WHEN k.kesim_noktasi = 1 THEN 1 ELSE 0 END) 
                            OVER (ORDER BY t.timestamp) as kesim_id
                    FROM testere_data t
                    LEFT JOIN kesim_baslangic_bitis k ON t.timestamp = k.timestamp
                    WHERE date(t.timestamp) = ?
                    AND t.testere_durumu IN (3, 4)  -- Sadece kesim yapılıyor ve kesim bitti durumlarını al
                )
                SELECT * FROM kesim_id_atanan
                WHERE kesim_id > 0
                ORDER BY timestamp ASC
            """
            
            result = cursor.execute(query, (last_date, last_date)).fetchall()
            
            if not result:
                logger.warning(f"{last_date} tarihi için kesim verisi bulunamadı")
                return None

            # Verileri sözlük formatına dönüştür
            data = {
                'timestamp': [row[0] for row in result],
                'serit_motor_akim_a': [float(row[1]) for row in result],
                'inme_motor_akim_a': [float(row[2]) for row in result],
                'kafa_yuksekligi_mm': [float(row[3]) for row in result],
                'serit_kesme_hizi': [float(row[4]) for row in result],
                'serit_inme_hizi': [float(row[5]) for row in result],
                'serit_sapmasi': [float(row[6]) for row in result],
                'ivme_olcer_x_hz': [float(row[7]) for row in result],
                'ivme_olcer_y_hz': [float(row[8]) for row in result],
                'ivme_olcer_z_hz': [float(row[9]) for row in result],
                'fuzzy_output': [float(row[10]) for row in result],
                'kesim_id': [int(row[11]) for row in result]
            }
            
            logger.info(f"{last_date} tarihli kesim verileri başarıyla alındı: {len(result)} kayıt")
            return data

        except sqlite3.Error as e:
            logger.error(f"Veritabanı hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Kesim verilerini alırken hata: {e}")
            logger.exception("Detaylı hata:")
            return None

    def show_table(self, df, parent_frame, title):
        """DataFrame'i tablo olarak gösterir"""
        try:
            if df is None or df.empty:
                logger.error("Gösterilecek veri seti boş veya None")
                return
                
            # Mevcut içeriği temizle
            for widget in parent_frame.winfo_children():
                widget.destroy()
                
            # Başlık etiketi
            title_label = ttk.Label(parent_frame, text=title, font=font_manager.get('medium_bold'))
            title_label.pack(pady=5)
            
            # Tablo oluştur
            table = ttk.Treeview(parent_frame)
            table["columns"] = list(df.columns)
            table["show"] = "headings"
            
            # Sütun başlıkları ve genişlikleri
            for column in df.columns:
                table.heading(column, text=column)
                # Sütun genişliğini içeriğe göre ayarla
                max_width = max(
                    len(str(column)),
                    df[column].astype(str).str.len().max()
                ) * 10
                table.column(column, width=min(max_width, 200))
            
            # Verileri ekle
            for i, row in df.iterrows():
                values = [str(val) for val in row]
                table.insert("", "end", values=values)
            
            # Scrollbar ekle
            scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=table.yview)
            table.configure(yscrollcommand=scrollbar.set)
            
            # Yerleştir
            table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            logger.error(f"Tablo gösterimi hatası: {e}")
            logger.exception("Detaylı hata:")