# src/control/ml/controller.py
import time
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from collections import deque

from core.logger import logger
from core.constants import (
    ML_MODEL_PATH,
    SPEED_LIMITS,
    TestereState,
    MIN_SPEED_UPDATE_INTERVAL,
    BASLANGIC_GECIKMESI,
    BUFFER_SIZE,
    BUFFER_DURATION
)
from utils.helpers import (
    reverse_calculate_value,
    get_current_time_ms,
    calculate_elapsed_time_ms,
    format_time
)

class MLController:
    def __init__(self):
        """ML tabanlı kontrol sistemi başlatılır"""
        self.cutting_start_time = None
        self.is_cutting = False
        self.last_update_time = 0
        
        # Model ve özellikler
        try:
            self.model = joblib.load(ML_MODEL_PATH)
            logger.info("ML modeli başarıyla yüklendi")
        except Exception as e:
            logger.error(f"ML modeli yüklenemedi: {str(e)}")
            self.model = None
            
        self.input_features = ['serit_motor_akim_a', 'serit_kesme_hizi', 'serit_inme_hizi']
        
        # Kesme hızı değişim buffer'ı
        self.kesme_hizi_degisim_buffer = 0.0
        
        # Veri tamponları
        self.akim_buffer = deque(maxlen=BUFFER_SIZE)
        self.kesme_hizi_buffer = deque(maxlen=BUFFER_SIZE)
        self.inme_hizi_buffer = deque(maxlen=BUFFER_SIZE)
        self.last_buffer_update = time.time()
    
    def _update_buffers(self, akim, kesme_hizi, inme_hizi):
        """Veri tamponlarını günceller"""
        current_time = time.time()
        
        # Tamponları güncelle
        self.akim_buffer.append((current_time, akim))
        self.kesme_hizi_buffer.append((current_time, kesme_hizi))
        self.inme_hizi_buffer.append((current_time, inme_hizi))
        
        # Eski verileri temizle (BUFFER_DURATION saniyeden eski)
        while self.akim_buffer and current_time - self.akim_buffer[0][0] > BUFFER_DURATION:
            self.akim_buffer.popleft()
        while self.kesme_hizi_buffer and current_time - self.kesme_hizi_buffer[0][0] > BUFFER_DURATION:
            self.kesme_hizi_buffer.popleft()
        while self.inme_hizi_buffer and current_time - self.inme_hizi_buffer[0][0] > BUFFER_DURATION:
            self.inme_hizi_buffer.popleft()
            
    def _get_buffer_averages(self):
        """Tamponlardaki verilerin ortalamasını alır"""
        if not self.akim_buffer or not self.kesme_hizi_buffer or not self.inme_hizi_buffer:
            return None, None, None
            
        akim_avg = sum(akim for _, akim in self.akim_buffer) / len(self.akim_buffer)
        kesme_hizi_avg = sum(hiz for _, hiz in self.kesme_hizi_buffer) / len(self.kesme_hizi_buffer)
        inme_hizi_avg = sum(hiz for _, hiz in self.inme_hizi_buffer) / len(self.inme_hizi_buffer)
        
        return akim_avg, kesme_hizi_avg, inme_hizi_avg
    
    def predict_next_speed(self, serit_motor_akim_a: float, serit_kesme_hizi: float, serit_inme_hizi: float) -> float:
        """Bir sonraki şerit inme hızını tahmin eder"""
        try:
            if self.model is None:
                return serit_inme_hizi
                
            # Tamponları güncelle
            self._update_buffers(serit_motor_akim_a, serit_kesme_hizi, serit_inme_hizi)
            
            # Ortalama değerleri al
            avg_akim, avg_kesme_hizi, avg_inme_hizi = self._get_buffer_averages()
            if avg_akim is None:
                logger.warning("Yeterli veri yok, ham değerler kullanılıyor")
                avg_akim, avg_kesme_hizi, avg_inme_hizi = serit_motor_akim_a, serit_kesme_hizi, serit_inme_hizi
            
            logger.debug(f"Ortalama değerler - Akım: {avg_akim:.2f}A, Kesme Hızı: {avg_kesme_hizi:.2f}, İnme Hızı: {avg_inme_hizi:.2f}")
                
            # Giriş verisini oluştur
            input_data = pd.DataFrame([[avg_akim, avg_kesme_hizi, avg_inme_hizi]], 
                                    columns=self.input_features)
            
            # Tahmin yap
            predicted_speed = self.model.predict(input_data)[0]
            
            # Hız sınırlarını uygula
            predicted_speed = max(SPEED_LIMITS['inme']['min'], 
                                min(predicted_speed, SPEED_LIMITS['inme']['max']))
            
            return predicted_speed
            
        except Exception as e:
            logger.error(f"Hız tahmini hatası: {str(e)}")
            return serit_inme_hizi
    
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

    def kesim_durumu_kontrol(self, testere_durumu: int) -> bool:
        """Kesim durumunu kontrol eder"""
        current_time = time.time() * 1000
        
        if testere_durumu != TestereState.CUTTING.value:
            if self.is_cutting:
                self._log_kesim_bitis()
            return False

        if not self.is_cutting:
            self._log_kesim_baslangic()

        if current_time - self.cutting_start_time < BASLANGIC_GECIKMESI:
            kalan_sure = int((BASLANGIC_GECIKMESI - (current_time - self.cutting_start_time)) / 1000)
            if kalan_sure % 5 == 0:
                logger.info(f"Kontrol sisteminin devreye girmesine {kalan_sure} saniye kaldı...")
            return False

        return True

    def hiz_guncelleme_zamani_geldi_mi(self) -> bool:
        """Hız güncelleme zamanının gelip gelmediğini kontrol eder"""
        current_time = time.time()
        return current_time - self.last_update_time >= MIN_SPEED_UPDATE_INTERVAL

    def adjust_speeds(self, processed_data: dict, modbus_client, last_modbus_write_time: float,
                     speed_adjustment_interval: float, prev_current: float) -> Tuple[float, Optional[float]]:
        """Hızları ayarlar"""
        if not self.kesim_durumu_kontrol(processed_data.get('testere_durumu')):
            return last_modbus_write_time, None

        if not self.hiz_guncelleme_zamani_geldi_mi():
            return last_modbus_write_time, None

        try:
            # Mevcut değerleri al
            current_akim = float(processed_data.get('serit_motor_akim_a', 0))
            current_kesme_hizi = float(processed_data.get('serit_kesme_hizi', SPEED_LIMITS['kesme']['min']))
            current_inme_hizi = float(processed_data.get('serit_inme_hizi', SPEED_LIMITS['inme']['min']))
            
            # Yeni inme hızını tahmin et
            new_inme_hizi = self.predict_next_speed(current_akim, current_kesme_hizi, current_inme_hizi)
            
            # İnme hızı değişimini hesapla
            inme_hizi_degisim = new_inme_hizi - current_inme_hizi
            
            # İnme hızı değişim yüzdesini hesapla
            inme_degisim_yuzdesi = self._calculate_speed_change_percentage(inme_hizi_degisim, 'inme')
            
            # Kesme hızı için değişimi hesapla
            kesme_hizi_degisim = self._calculate_speed_change_from_percentage(inme_degisim_yuzdesi, 'kesme')
            
            # Kesme hızı değişimini buffer'a ekle
            self.kesme_hizi_degisim_buffer += kesme_hizi_degisim
            
            # Modbus'a yazma işlemleri
            if new_inme_hizi != current_inme_hizi:
                # İnme hızını yaz
                inme_hizi_is_negative = new_inme_hizi < 0
                reverse_calculate_value(modbus_client, new_inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
                logger.debug(f"Yeni inme hızı: {new_inme_hizi:.2f}")
                
                # Kesme hızı için buffer kontrolü
                if abs(self.kesme_hizi_degisim_buffer) >= 1.0:
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
            
            return last_modbus_write_time, new_inme_hizi
            
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
        logger.info(f"Kontrol sistemi {BASLANGIC_GECIKMESI/1000} saniye sonra devreye girecek...")
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