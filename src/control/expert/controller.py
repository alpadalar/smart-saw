# src/control/expert_adjustment/controller.py
import time
from datetime import datetime
from collections import deque
from core.logger import logger
from core.constants import SPEED_LIMITS
from utils.helpers import (
    reverse_calculate_value,
    get_current_time_ms,
    calculate_elapsed_time_ms,
    format_time
)

# Sabitler
IDEAL_AKIM = 17.0
SAPMA_ESIK = 0.4
MIN_SPEED_UPDATE_INTERVAL = 1.0  # 1 Hz güncelleme hızı
BASLANGIC_GECIKMESI = 15000.0  # 30 saniye başlangıç gecikmesi (ms)
BUFFER_SURESI = 1.0  # 1 saniyelik veri tamponu

class VeriBuffer:
    def __init__(self):
        self.akim_buffer = deque()
        self.sapma_buffer = deque()
        self.son_veri_zamani = None
    
    def veri_ekle(self, akim, sapma):
        current_time = time.time()
        
        if self.son_veri_zamani is None:
            self.son_veri_zamani = current_time
        
        self.akim_buffer.append((current_time, akim))
        self.sapma_buffer.append((current_time, sapma))
        
        # Eski verileri temizle
        while self.akim_buffer and current_time - self.akim_buffer[0][0] > BUFFER_SURESI:
            self.akim_buffer.popleft()
        while self.sapma_buffer and current_time - self.sapma_buffer[0][0] > BUFFER_SURESI:
            self.sapma_buffer.popleft()
    
    def ortalamalari_al(self):
        if not self.akim_buffer or not self.sapma_buffer:
            return None, None
        
        ort_akim = sum(akim for _, akim in self.akim_buffer) / len(self.akim_buffer)
        ort_sapma = sum(sapma for _, sapma in self.sapma_buffer) / len(self.sapma_buffer)
        
        return ort_akim, ort_sapma

class AkimKontrol:
    def __init__(self):
        self.cutting_start_time = None
        self.is_cutting = False
        self.last_update_time = 0
        self.veri_buffer = VeriBuffer()

    def kesim_durumu_kontrol(self, testere_durumu):
        current_time = time.time() * 1000  # milisaniye cinsinden
        
        if testere_durumu != 3:
            if self.is_cutting:
                self._log_kesim_bitis()
            return False

        if not self.is_cutting:
            self._log_kesim_baslangic()

        if current_time - self.cutting_start_time < BASLANGIC_GECIKMESI:
            kalan_sure = int((BASLANGIC_GECIKMESI - (current_time - self.cutting_start_time)) / 1000)
            if kalan_sure % 5 == 0:  # Her 5 saniyede bir bilgi ver
                logger.info(f"Kontrol sisteminin devreye girmesine {kalan_sure} saniye kaldı...")
            return False

        return True

    def hiz_guncelleme_zamani_geldi_mi(self):
        current_time = time.time()
        if current_time - self.last_update_time < MIN_SPEED_UPDATE_INTERVAL:
            return False
        return True

    def inme_hizi_hesapla(self, current_akim, current_sapma, current_inme_hizi):
        self.veri_buffer.veri_ekle(current_akim, current_sapma)
        
        ort_akim, ort_sapma = self.veri_buffer.ortalamalari_al()
        if ort_akim is None or ort_sapma is None:
            return current_inme_hizi
        
        akim_fark = ort_akim - IDEAL_AKIM
        sapma_var = abs(ort_sapma) > SAPMA_ESIK
        
        hiz_degisim_katsayi = 0.0
        
        if akim_fark > 0:  # Akım yüksek
            hiz_degisim_katsayi = -0.5 * akim_fark
            if sapma_var:
                hiz_degisim_katsayi *= 1.0
                logger.warning(f"UYARI: Yüksek akım ({ort_akim:.1f}A) ve şerit sapması ({ort_sapma:.3f}) tespit edildi!")
                
        elif akim_fark < 0:  # Akım düşük
            hiz_degisim_katsayi = -0.5 * akim_fark
            if sapma_var:
                logger.warning(f"UYARI: Düşük akım ({ort_akim:.2f}A) durumunda şerit sapması ({ort_sapma:.3f}) tespit edildi!")
        
        new_inme_hizi = current_inme_hizi + hiz_degisim_katsayi
        new_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(new_inme_hizi, SPEED_LIMITS['inme']['max']))
        
        logger.info(f"Ortalama Akım: {ort_akim:.1f}A (Fark: {akim_fark:+.1f}A)")
        logger.info(f"Ortalama Sapma: {ort_sapma:.3f} ({'Var' if sapma_var else 'Yok'})")
        logger.info(f"İnme Hızı: {current_inme_hizi:.1f} -> {new_inme_hizi:.1f} (Değişim: {hiz_degisim_katsayi:+.2f})")
        logger.info("-" * 60)
        
        return new_inme_hizi

    def _log_kesim_baslangic(self):
        self.cutting_start_time = time.time() * 1000
        self.is_cutting = True
        start_time_str = get_current_time_ms()
        logger.info("\n" + "="*60)
        logger.info("YENİ KESİM BAŞLADI")
        logger.info("-"*60)
        logger.info(f"Başlangıç Zamanı : {start_time_str}")
        logger.info(f"Kontrol sistemi {BASLANGIC_GECIKMESI/1000} saniye sonra devreye girecek...")
        logger.info("="*60 + "\n")

    def _log_kesim_bitis(self):
        if self.cutting_start_time:
            elapsed = calculate_elapsed_time_ms(self.cutting_start_time)
            end_time_str = get_current_time_ms()
            elapsed_str = format_time(elapsed)
            logger.info("\n" + "="*60)
            logger.info("KESİM BİTTİ")
            logger.info("-"*60)
            logger.info(f"Bitiş Zamanı     : {end_time_str}")
            logger.info(f"Toplam Süre      : {elapsed_str}")
            logger.info("="*60 + "\n")
        
        self.is_cutting = False
        self.cutting_start_time = None


# Global controller nesnesi
akim_kontrol = AkimKontrol()

def adjust_speeds(processed_data, modbus_client, last_modbus_write_time, speed_adjustment_interval, prev_current):
    """Expert kontrol için hız ayarlama fonksiyonu"""
    if not akim_kontrol.kesim_durumu_kontrol(processed_data.get('testere_durumu')):
        return last_modbus_write_time, None

    if not akim_kontrol.hiz_guncelleme_zamani_geldi_mi():
        return last_modbus_write_time, None

    try:
        # Mevcut değerleri al
        current_akim = float(processed_data.get('serit_motor_akim_a', IDEAL_AKIM))
        current_sapma = float(processed_data.get('serit_sapmasi', 0))
        current_inme_hizi = float(processed_data.get('serit_inme_hizi', SPEED_LIMITS['inme']['min']))
        
        # Yeni inme hızını hesapla
        new_inme_hizi = akim_kontrol.inme_hizi_hesapla(current_akim, current_sapma, current_inme_hizi)
        
        # Hız sınırlarını uygula
        new_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(new_inme_hizi, SPEED_LIMITS['inme']['max']))
        
        # Modbus'a yaz
        if new_inme_hizi != current_inme_hizi:
            inme_hizi_is_negative = new_inme_hizi < 0
            reverse_calculate_value(modbus_client, new_inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
            logger.debug(f"Yeni inme hızı: {new_inme_hizi:.2f}")
        
        # Son güncelleme zamanını kaydet
        akim_kontrol.last_update_time = time.time()
        
        return last_modbus_write_time, new_inme_hizi
        
    except Exception as e:
        logger.error(f"Expert kontrol hatası: {str(e)}")
        logger.exception("Detaylı hata:")
        return last_modbus_write_time, None