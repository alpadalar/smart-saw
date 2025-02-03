# src/control/fuzzy/controller.py
import time
import numpy as np
import skfuzzy as fuzz
from datetime import datetime
from core.logger import logger
from core.constants import SPEED_LIMITS, TestereState
from utils.helpers import (
    reverse_calculate_value,
    get_current_time_ms,
    calculate_elapsed_time_ms,
    format_time
)

class FuzzyController:
    def __init__(self):
        self.cutting_start_time = None
        self.is_cutting = False
        self.last_update_time = time.time()
        
        # Kontrol parametreleri
        self.MIN_SPEED_UPDATE_INTERVAL = 1.0  # 1 Hz
        self.BASLANGIC_GECIKMESI = 15000.0  # 15 saniye (ms)
        self.IDEAL_AKIM = 17.0
        
        # Fuzzy sistem kurulumu
        self.setup_fuzzy_system()
        
        self.membership = FuzzyMembership()
        self.rules = FuzzyRules()
        self.speed_buffer = SpeedBuffer()  # Yeni eklenen
        
    def setup_fuzzy_system(self):
        """Fuzzy kontrol sistemini kurar"""
        # Evrensel kümeler
        self.akim = np.arange(0, 31, 1)
        self.akim_degisim = np.arange(-10, 11, 1)
        self.hiz_degisim = np.arange(-10, 11, 0.1)
        
        # Akım üyelik fonksiyonları
        self.akim_cok_dusuk = fuzz.trimf(self.akim, [0, 0, 10])
        self.akim_dusuk = fuzz.trimf(self.akim, [5, 12, 16])
        self.akim_normal = fuzz.trimf(self.akim, [14, 17, 20])
        self.akim_yuksek = fuzz.trimf(self.akim, [18, 22, 26])
        self.akim_cok_yuksek = fuzz.trimf(self.akim, [24, 30, 30])
        
        # Akım değişim üyelik fonksiyonları
        self.degisim_negatif = fuzz.trimf(self.akim_degisim, [-10, -5, 0])
        self.degisim_sifir = fuzz.trimf(self.akim_degisim, [-2, 0, 2])
        self.degisim_pozitif = fuzz.trimf(self.akim_degisim, [0, 5, 10])
        
        # Hız değişim üyelik fonksiyonları
        self.hiz_azalt_cok = fuzz.trimf(self.hiz_degisim, [-10, -10, -5])
        self.hiz_azalt = fuzz.trimf(self.hiz_degisim, [-7, -4, -1])
        self.hiz_sabit = fuzz.trimf(self.hiz_degisim, [-2, 0, 2])
        self.hiz_artir = fuzz.trimf(self.hiz_degisim, [1, 4, 7])
        self.hiz_artir_cok = fuzz.trimf(self.hiz_degisim, [5, 10, 10])

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
        # Akım üyelik dereceleri
        akim_level_cd = fuzz.interp_membership(self.akim, self.akim_cok_dusuk, current_akim)
        akim_level_d = fuzz.interp_membership(self.akim, self.akim_dusuk, current_akim)
        akim_level_n = fuzz.interp_membership(self.akim, self.akim_normal, current_akim)
        akim_level_y = fuzz.interp_membership(self.akim, self.akim_yuksek, current_akim)
        akim_level_cy = fuzz.interp_membership(self.akim, self.akim_cok_yuksek, current_akim)
        
        # Akım değişim üyelik dereceleri
        degisim_level_n = fuzz.interp_membership(self.akim_degisim, self.degisim_negatif, akim_degisim)
        degisim_level_s = fuzz.interp_membership(self.akim_degisim, self.degisim_sifir, akim_degisim)
        degisim_level_p = fuzz.interp_membership(self.akim_degisim, self.degisim_pozitif, akim_degisim)
        
        # Kural aktivasyonları
        rule1 = np.fmin(akim_level_cd, self.hiz_artir_cok)
        rule2 = np.fmin(akim_level_d, self.hiz_artir)
        rule3 = np.fmin(akim_level_n, self.hiz_sabit)
        rule4 = np.fmin(akim_level_y, self.hiz_azalt)
        rule5 = np.fmin(akim_level_cy, self.hiz_azalt_cok)
        
        # Değişim kuralları
        rule6 = np.fmin(degisim_level_n, self.hiz_artir)
        rule7 = np.fmin(degisim_level_s, self.hiz_sabit)
        rule8 = np.fmin(degisim_level_p, self.hiz_azalt)
        
        # Kural birleştirme
        aggregated = np.fmax.reduce([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
        
        # Durulaştırma
        hiz_degisimi = fuzz.defuzz(self.hiz_degisim, aggregated, 'centroid')
        
        return hiz_degisimi

    def adjust_speeds(self, processed_data, modbus_client, last_modbus_write_time, 
                     speed_adjustment_interval, prev_current):
        # Kesim durumu kontrolü
        if not self._check_cutting_state(processed_data.get('testere_durumu')):
            return last_modbus_write_time, None

        # Güncelleme zamanı kontrolü
        current_time = time.time()
        if current_time - self.last_update_time < speed_adjustment_interval:
            return last_modbus_write_time, None

        # Akım ve sapma değerlerini al
        current_akim = processed_data.get('serit_motor_akim_a', self.IDEAL_AKIM)
        current_sapma = processed_data.get('serit_sapmasi', 0)
        
        # Fuzzy çıktısını hesapla
        inme_hizi_degisimi = self.rules.evaluate(current_akim, current_sapma)
        
        # İnme hızı için limit kontrolü
        current_inme_hizi = processed_data.get('serit_inme_hizi', SPEED_LIMITS['inme']['min'])
        new_inme_hizi = current_inme_hizi + inme_hizi_degisimi
        new_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(SPEED_LIMITS['inme']['max'], new_inme_hizi))
        
        # İnme hızı değişim oranını hesapla
        inme_hizi_range = SPEED_LIMITS['inme']['max'] - SPEED_LIMITS['inme']['min']
        change_percentage = (inme_hizi_degisimi / inme_hizi_range) * 100
        
        # Kesme hızı için orantılı değişimi hesapla
        kesme_hizi_range = SPEED_LIMITS['kesme']['max'] - SPEED_LIMITS['kesme']['min']
        kesme_hizi_degisimi = (kesme_hizi_range * change_percentage) / 100
        
        # Kesme hızı değişimini buffer'a ekle
        self.speed_buffer.add_to_buffer(0, kesme_hizi_degisimi)  # İlk parametre kesme hızı için
        
        # Modbus'a yazma işlemleri
        if new_inme_hizi != current_inme_hizi:
            inme_hizi_is_negative = new_inme_hizi < 0
            reverse_calculate_value(modbus_client, new_inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
        
        # Buffer'dan kesme hızı değişimini kontrol et ve gerekirse uygula
        if self.speed_buffer.should_adjust():
            adjustment = self.speed_buffer.get_and_clear()
            current_kesme_hizi = processed_data.get('serit_kesme_hizi', SPEED_LIMITS['kesme']['min'])
            new_kesme_hizi = current_kesme_hizi + adjustment.kesme_hizi
            new_kesme_hizi = max(SPEED_LIMITS['kesme']['min'], min(SPEED_LIMITS['kesme']['max'], new_kesme_hizi))
            
            if new_kesme_hizi != current_kesme_hizi:
                reverse_calculate_value(modbus_client, new_kesme_hizi, 'serit_kesme_hizi', False)
        
        self.last_update_time = current_time
        return current_time, inme_hizi_degisimi

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


# Global controller nesnesi
fuzzy_controller = FuzzyController()

def adjust_speeds_fuzzy(processed_data, modbus_client, last_modbus_write_time, speed_adjustment_interval, prev_current):
    return fuzzy_controller.adjust_speeds(processed_data, modbus_client, last_modbus_write_time,
                                       speed_adjustment_interval, prev_current)

def fuzzy_output(cikis_sim, current_akim, akim_degisim):
    """Eski fuzzy_output fonksiyonu için uyumluluk katmanı"""
    return fuzzy_controller.calculate_fuzzy_output(current_akim, akim_degisim)