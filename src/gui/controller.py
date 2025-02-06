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
from utils.helpers import reverse_calculate_value

class SimpleGUI:
    def __init__(self, controller_factory=None):
        self.controller_factory = controller_factory or get_controller_factory()
        
        # Ana pencere
        self.root = tk.Tk()
        self.root.title("Smart Saw Control Panel")
        self.root.geometry("768x520")
        
        # Değişkenler
        self.current_controller = tk.StringVar(value="Kontrol Sistemi Kapalı")
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
        
        self.last_update_time = None
        self.kesim_baslama_zamani = None
        self._create_widgets()
        self._setup_update_loop()

    def _create_widgets(self):
        """GUI bileşenlerini oluşturur"""
        # Kontrol Paneli
        control_frame = ttk.LabelFrame(self.root, text="Kontrol Sistemi", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Kontrol sistemi seçimi ve butonları (mevcut kod)
        ttk.Label(control_frame, text="Aktif Sistem:").pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, textvariable=self.current_controller).pack(side=tk.LEFT, padx=5)
        
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
        
        # Manuel Hız Kontrolü
        manual_frame = ttk.LabelFrame(self.root, text="Manuel Hız Kontrolü", padding=10)
        manual_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # İnme Hızı
        inme_frame = ttk.Frame(manual_frame)
        inme_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(inme_frame, text="İnme Hızı (mm/s):").pack(side=tk.LEFT)
        self.inme_hizi_entry = ttk.Entry(inme_frame, width=10)
        self.inme_hizi_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            inme_frame,
            text="İnme Hızı Gönder",
            command=lambda: self._send_manual_speed('inme')
        ).pack(side=tk.LEFT, padx=5)
        
        # Kesme Hızı
        kesme_frame = ttk.Frame(manual_frame)
        kesme_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(kesme_frame, text="Kesme Hızı (mm/s):").pack(side=tk.LEFT)
        self.kesme_hizi_entry = ttk.Entry(kesme_frame, width=10)
        self.kesme_hizi_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            kesme_frame,
            text="Kesme Hızı Gönder",
            command=lambda: self._send_manual_speed('kesme')
        ).pack(side=tk.LEFT, padx=5)
        
        # Hepsini Gönder Butonu
        ttk.Button(
            manual_frame,
            text="Hepsini Gönder",
            command=self._send_all_speeds
        ).pack(side=tk.LEFT, padx=5)
        
        # Ana bilgi paneli (notebook)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Kesim Bilgileri Sekmesi
        kesim_frame = ttk.Frame(notebook)
        notebook.add(kesim_frame, text="Kesim Bilgileri")
        self._create_info_grid(kesim_frame, [
            ('kesilen_parca_adeti', 'Kesilen Parça'),
            ('serit_kesme_hizi', 'Kesme Hızı'),
            ('serit_inme_hizi', 'İnme Hızı'),
            ('serit_motor_akim_a', 'Motor Akımı'),
            ('serit_sapmasi', 'Şerit Sapması'),
            ('kafa_yuksekligi_mm', 'Kafa Yüksekliği')
        ])
        
        # Temel Bilgiler Sekmesi
        temel_frame = ttk.Frame(notebook)
        notebook.add(temel_frame, text="Temel Bilgiler")
        self._create_info_grid(temel_frame, [
            ('makine_id', 'Makine ID'),
            ('serit_id', 'Şerit ID'),
            ('serit_dis_mm', 'Şerit Diş (mm)'),
            ('serit_tip', 'Şerit Tipi'),
            ('serit_marka', 'Şerit Markası'),
            ('serit_malz', 'Şerit Malzemesi')
        ])
        
        # Malzeme Bilgileri Sekmesi
        malzeme_frame = ttk.Frame(notebook)
        notebook.add(malzeme_frame, text="Malzeme Bilgileri")
        self._create_info_grid(malzeme_frame, [
            ('malzeme_cinsi', 'Malzeme Cinsi'),
            ('malzeme_sertlik', 'Malzeme Sertlik'),
            ('kesit_yapisi', 'Kesit Yapısı'),
            ('a_mm', 'A (mm)'),
            ('b_mm', 'B (mm)'),
            ('c_mm', 'C (mm)'),
            ('d_mm', 'D (mm)')
        ])
        
        # Motor ve Hareket Sekmesi
        motor_frame = ttk.Frame(notebook)
        notebook.add(motor_frame, text="Motor ve Hareket")
        self._create_info_grid(motor_frame, [
            ('serit_motor_akim_a', 'Şerit Motor Akım'),
            ('serit_motor_tork_percentage', 'Şerit Motor Tork'),
            ('inme_motor_akim_a', 'İnme Motor Akım'),
            ('inme_motor_tork_percentage', 'İnme Motor Tork'),
            ('serit_kesme_hizi', 'Kesme Hızı'),
            ('serit_inme_hizi', 'İnme Hızı'),
            ('kafa_yuksekligi_mm', 'Kafa Yüksekliği')
        ])
        
        # Sensör Bilgileri Sekmesi
        sensor_frame = ttk.Frame(notebook)
        notebook.add(sensor_frame, text="Sensör Bilgileri")
        self._create_info_grid(sensor_frame, [
            ('mengene_basinc_bar', 'Mengene Basıncı'),
            ('serit_gerginligi_bar', 'Şerit Gerginliği'),
            ('serit_sapmasi', 'Şerit Sapması'),
            ('ortam_sicakligi_c', 'Ortam Sıcaklığı'),
            ('ortam_nem_percentage', 'Ortam Nem'),
            ('sogutma_sivi_sicakligi_c', 'Soğutma Sıvısı Sıc.'),
            ('hidrolik_yag_sicakligi_c', 'Hidrolik Yağ Sıc.')
        ])
        
        # İvme Ölçer Sekmesi
        ivme_frame = ttk.Frame(notebook)
        notebook.add(ivme_frame, text="İvme Ölçer")
        self._create_info_grid(ivme_frame, [
            ('ivme_olcer_x', 'X Ekseni İvme'),
            ('ivme_olcer_y', 'Y Ekseni İvme'),
            ('ivme_olcer_z', 'Z Ekseni İvme'),
            ('ivme_olcer_x_hz', 'X Ekseni Frekans'),
            ('ivme_olcer_y_hz', 'Y Ekseni Frekans'),
            ('ivme_olcer_z_hz', 'Z Ekseni Frekans')
        ])
        
        # Varsayılan sekmeyi ayarla
        notebook.select(0)  # İlk sekme (Kesim Bilgileri) seçili olacak
        
        # Durum çubuğu
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        self.status_label = ttk.Label(
            status_frame,
            text=f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(
            status_frame,
            text="Uygulamayı Kapat",
            command=self._quit
        ).pack(side=tk.RIGHT)

    def _create_info_grid(self, parent, fields, columns=2):
        """Bilgi grid'ini oluşturur"""
        frame = ttk.LabelFrame(parent, text="Kesim Bilgileri", padding=(5, 5))
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Kesim zamanları için frame
        time_frame = ttk.LabelFrame(frame, text="Zaman Bilgileri", padding=(5, 5))
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Mevcut kesim bilgileri
        current_cut_frame = ttk.Frame(time_frame)
        current_cut_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(current_cut_frame, text="Mevcut Kesim Başlangıç:").pack(side=tk.LEFT)
        self.current_cut_start = ttk.Label(current_cut_frame, text="-")
        self.current_cut_start.pack(side=tk.LEFT, padx=5)
        
        # Önceki kesim bilgileri
        prev_cut_frame = ttk.Frame(time_frame)
        prev_cut_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(prev_cut_frame, text="Önceki Kesim:").pack(side=tk.LEFT)
        self.prev_cut_info = ttk.Label(prev_cut_frame, text="-")
        self.prev_cut_info.pack(side=tk.LEFT, padx=5)
        
        # Son güncelleme zamanı
        update_frame = ttk.Frame(time_frame)
        update_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(update_frame, text="Son Güncelleme:").pack(side=tk.LEFT)
        self.last_update_time = ttk.Label(update_frame, text="-")
        self.last_update_time.pack(side=tk.LEFT, padx=5)
        
        # Sensör değerleri için grid
        grid_frame = ttk.Frame(frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        row = 0
        col = 0
        self.value_labels = {}
        
        for field in fields:
            label = ttk.Label(grid_frame, text=f"{field}:")
            label.grid(row=row, column=col*2, sticky=tk.E, padx=5, pady=2)
            
            value_label = ttk.Label(grid_frame, text="-")
            value_label.grid(row=row, column=col*2+1, sticky=tk.W, padx=5, pady=2)
            
            self.value_labels[field] = value_label
            
            col += 1
            if col >= columns:
                col = 0
                row += 1

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
        self.last_update_time = datetime.now()
        self.status_label.config(
            text=f"Son güncelleme: {self.last_update_time.strftime('%H:%M:%S.%f')[:-3]}"
        )

    def _setup_update_loop(self):
        """Güncelleme döngüsünü başlatır"""
        def update_loop():
            # Son güncelleme zamanını kontrol et
            if self.last_update_time:
                gecen_sure = datetime.now() - self.last_update_time
                if gecen_sure.total_seconds() > 1:
                    self.status_label.config(
                        text=f"Son güncelleme: {self.last_update_time.strftime('%H:%M:%S.%f')[:-3]} (Veri alınamıyor)"
                    )
            
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
        """Arayüz verilerini günceller"""
        try:
            # Kesim durumunu kontrol et
            testere_durumu = processed_data.get('testere_durumu', 0)
            
            # Mevcut zaman
            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            self.last_update_time.config(text=current_time)
            
            # Kesim durumu değişimini kontrol et
            if testere_durumu == 3:  # Kesim yapılıyor
                if not hasattr(self, '_current_cut_start_time'):
                    self._current_cut_start_time = datetime.now()
                    self.current_cut_start.config(
                        text=self._current_cut_start_time.strftime('%H:%M:%S.%f')[:-3]
                    )
            elif hasattr(self, '_current_cut_start_time'):
                # Kesim bitti
                end_time = datetime.now()
                duration = end_time - self._current_cut_start_time
                duration_str = f"{int(duration.total_seconds())//60:02d}:{int(duration.total_seconds())%60:02d}.{str(duration.microseconds)[:3]}"
                
                # Önceki kesim bilgilerini güncelle
                self.prev_cut_info.config(
                    text=f"Başlangıç: {self._current_cut_start_time.strftime('%H:%M:%S.%f')[:-3]} "
                        f"Bitiş: {end_time.strftime('%H:%M:%S.%f')[:-3]} "
                        f"Süre: {duration_str}"
                )
                
                # Mevcut kesim bilgilerini temizle
                delattr(self, '_current_cut_start_time')
                self.current_cut_start.config(text="-")
            
            # Diğer değerleri güncelle
            for field, label in self.value_labels.items():
                value = processed_data.get(field, '-')
                if isinstance(value, float):
                    label.config(text=f"{value:.2f}")
                else:
                    label.config(text=str(value))
                    
        except Exception as e:
            logger.error(f"GUI güncelleme hatası: {str(e)}")
            logger.exception("Detaylı hata:")

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

