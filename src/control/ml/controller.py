# src/control/ml/controller.py
import time
import sqlite3
import threading
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from collections import deque
import os

from core.logger import logger
from core.constants import (
    ML_MODEL_PATH,
    SPEED_LIMITS,
    TestereState,
    MIN_SPEED_UPDATE_INTERVAL,
    BUFFER_SIZE,
    BUFFER_DURATION,
    KATSAYI,
    TORQUE_TO_CURRENT_A2,
    TORQUE_TO_CURRENT_A1,
    TORQUE_TO_CURRENT_A0
)
from utils.helpers import (
    reverse_calculate_value,
    get_current_time_ms,
    calculate_elapsed_time_ms,
    format_time
)
from utils.delay_calculator import calculate_control_delay

class MLController:
    def __init__(self):
        """ML tabanlı kontrol sistemi başlatılır"""
        self.cutting_start_time = None
        self.is_cutting = False
        self.last_update_time = 0
        
        # Thread-local storage için
        self.thread_local = threading.local()
        
        # Veritabanı dizinini oluştur
        os.makedirs('data', exist_ok=True)
        
        # Model ve özellikler
        try:
            self.model = joblib.load(ML_MODEL_PATH)
            logger.info("ML modeli başarıyla yüklendi")
        except Exception as e:
            logger.error(f"ML modeli yüklenemedi: {str(e)}")
            self.model = None
            
        # Giriş özelliklerinin sıralaması önemli
        self.input_features = [
            'akim_input',
            'sapma_input',
            'kesme_hizi',
            'inme_hizi'
        ]
        
        # Kesme hızı değişim buffer'ı
        self.kesme_hizi_degisim_buffer = 0.0
        
        # İlk çıktı kontrolü için
        self.first_output_sent = False
        self.last_sent_inme_hizi = None
        
        # Veri tamponları - constants.py'dan alınan boyut
        self.akim_buffer = deque(maxlen=BUFFER_SIZE)
        self.sapma_buffer = deque(maxlen=BUFFER_SIZE)
        self.kesme_hizi_buffer = deque(maxlen=BUFFER_SIZE)
        self.inme_hizi_buffer = deque(maxlen=BUFFER_SIZE)
        self.last_buffer_update = time.time()
    
    def _get_db(self):
        """Thread-safe veritabanı bağlantısı döndürür"""
        if not hasattr(self.thread_local, 'db'):
            try:
                self.thread_local.db = sqlite3.connect('data/ml_control.db')
                cursor = self.thread_local.db.cursor()
                
                # ML kontrol verilerini saklayacak tablo
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ml_control_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        akim_input REAL,
                        sapma_input REAL,
                        kesme_hizi_input REAL,
                        inme_hizi_input REAL,
                        yeni_kesme_hizi REAL,
                        yeni_inme_hizi REAL,
                        katsayi REAL,
                        ml_output REAL
                    )
                ''')
                self.thread_local.db.commit()
                logger.debug(f"Thread {threading.get_ident()} için yeni veritabanı bağlantısı oluşturuldu")
                
            except Exception as e:
                logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
                return None
                
        return self.thread_local.db

    def _save_control_data(self, akim: float, sapma: float, kesme_hizi: float, 
                          inme_hizi: float, yeni_kesme_hizi: float, yeni_inme_hizi: float,
                          katsayi: float, ml_output: float):
        """Kontrol verilerini veritabanına kaydeder"""
        try:
            db = self._get_db()
            if db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                cursor = db.cursor()
                cursor.execute('''
                    INSERT INTO ml_control_data 
                    (timestamp, akim_input, sapma_input, kesme_hizi_input, 
                     inme_hizi_input, yeni_kesme_hizi, yeni_inme_hizi, katsayi, ml_output)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (current_time, akim, sapma, kesme_hizi, inme_hizi, 
                     yeni_kesme_hizi, yeni_inme_hizi, katsayi, ml_output))
                
                db.commit()
                logger.debug(f"ML kontrol verisi kaydedildi - Zaman: {current_time}, Çıktı: {ml_output}")
                
        except Exception as e:
            logger.error(f"Veri kaydetme hatası: {str(e)}")

    def _update_buffers(self, akim, sapma, kesme_hizi, inme_hizi):
        """Veri tamponlarını günceller"""
        current_time = time.time()
        
        # Tamponları güncelle
        self.akim_buffer.append((current_time, akim))
        self.sapma_buffer.append((current_time, sapma))
        self.kesme_hizi_buffer.append((current_time, kesme_hizi))
        self.inme_hizi_buffer.append((current_time, inme_hizi))
            
    def _get_buffer_averages(self):
        """Tamponlardaki verilerin ortalamasını alır"""
        if not self.akim_buffer or not self.sapma_buffer or not self.kesme_hizi_buffer or not self.inme_hizi_buffer:
            return None, None, None, None
            
        akim_avg = sum(akim for _, akim in self.akim_buffer) / len(self.akim_buffer)
        sapma_avg = sum(sapma for _, sapma in self.sapma_buffer) / len(self.sapma_buffer)
        kesme_hizi_avg = sum(hiz for _, hiz in self.kesme_hizi_buffer) / len(self.kesme_hizi_buffer)
        inme_hizi_avg = sum(hiz for _, hiz in self.inme_hizi_buffer) / len(self.inme_hizi_buffer)
        
        return akim_avg, sapma_avg, kesme_hizi_avg, inme_hizi_avg
    
    def _torque_to_current(self, torque_percentage: float) -> float:
        """Makineden gelen tork yüzdesini akıma çevirir.
        
        f(x) = A2*x^2 + A1*x + A0
        x: serit_motor_tork_percentage (yüzde), çıktı: akım (A)
        
        Args:
            torque_percentage: serit_motor_tork_percentage (yüzde)
            
        Returns:
            float: Akım (A)
        """
        try:
            return (
                TORQUE_TO_CURRENT_A2 * (torque_percentage ** 2)
                + TORQUE_TO_CURRENT_A1 * torque_percentage
                + TORQUE_TO_CURRENT_A0
            )
        except Exception:
            return 0.0
    
    def predict_coefficient(self, serit_motor_akim_a: float, serit_sapmasi: float, serit_kesme_hizi: float, serit_inme_hizi: float) -> float:
        """ML modeli ile katsayı tahmin eder (-1 ile 1 arası)"""
        try:
            if self.model is None:
                return 0.0
                
            # Tamponları güncelle
            self._update_buffers(serit_motor_akim_a, serit_sapmasi, serit_kesme_hizi, serit_inme_hizi)
            
            # Ortalama değerleri al
            avg_akim, avg_sapma, avg_kesme_hizi, avg_inme_hizi = self._get_buffer_averages()
            if avg_akim is None:
                logger.warning("Yeterli veri yok, ham değerler kullanılıyor")
                avg_akim, avg_sapma, avg_kesme_hizi, avg_inme_hizi = serit_motor_akim_a, serit_sapmasi, serit_kesme_hizi, serit_inme_hizi
            
            logger.debug(f"Ortalama değerler - Akım: {avg_akim:.2f}A, Sapma: {avg_sapma:.2f}mm, Kesme Hızı: {avg_kesme_hizi:.2f}, İnme Hızı: {avg_inme_hizi:.2f}")
                
            # Giriş verisini oluştur
            input_data = pd.DataFrame([[avg_akim, avg_sapma, avg_kesme_hizi, avg_inme_hizi]], 
                                    columns=self.input_features)
            
            # Tahmin yap
            coefficient = self.model.predict(input_data)[0]
            
            # Katsayıyı -1 ile 1 arasına sınırla
            coefficient = max(-1.0, min(coefficient, 1.0))
            
            # Yeni hızları hesapla
            new_inme_hizi = avg_inme_hizi + coefficient
            new_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(new_inme_hizi, SPEED_LIMITS['inme']['max']))
            
            # İnme hızı değişim yüzdesini hesapla
            inme_hizi_degisim = new_inme_hizi - avg_inme_hizi
            inme_degisim_yuzdesi = self._calculate_speed_change_percentage(inme_hizi_degisim, 'inme')
            
            # Kesme hızı için değişimi hesapla
            if coefficient < 0:
                # Negatif değişim: mevcut hız ile minimum hız arası
                speed_range = avg_kesme_hizi - SPEED_LIMITS['kesme']['min']
                kesme_hizi_degisim = -(speed_range * abs(inme_degisim_yuzdesi) / 100)
            else:
                # Pozitif değişim: mevcut hız ile maksimum hız arası
                speed_range = SPEED_LIMITS['kesme']['max'] - avg_kesme_hizi
                kesme_hizi_degisim = (speed_range * abs(inme_degisim_yuzdesi) / 100)
            
            # Yeni kesme hızını hesapla
            new_kesme_hizi = avg_kesme_hizi + kesme_hizi_degisim
            new_kesme_hizi = max(SPEED_LIMITS['kesme']['min'], min(new_kesme_hizi, SPEED_LIMITS['kesme']['max']))
            
            # Verileri kaydet
            self._save_control_data(
                akim=avg_akim,
                sapma=avg_sapma,
                kesme_hizi=avg_kesme_hizi,
                inme_hizi=avg_inme_hizi,
                yeni_kesme_hizi=new_kesme_hizi,
                yeni_inme_hizi=new_inme_hizi,
                katsayi=KATSAYI,
                ml_output=coefficient
            )
            
            return coefficient
            
        except Exception as e:
            logger.error(f"Katsayı tahmini hatası: {str(e)}")
            return 0.0
    
    def _calculate_speed_change_percentage(self, speed_change: float, speed_type: str) -> float:
        """Hız değişiminin yüzdesini hesaplar"""
        speed_range = SPEED_LIMITS[speed_type]['max'] - SPEED_LIMITS[speed_type]['min']
        if speed_range == 0:
            return 0
        return (speed_change / speed_range) * 100

    def _calculate_speed_change_from_percentage(self, percentage: float, speed_type: str) -> float:
        """Yüzdeye göre hız değişimini hesaplar"""
        speed_range = SPEED_LIMITS[speed_type]['max'] - SPEED_LIMITS[speed_type]['min']
        return (percentage / 100) * speed_range

    def kesim_durumu_kontrol(self, testere_durumu: int, modbus_client=None) -> bool:
        """Kesim durumunu kontrol eder"""
        current_time = time.time() * 1000
        
        if testere_durumu != TestereState.KESIM_YAPILIYOR.value:
            if self.is_cutting:
                self._log_kesim_bitis()
                self.is_cutting = False
                self.cutting_start_time = None
            return False

        if not self.is_cutting:
            self._log_kesim_baslangic()
            self.is_cutting = True
            self.cutting_start_time = current_time
            
            # İnme hızını register'dan okuyarak dinamik bekleme süresini hesapla
            self.initial_delay = calculate_control_delay(modbus_client)
            logger.info(f"ML - Register'dan hesaplanan bekleme süresi: {self.initial_delay/1000:.1f} saniye")

        # Başlangıç gecikmesi kontrolü
        if hasattr(self, 'initial_delay') and self.initial_delay > 0:
            if current_time - self.cutting_start_time < self.initial_delay:
                kalan_sure = int((self.initial_delay - (current_time - self.cutting_start_time)) / 1000)
                if kalan_sure % 5 == 0:
                    logger.info(f"ML kontrol sisteminin devreye girmesine {kalan_sure} saniye kaldı...")
                return False

        return True

    def hiz_guncelleme_zamani_geldi_mi(self) -> bool:
        """Hız güncelleme zamanının gelip gelmediğini kontrol eder"""
        current_time = time.time()
        return current_time - self.last_update_time >= MIN_SPEED_UPDATE_INTERVAL

    def adjust_speeds(self, processed_data: dict, modbus_client, last_modbus_write_time: float,
                     speed_adjustment_interval: float, prev_current: float) -> Tuple[float, Optional[float]]:
        """Hızları ayarlar"""
        if not self.kesim_durumu_kontrol(processed_data.get('testere_durumu'), modbus_client):
            return last_modbus_write_time, None

        if not self.hiz_guncelleme_zamani_geldi_mi():
            return last_modbus_write_time, None

        try:
            # Mevcut değerleri al
            # Not: Akım doğrudan alınmıyor, tork yüzdesi f(x) ile akıma dönüştürülüyor.
            torque_percentage = float(processed_data.get('serit_motor_tork_percentage', 0))
            current_akim = float(self._torque_to_current(torque_percentage))
            current_sapma = float(processed_data.get('serit_sapmasi', 0))
            current_kesme_hizi = float(processed_data.get('serit_kesme_hizi', SPEED_LIMITS['kesme']['min']))
            
            # İnme hızı için: ilk çıktıdan sonra bir önceki gönderilen değeri kullan
            if self.first_output_sent and self.last_sent_inme_hizi is not None:
                current_inme_hizi = self.last_sent_inme_hizi
                logger.debug(f"ML - Bir önceki gönderilen inme hızı kullanılıyor: {current_inme_hizi:.2f}")
            else:
                current_inme_hizi = float(processed_data.get('serit_inme_hizi', SPEED_LIMITS['inme']['min']))
                logger.debug(f"ML - Makineden okunan inme hızı kullanılıyor: {current_inme_hizi:.2f}")
            
            # ML modelinden katsayı tahmin et
            coefficient = self.predict_coefficient(current_akim, current_sapma, current_kesme_hizi, current_inme_hizi)
            
            # Katsayıyı KATSAYI ile çarp
            coefficient = coefficient * KATSAYI
            logger.debug(f"ML katsayı çıktısı: {coefficient:.3f}")
            
            # İnme hızı değişimini hesapla
            inme_hizi_degisim = coefficient
            new_inme_hizi = current_inme_hizi + inme_hizi_degisim
            
            # İnme hızı sınırlarını uygula
            new_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(new_inme_hizi, SPEED_LIMITS['inme']['max']))
            
            # İnme hızı değişim yüzdesini hesapla
            inme_degisim_yuzdesi = self._calculate_speed_change_percentage(new_inme_hizi - current_inme_hizi, 'inme')
            
            # Kesme hızı için değişimi hesapla
            if coefficient < 0:
                # Negatif değişim: mevcut hız ile minimum hız arası
                speed_range = current_kesme_hizi - SPEED_LIMITS['kesme']['min']
                kesme_hizi_degisim = -(speed_range * abs(inme_degisim_yuzdesi) / 100)
            else:
                # Pozitif değişim: mevcut hız ile maksimum hız arası
                speed_range = SPEED_LIMITS['kesme']['max'] - current_kesme_hizi
                kesme_hizi_degisim = (speed_range * abs(inme_degisim_yuzdesi) / 100)
            
            # Kesme hızı değişimini buffer'a ekle
            self.kesme_hizi_degisim_buffer += kesme_hizi_degisim
            
            # Modbus'a yazma işlemleri
            if new_inme_hizi != current_inme_hizi:
                # İnme hızını yaz
                inme_hizi_is_negative = new_inme_hizi < 0
                reverse_calculate_value(modbus_client, new_inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
                logger.debug(f"Yeni inme hızı: {new_inme_hizi:.2f}")
                
                # İlk çıktı gönderildi olarak işaretle ve son gönderilen değeri kaydet
                self.first_output_sent = True
                self.last_sent_inme_hizi = new_inme_hizi
                
                # Kesme hızı için buffer kontrolü
                if abs(self.kesme_hizi_degisim_buffer) >= 0.9:
                    new_kesme_hizi = current_kesme_hizi + self.kesme_hizi_degisim_buffer
                    new_kesme_hizi = max(SPEED_LIMITS['kesme']['min'], 
                                       min(new_kesme_hizi, SPEED_LIMITS['kesme']['max']))
                    
                    # Kesme hızını yaz
                    kesme_hizi_is_negative = new_kesme_hizi < 0
                    reverse_calculate_value(modbus_client, new_kesme_hizi, 'serit_kesme_hizi', kesme_hizi_is_negative)
                    logger.debug(f"Yeni kesme hızı: {new_kesme_hizi:.2f}")
                    
                    # Buffer'ı sıfırla
                    self.kesme_hizi_degisim_buffer = 0.0
            
            # Son güncelleme zamanını kaydet
            self.last_update_time = time.time()
            
            return last_modbus_write_time, coefficient
            
        except Exception as e:
            logger.error(f"ML kontrol hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            return last_modbus_write_time, None

    def _log_kesim_baslangic(self):
        """Kesim başlangıcını loglar"""
        self.cutting_start_time = time.time() * 1000
        self.is_cutting = True
        start_time_str = get_current_time_ms()
        logger.info("\n" + "="*60)
        logger.info("YENİ KESİM BAŞLADI (ML Kontrol)")
        logger.info("-"*60)
        logger.info(f"Başlangıç Zamanı : {start_time_str}")
        logger.info("Kontrol sistemi başlangıç gecikmesi sonrası devreye girecek...")
        logger.info("="*60 + "\n")

    def _log_kesim_bitis(self):
        """Kesim bitişini loglar"""
        if self.cutting_start_time:
            elapsed = calculate_elapsed_time_ms(self.cutting_start_time)
            end_time_str = get_current_time_ms()
            elapsed_str = format_time(elapsed)
            logger.info("\n" + "="*60)
            logger.info("KESİM BİTTİ (ML Kontrol)")
            logger.info("-"*60)
            logger.info(f"Bitiş Zamanı     : {end_time_str}")
            logger.info(f"Toplam Süre      : {elapsed_str}")
            logger.info("="*60 + "\n")
        
        self.is_cutting = False
        self.cutting_start_time = None
        
        # İlk çıktı kontrolünü sıfırla
        self.first_output_sent = False
        self.last_sent_inme_hizi = None

    def __del__(self):
        """Yıkıcı metod - tüm veritabanı bağlantılarını kapatır"""
        if hasattr(self.thread_local, 'db'):
            try:
                self.thread_local.db.close()
            except Exception:
                pass


# Global controller nesnesi
ml_controller = MLController()

def adjust_speeds_ml(processed_data: dict, modbus_client, last_modbus_write_time: float,
                    speed_adjustment_interval: float, prev_current: float) -> Tuple[float, Optional[float]]:
    """ML kontrol için hız ayarlama fonksiyonu"""
    return ml_controller.adjust_speeds(
        processed_data=processed_data,
        modbus_client=modbus_client,
        last_modbus_write_time=last_modbus_write_time,
        speed_adjustment_interval=speed_adjustment_interval,
        prev_current=prev_current
    )