# src/control/fuzzy/controller.py
import time
from datetime import datetime
from core.logger import logger
from core.constants import SPEED_LIMITS, TestereState
from utils.helpers import (
    reverse_calculate_value,
    get_current_time_ms,
    calculate_elapsed_time_ms,
    format_time
)
from utils.speed.buffer import SpeedBuffer
from .membership import FuzzyMembership
from .rules import FuzzyRules

class FuzzyController:
    def __init__(self):
        self.cutting_start_time = None
        self.is_cutting = False
        self.last_update_time = time.time()
        
        # Kontrol parametreleri
        self.MIN_SPEED_UPDATE_INTERVAL = 1.0  # 1 Hz
        self.BASLANGIC_GECIKMESI = 15000.0  # 15 saniye (ms)
        self.IDEAL_AKIM = 17.0
        
        # Fuzzy sistem bileşenleri
        self.membership = FuzzyMembership()
        self.rules = FuzzyRules()
        self.speed_buffer = SpeedBuffer()
        
        # Kesme hızı değişim buffer'ı
        self.kesme_hizi_degisim_buffer = 0.0
    
    def _calculate_speed_change_percentage(self, speed_change, speed_type):
        """Hız değişiminin yüzdesini hesaplar"""
        speed_range = SPEED_LIMITS[speed_type]['max'] - SPEED_LIMITS[speed_type]['min']
        if speed_range == 0:
            return 0
        return (speed_change / speed_range) * 100

    def _calculate_speed_change_from_percentage(self, percentage, speed_type):
        """Yüzdeye göre hız değişimini hesaplar"""
        speed_range = SPEED_LIMITS[speed_type]['max'] - SPEED_LIMITS[speed_type]['min']
        return (percentage / 100) * speed_range

    def kesim_durumu_kontrol(self, testere_durumu):
        current_time = time.time() * 1000
        
        if testere_durumu != 3:
            if self.is_cutting:
                self._log_kesim_bitis()
            return False

        if not self.is_cutting:
            self._log_kesim_baslangic()

        if current_time - self.cutting_start_time < self.BASLANGIC_GECIKMESI:
            kalan_sure = int((self.BASLANGIC_GECIKMESI - (current_time - self.cutting_start_time)) / 1000)
            if kalan_sure % 5 == 0:
                logger.info(f"Kontrol sisteminin devreye girmesine {kalan_sure} saniye kaldı...")
            return False

        return True

    def hiz_guncelleme_zamani_geldi_mi(self):
        current_time = time.time()
        return current_time - self.last_update_time >= self.MIN_SPEED_UPDATE_INTERVAL

    def calculate_fuzzy_output(self, current_akim, akim_degisim):
        """Fuzzy çıkış değerini hesaplar"""
        return self.rules.evaluate(current_akim, akim_degisim)

    def adjust_speeds(self, processed_data, modbus_client, last_modbus_write_time, 
                     speed_adjustment_interval, prev_current):
        """Hızları ayarlar ve fuzzy çıktısını döndürür"""
        # Kesim durumu kontrolü
        testere_durumu = processed_data.get('testere_durumu')
        logger.debug(f"Testere durumu: {testere_durumu}")
        
        if not self.kesim_durumu_kontrol(testere_durumu):
            logger.debug("Kesim durumu uygun değil")
            return last_modbus_write_time, None

        # Güncelleme zamanı kontrolü
        if not self.hiz_guncelleme_zamani_geldi_mi():
            logger.debug("Hız güncelleme zamanı gelmedi")
            return last_modbus_write_time, None

        try:
            # Akım ve sapma değerlerini al
            current_akim = float(processed_data.get('serit_motor_akim_a', self.IDEAL_AKIM))
            current_sapma = float(processed_data.get('serit_sapmasi', 0))
            logger.debug(f"Mevcut akım: {current_akim:.2f}A, Sapma: {current_sapma:.2f}mm")
            
            # Akım değişimini hesapla
            akim_degisim = current_akim - prev_current if prev_current is not None else 0
            logger.debug(f"Akım değişimi: {akim_degisim:.2f}A")
            
            # Fuzzy çıktısını hesapla
            fuzzy_output = self.calculate_fuzzy_output(current_akim, akim_degisim)
            logger.debug(f"Fuzzy çıktısı: {fuzzy_output}")
            
            # İnme hızı için limit kontrolü
            current_inme_hizi = float(processed_data.get('serit_inme_hizi', SPEED_LIMITS['inme']['min']))
            new_inme_hizi = current_inme_hizi + fuzzy_output
            new_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(new_inme_hizi, SPEED_LIMITS['inme']['max']))
            inme_hizi_degisim = new_inme_hizi - current_inme_hizi
            logger.debug(f"Mevcut inme hızı: {current_inme_hizi:.2f}, Yeni inme hızı: {new_inme_hizi:.2f}")
            
            # İnme hızı değişim yüzdesini hesapla
            inme_degisim_yuzdesi = self._calculate_speed_change_percentage(inme_hizi_degisim, 'inme')
            logger.debug(f"İnme hızı değişim yüzdesi: %{inme_degisim_yuzdesi:.2f}")
            
            # Kesme hızı için değişimi hesapla
            kesme_hizi_degisim = self._calculate_speed_change_from_percentage(inme_degisim_yuzdesi, 'kesme')
            logger.debug(f"Hesaplanan kesme hızı değişimi: {kesme_hizi_degisim:.2f}")
            
            # Kesme hızı değişimini buffer'a ekle
            self.kesme_hizi_degisim_buffer += kesme_hizi_degisim
            logger.debug(f"Kesme hızı değişim buffer'ı: {self.kesme_hizi_degisim_buffer:.2f}")
            
            # Modbus'a yazma işlemleri
            if new_inme_hizi != current_inme_hizi:
                # İnme hızını yaz
                inme_hizi_is_negative = new_inme_hizi < 0
                reverse_calculate_value(modbus_client, new_inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
                logger.debug("Yeni inme hızı değeri Modbus'a yazıldı")
                
                # Kesme hızı için buffer kontrolü
                if abs(self.kesme_hizi_degisim_buffer) >= 1.0:
                    current_kesme_hizi = float(processed_data.get('serit_kesme_hizi', SPEED_LIMITS['kesme']['min']))
                    new_kesme_hizi = current_kesme_hizi + self.kesme_hizi_degisim_buffer
                    new_kesme_hizi = max(SPEED_LIMITS['kesme']['min'], min(new_kesme_hizi, SPEED_LIMITS['kesme']['max']))
                    
                    # Kesme hızını yaz
                    kesme_hizi_is_negative = new_kesme_hizi < 0
                    reverse_calculate_value(modbus_client, new_kesme_hizi, 'serit_kesme_hizi', kesme_hizi_is_negative)
                    logger.debug(f"Yeni kesme hızı değeri Modbus'a yazıldı: {new_kesme_hizi:.2f}")
                    
                    # Buffer'ı sıfırla
                    self.kesme_hizi_degisim_buffer = 0.0
            
            # Son güncelleme zamanını kaydet
            self.last_update_time = time.time()
            
            # Fuzzy çıktısını döndür
            return last_modbus_write_time, fuzzy_output
            
        except Exception as e:
            logger.error(f"Fuzzy kontrol hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            return last_modbus_write_time, None

    def _check_cutting_state(self, state):
        """Kesim durumunu kontrol eder"""
        return state in [TestereState.CUTTING.value, TestereState.STARTING.value]

    def _log_kesim_baslangic(self):
        self.cutting_start_time = time.time() * 1000
        self.is_cutting = True
        start_time_str = get_current_time_ms()
        logger.info("\n" + "="*60)
        logger.info("YENİ KESİM BAŞLADI (Fuzzy Kontrol)")
        logger.info("-"*60)
        logger.info(f"Başlangıç Zamanı : {start_time_str}")
        logger.info(f"Kontrol sistemi {self.BASLANGIC_GECIKMESI/1000} saniye sonra devreye girecek...")
        logger.info("="*60 + "\n")

    def _log_kesim_bitis(self):
        if self.cutting_start_time:
            elapsed = calculate_elapsed_time_ms(self.cutting_start_time)
            end_time_str = get_current_time_ms()
            elapsed_str = format_time(elapsed)
            logger.info("\n" + "="*60)
            logger.info("KESİM BİTTİ (Fuzzy Kontrol)")
            logger.info("-"*60)
            logger.info(f"Bitiş Zamanı     : {end_time_str}")
            logger.info(f"Toplam Süre      : {elapsed_str}")
            logger.info("="*60 + "\n")
        
        self.is_cutting = False
        self.cutting_start_time = None

# Singleton controller nesnesi
_fuzzy_controller = FuzzyController()

def adjust_speeds_fuzzy(processed_data, modbus_client, last_modbus_write_time, speed_adjustment_interval, prev_current):
    """Fuzzy kontrol için hız ayarlama fonksiyonu"""
    return _fuzzy_controller.adjust_speeds(
        processed_data=processed_data,
        modbus_client=modbus_client,
        last_modbus_write_time=last_modbus_write_time,
        speed_adjustment_interval=speed_adjustment_interval,
        prev_current=prev_current
    )

def fuzzy_output(cikis_sim, current_akim, akim_degisim):
    """Eski fuzzy_output fonksiyonu için uyumluluk katmanı"""
    return _fuzzy_controller.calculate_fuzzy_output(current_akim, akim_degisim)