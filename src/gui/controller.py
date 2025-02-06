# src/gui/controller.py
import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
from typing import Dict, Optional
from queue import Queue
import logging

from core import logger
from control import ControllerType, get_controller_factory
from models import ProcessedData
from utils.helpers import reverse_calculate_value

class GUILogHandler(logging.Handler):
    """GUI için özel log handler"""
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        
    def emit(self, record):
        try:
            # Log seviyesine göre renk belirle
            level_map = {
                'DEBUG': 'INFO',
                'INFO': 'INFO',
                'WARNING': 'WARNING',
                'ERROR': 'ERROR',
                'CRITICAL': 'ERROR'
            }
            level = level_map.get(record.levelname, 'INFO')
            
            # Log mesajını GUI'ye ekle
            self.gui.add_log(record.getMessage(), level)
        except Exception:
            self.handleError(record)

class SimpleGUI:
    def __init__(self, controller_factory=None):
        self.controller_factory = controller_factory or get_controller_factory()
        
        # Ana pencere
        self.root = tk.Tk()
        self.root.title("Smart Saw Control Panel")
        
        # Logger'a GUI handler'ı ekle
        self.log_handler = GUILogHandler(self)
        self.log_handler.setFormatter(
            logging.Formatter('%(message)s')  # Timestamp GUI'de ekleniyor
        )
        logger.addHandler(self.log_handler)
        
        # Değişkenler
        self.current_controller = tk.StringVar(value="Kontrol Sistemi Kapalı")
        self._last_update_time = None  # datetime nesnesi
        self._current_cut_start_time = None  # datetime nesnesi
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
            'kafa_yuksekligi_mm': tk.StringVar(value="0.0 mm"),
            'serit_motor_akim_a': tk.StringVar(value="0.0 A"),
            'serit_motor_tork_percentage': tk.StringVar(value="0.0 %"),
            'inme_motor_akim_a': tk.StringVar(value="0.0 A"),
            'inme_motor_tork_percentage': tk.StringVar(value="0.0 %"),
            
            # Basınç ve sıcaklık bilgileri
            'mengene_basinc_bar': tk.StringVar(value="0.0 bar"),
            'serit_gerginligi_bar': tk.StringVar(value="0.0 bar"),
            'serit_sapmasi': tk.StringVar(value="0.0 mm"),
            'ortam_sicakligi_c': tk.StringVar(value="0.0 °C"),
            'ortam_nem_percentage': tk.StringVar(value="0.0 %"),
            'sogutma_sivi_sicakligi_c': tk.StringVar(value="0.0 °C"),
            'hidrolik_yag_sicakligi_c': tk.StringVar(value="0.0 °C"),
            
            # İvme ölçer bilgileri
            'ivme_olcer_x': tk.StringVar(value="0.0 g"),
            'ivme_olcer_y': tk.StringVar(value="0.0 g"),
            'ivme_olcer_z': tk.StringVar(value="0.0 g"),
            'ivme_olcer_x_hz': tk.StringVar(value="0.0 Hz"),
            'ivme_olcer_y_hz': tk.StringVar(value="0.0 Hz"),
            'ivme_olcer_z_hz': tk.StringVar(value="0.0 Hz"),
            
            # Durum bilgileri
            'testere_durumu': tk.StringVar(value="Bekleniyor"),
            'alarm_status': tk.StringVar(value="-"),
            'alarm_bilgisi': tk.StringVar(value="-"),
            'serit_kesme_hizi': tk.StringVar(value="0.0 mm/s"),
            'serit_inme_hizi': tk.StringVar(value="0.0 mm/s"),
            
            # Kesim bilgileri
            'kesilen_parca_adeti': tk.StringVar(value="0"),
            'kesim_baslama': tk.StringVar(value="-"),
            'kesim_sure': tk.StringVar(value="-"),
            'onceki_kesim_baslama': tk.StringVar(value="-"),
            'onceki_kesim_bitis': tk.StringVar(value="-"),
            'onceki_kesim_sure': tk.StringVar(value="-")
        }
        
        self.kesim_baslama_zamani = None
        self._create_widgets()
        
        # Pencereyi içeriğe göre boyutlandır
        self.root.update_idletasks()  # Tüm widget'ların boyutlarının hesaplanmasını sağla
        
        # Minimum boyutu ayarla
        width = max(
            self.root.winfo_reqwidth(),  # İçeriğin istediği genişlik
            800  # Minimum genişlik
        )
        height = max(
            self.root.winfo_reqheight(),  # İçeriğin istediği yükseklik
            600  # Minimum yükseklik
        )
        
        # Ekran boyutlarını al
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Pencere boyutunu ekran boyutuna göre sınırla
        width = min(width, screen_width - 100)
        height = min(height, screen_height - 100)
        
        # Minimum boyutu ayarla
        self.root.minsize(width, height)
        
        # Pencereyi ekranın ortasına konumlandır
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Yeniden boyutlandırmaya izin ver
        self.root.resizable(True, True)
        
        self._setup_update_loop()

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
        
        # Modbus Durum Göstergesi
        modbus_frame = ttk.LabelFrame(top_frame, text="Modbus Durumu", padding=(5, 5))
        modbus_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.modbus_status = ttk.Label(modbus_frame, text="Bağlı Değil", foreground="red")
        self.modbus_status.pack(fill=tk.X, padx=5, pady=5)
        
        # Kontrol Sistemi
        control_frame = ttk.LabelFrame(top_frame, text="Kontrol Sistemi", padding=(5, 5))
        control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(control_frame, text="Aktif Sistem:").pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, textvariable=self.current_controller).pack(side=tk.LEFT, padx=5)
        
        for controller in ControllerType:
            ttk.Button(
                control_frame,
                text=f"{controller.value.capitalize()}",
                command=lambda c=controller: self._switch_controller(c)
            ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="Kapat",
            command=self._disable_controller
        ).pack(side=tk.LEFT, padx=2)
        
        # Manuel Hız Kontrolü
        speed_frame = ttk.LabelFrame(left_panel, text="Manuel Hız Kontrolü", padding=(5, 5))
        speed_frame.pack(fill=tk.X, pady=5)
        
        # İnme Hızı
        inme_frame = ttk.Frame(speed_frame)
        inme_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(inme_frame, text="İnme Hızı (mm/s):").pack(side=tk.LEFT)
        self.inme_hizi_entry = ttk.Entry(inme_frame, width=8)
        self.inme_hizi_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            inme_frame,
            text="Gönder",
            command=lambda: self._send_manual_speed('inme')
        ).pack(side=tk.LEFT)
        
        # Kesme Hızı
        kesme_frame = ttk.Frame(speed_frame)
        kesme_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(kesme_frame, text="Kesme Hızı (mm/s):").pack(side=tk.LEFT)
        self.kesme_hizi_entry = ttk.Entry(kesme_frame, width=8)
        self.kesme_hizi_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            kesme_frame,
            text="Gönder",
            command=lambda: self._send_manual_speed('kesme')
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            speed_frame,
            text="Hepsini Gönder",
            command=self._send_all_speeds
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
        self.value_labels = {}
        
        for i, (field, label) in enumerate(fields):
            ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.E, padx=5, pady=2)
            value_label = ttk.Label(parent, text="-")
            value_label.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.value_labels[field] = value_label

    def _switch_controller(self, controller_type: ControllerType):
        """Kontrol sistemini değiştirir"""
        try:
            # Önce mevcut kontrolcüyü kapat
            self.controller_factory.set_controller(None)
            time.sleep(0.5)  # Biraz daha uzun bekleme
            
            # Yeni kontrolcüyü etkinleştir
            if not isinstance(controller_type, ControllerType):
                logger.error(f"Geçersiz kontrol sistemi tipi: {controller_type}")
                return
                
            self.controller_factory.set_controller(controller_type)
            self.current_controller.set(f"{controller_type.value.capitalize()} Kontrol Aktif")
            logger.info(f"Kontrol sistemi değiştirildi: {controller_type.value}")
        except Exception as e:
            logger.error(f"Kontrol sistemi değiştirilemedi: {str(e)}")
            logger.exception("Detaylı hata:")
            self.current_controller.set("Kontrol Sistemi Kapalı")

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
            0: "Bekleniyor",
            1: "Hazırlanıyor",
            2: "Hazır",
            3: "Kesim Yapılıyor",
            4: "Tamamlandı",
            5: "Hata"
        }.get(testere_durumu, "Bilinmiyor")
        
        self.current_values['testere_durumu'].set(durum_text)
        self.current_values['alarm_status'].set(str(processed_data.get('alarm_status', '-')))
        self.current_values['alarm_bilgisi'].set(str(processed_data.get('alarm_bilgisi', '-')))
        
        # Kesim durumunu kontrol et
        if testere_durumu == 3:  # Kesim yapılıyor
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
        elif testere_durumu != 3 and self.kesim_baslama_zamani:
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
        # Log handler'ı kaldır
        logger.removeHandler(self.log_handler)
        self.root.quit()

    def start(self):
        """GUI'yi başlatır"""
        self.root.mainloop()

    def update_data(self, processed_data: Dict):
        """Arayüz verilerini günceller"""
        try:
            # Modbus durumunu güncelle
            if 'modbus_connected' in processed_data:
                self.update_modbus_status(
                    processed_data['modbus_connected'],
                    processed_data.get('modbus_ip', '192.168.11.186')
                )
            
            # Kesim durumunu kontrol et
            testere_durumu = processed_data.get('testere_durumu')
            if testere_durumu == TestereState.CUTTING.value:
                if not hasattr(self, '_cutting_start_time'):
                    self._cutting_start_time = datetime.now()
                    self.current_cut_start.config(
                        text=self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3]
                    )
                    self.add_log("Yeni kesim başladı", "INFO")
                else:
                    # Mevcut kesim süresini güncelle
                    elapsed = datetime.now() - self._cutting_start_time
                    minutes = int(elapsed.total_seconds() // 60)
                    seconds = int(elapsed.total_seconds() % 60)
                    milliseconds = int((elapsed.total_seconds() * 1000) % 1000)
                    self.current_cut_duration = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
                    
            elif hasattr(self, '_cutting_start_time'):
                # Kesim bitti
                end_time = datetime.now()
                elapsed = end_time - self._cutting_start_time
                minutes = int(elapsed.total_seconds() // 60)
                seconds = int(elapsed.total_seconds() % 60)
                milliseconds = int((elapsed.total_seconds() * 1000) % 1000)
                
                # Önceki kesim bilgilerini güncelle
                self.prev_cut_start.config(text=self._cutting_start_time.strftime('%H:%M:%S.%f')[:-3])
                self.prev_cut_end.config(text=end_time.strftime('%H:%M:%S.%f')[:-3])
                self.prev_cut_duration.config(text=f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}")
                
                # Mevcut kesim bilgilerini temizle
                self.current_cut_start.config(text="-")
                delattr(self, '_cutting_start_time')
                self.add_log("Kesim tamamlandı", "INFO")
            
            # Değerleri güncelle
            for field, label in self.value_labels.items():
                if field in processed_data:
                    value = processed_data[field]
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    else:
                        formatted_value = str(value)
                    label.config(text=formatted_value)
            
            # Durum çubuğunu güncelle
            self.status_label.config(
                text=f"Son güncelleme: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}"
            )
            
            # Önemli değerleri kontrol et ve log ekle
            self._check_critical_values(processed_data)
            
        except Exception as e:
            logger.error(f"Veri güncelleme hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            self.add_log(f"Veri güncelleme hatası: {str(e)}", "ERROR")

    def _check_critical_values(self, data: Dict):
        """Kritik değerleri kontrol eder ve gerekirse log ekler"""
        # Akım kontrolü
        current = float(data.get('serit_motor_akim_a', 0))
        if current > 25:
            self.add_log(f"Yüksek motor akımı: {current:.2f}A", "WARNING")
        elif current > 30:
            self.add_log(f"Kritik motor akımı: {current:.2f}A", "ERROR")
            
        # Sapma kontrolü
        deviation = float(data.get('serit_sapmasi', 0))
        if abs(deviation) > 0.5:
            self.add_log(f"Yüksek şerit sapması: {deviation:.2f}mm", "WARNING")
        elif abs(deviation) > 1.0:
            self.add_log(f"Kritik şerit sapması: {deviation:.2f}mm", "ERROR")
            
        # Titreşim kontrolü
        vib_x = float(data.get('ivme_olcer_x_hz', 0))
        vib_y = float(data.get('ivme_olcer_y_hz', 0))
        vib_z = float(data.get('ivme_olcer_z_hz', 0))
        max_vib = max(vib_x, vib_y, vib_z)
        
        if max_vib > 1.0:
            self.add_log(f"Yüksek titreşim: {max_vib:.2f}Hz", "WARNING")
        elif max_vib > 2.0:
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
            # Önce inme hızını gönder
            self._send_manual_speed('inme')
            
            # Modbus yazma işlemleri arasında biraz bekle
            self.root.after(110)  # 110ms bekle
            
            # Sonra kesme hızını gönder
            self._send_manual_speed('kesme')
            
        except Exception as e:
            logger.error(f"Toplu hız gönderme hatası: {str(e)}")
            logger.exception("Detaylı hata:")

    def update_modbus_status(self, is_connected: bool, ip_address: str = None):
        """Modbus bağlantı durumunu günceller"""
        if is_connected:
            self.modbus_status.config(
                text=f"Bağlı - {ip_address}",
                foreground="green"
            )
        else:
            self.modbus_status.config(
                text="Bağlı Değil",
                foreground="red"
            )

    def add_log(self, message: str, level: str = 'INFO'):
        """Log mesajı ekler"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_message = f"{timestamp} [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)  # Son mesaja kaydır

