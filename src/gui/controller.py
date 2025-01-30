# src/gui/controller.py
import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
from typing import Dict, Optional
from queue import Queue

from core import logger
from control import ControllerType, get_controller_factory
from models import ProcessedData

class SimpleGUI:
    def __init__(self):
        self.controller_factory = get_controller_factory()
        
        # Ana pencere
        self.root = tk.Tk()
        self.root.title("Smart Saw Control Panel")
        self.root.geometry("800x600")
        
        # Değişkenler
        self.current_controller = tk.StringVar(value="Kontrol Sistemi Kapalı")
        self.current_values = {
            'akim': tk.StringVar(value="0.0 A"),
            'kesme_hizi': tk.StringVar(value="0.0 mm/s"),
            'inme_hizi': tk.StringVar(value="0.0 mm/s"),
            'sapma': tk.StringVar(value="0.0 mm"),
            'yukseklik': tk.StringVar(value="0.0 mm"),
            'durum': tk.StringVar(value="Bekleniyor")
        }
        
        self._create_widgets()
        self._setup_update_loop()

    def _create_widgets(self):
        """GUI bileşenlerini oluşturur"""
        # Kontrol Paneli
        control_frame = ttk.LabelFrame(self.root, text="Kontrol Sistemi", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Kontrol sistemi seçimi
        ttk.Label(control_frame, text="Aktif Sistem:").pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, textvariable=self.current_controller).pack(side=tk.LEFT, padx=5)
        
        # Kontrol butonları
        for controller in ControllerType:
            ttk.Button(
                control_frame,
                text=f"{controller.value.capitalize()} Kontrol",
                command=lambda c=controller: self._switch_controller(c)
            ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Kapat",
            command=self._disable_controller
        ).pack(side=tk.LEFT, padx=5)
        
        # Anlık Değerler Paneli
        values_frame = ttk.LabelFrame(self.root, text="Anlık Değerler", padding=10)
        values_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Değer göstergeleri
        for i, (key, label) in enumerate([
            ('akim', 'Motor Akımı'),
            ('kesme_hizi', 'Kesme Hızı'),
            ('inme_hizi', 'İnme Hızı'),
            ('sapma', 'Şerit Sapması'),
            ('yukseklik', 'Kafa Yüksekliği'),
            ('durum', 'Sistem Durumu')
        ]):
            row = i // 2
            col = i % 2
            
            frame = ttk.Frame(values_frame)
            frame.grid(row=row, column=col, padx=10, pady=5, sticky='ew')
            
            ttk.Label(frame, text=f"{label}:").pack(side=tk.LEFT)
            ttk.Label(
                frame,
                textvariable=self.current_values[key],
                width=15,
                anchor='e'
            ).pack(side=tk.RIGHT)
        
        # Durum çubuğu
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        self.status_label = ttk.Label(
            status_frame,
            text=f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Kapatma butonu
        ttk.Button(
            status_frame,
            text="Uygulamayı Kapat",
            command=self._quit
        ).pack(side=tk.RIGHT)

    def _switch_controller(self, controller_type: ControllerType):
        """Kontrol sistemini değiştirir"""
        try:
            self.controller_factory.set_controller(controller_type)
            self.current_controller.set(f"{controller_type.value.capitalize()} Kontrol Aktif")
            logger.info(f"Kontrol sistemi değiştirildi: {controller_type.value}")
        except Exception as e:
            logger.error(f"Kontrol sistemi değiştirilemedi: {str(e)}")

    def _disable_controller(self):
        """Kontrol sistemini kapatır"""
        self.current_controller.set("Kontrol Sistemi Kapalı")
        logger.info("Kontrol sistemi kapatıldı")

    def _update_values(self, processed_data: Dict):
        """Gösterilen değerleri günceller"""
        self.current_values['akim'].set(f"{processed_data.get('serit_motor_akim_a', 0):.1f} A")
        self.current_values['kesme_hizi'].set(f"{processed_data.get('serit_kesme_hizi', 0):.1f} mm/s")
        self.current_values['inme_hizi'].set(f"{processed_data.get('serit_inme_hizi', 0):.1f} mm/s")
        self.current_values['sapma'].set(f"{processed_data.get('serit_sapmasi', 0):.2f} mm")
        self.current_values['yukseklik'].set(f"{processed_data.get('kafa_yuksekligi_mm', 0):.1f} mm")
        
        testere_durumu = processed_data.get('testere_durumu', 0)
        durum_text = {
            0: "Bekleniyor",
            1: "Hazırlanıyor",
            2: "Hazır",
            3: "Kesim Yapılıyor",
            4: "Tamamlandı",
            5: "Hata"
        }.get(testere_durumu, "Bilinmiyor")
        
        self.current_values['durum'].set(durum_text)
        
        # Durum çubuğunu güncelle
        self.status_label.config(
            text=f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _setup_update_loop(self):
        """Güncelleme döngüsünü başlatır"""
        def update_loop():
            # Her 100ms'de bir güncelle
            self.root.after(100, update_loop)
        
        update_loop()

    def _quit(self):
        """Uygulamayı kapatır"""
        self.root.quit()

    def start(self):
        """GUI'yi başlatır"""
        self.root.mainloop()

    def update_data(self, processed_data: Dict):
        """Dışarıdan veri güncellemesi için"""
        self._update_values(processed_data)

