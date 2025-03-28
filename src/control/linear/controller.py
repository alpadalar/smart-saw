# src/control/linear/controller.py
import time
from datetime import datetime
from core.logger import logger
from core.constants import SPEED_LIMITS
from utils.helpers import (
    reverse_calculate_value,
    get_current_time_ms,
    calculate_elapsed_time_ms,
    format_time
)
from .speed_matrix import speed_matrix

class LinearController:
    def __init__(self):
        self.cutting_start_time = None
        self.is_cutting = False
        self.last_update_time = 0
        self.katsayi = 1.0
        
        # Kontrol parametreleri
        self.MIN_SPEED_UPDATE_INTERVAL = 1.0  # 1 Hz
        self.BASLANGIC_GECIKMESI = 0.0  # 30 saniye (ms)
    
    def interpolate_speeds_by_height(self, height):
        """Verilen yükseklik için kesme ve inme hızlarını interpolasyon ile hesaplar"""
        if height >= speed_matrix[0][0]:
            return speed_matrix[0][1], speed_matrix[0][2]
        elif height <= speed_matrix[-1][0]:
            return speed_matrix[-1][1], speed_matrix[-1][2]

        for i in range(len(speed_matrix) - 1):
            high = speed_matrix[i][0]
            low = speed_matrix[i + 1][0]
            if high >= height > low:
                high_speeds = speed_matrix[i][1], speed_matrix[i][2]
                low_speeds = speed_matrix[i + 1][1], speed_matrix[i + 1][2]

                kesme_hizi = ((height - low) / (high - low)) * (high_speeds[0] - low_speeds[0]) + low_speeds[0]
                inme_hizi = ((height - low) / (high - low)) * (high_speeds[1] - low_speeds[1]) + low_speeds[1]
                return kesme_hizi, inme_hizi

        return speed_matrix[-1][1], speed_matrix[-1][2]

    def kesim_durumu_kontrol(self, testere_durumu):
        current_time = time.time() * 1000  # milisaniye cinsinden
        
        if testere_durumu != 3:
            if self.is_cutting:
                self._log_kesim_bitis()
            return False

        if not self.is_cutting:
            self._log_kesim_baslangic()

        if current_time - self.cutting_start_time < self.BASLANGIC_GECIKMESI:
            kalan_sure = int((self.BASLANGIC_GECIKMESI - (current_time - self.cutting_start_time)) / 1000)
            if kalan_sure % 5 == 0:  # Her 5 saniyede bir bilgi ver
                logger.info(f"Kontrol sisteminin devreye girmesine {kalan_sure} saniye kaldı...")
            return False

        return True

    def hiz_guncelleme_zamani_geldi_mi(self):
        current_time = time.time()
        return current_time - self.last_update_time >= self.MIN_SPEED_UPDATE_INTERVAL

    def adjust_speeds(self, processed_data, modbus_client, last_modbus_write_time, speed_adjustment_interval, prev_current):
        if not self.kesim_durumu_kontrol(processed_data.get('testere_durumu')):
            return last_modbus_write_time, None

        if not self.hiz_guncelleme_zamani_geldi_mi():
            return last_modbus_write_time, None

        try:
            # Kafa yüksekliğine göre hızları hesapla
            kafa_yuksekligi_mm = processed_data.get('kafa_yuksekligi_mm', 0)
            serit_kesme_hizi, serit_inme_hizi = self.interpolate_speeds_by_height(kafa_yuksekligi_mm)
            
            logger.info(f"Kafa yüksekliği: {kafa_yuksekligi_mm}mm")
            logger.info(f"İlk hesaplanan hızlar - Kesme: {serit_kesme_hizi:.1f}, İnme: {serit_inme_hizi:.1f}")
            
            # Katsayı ile çarp
            serit_inme_hizi *= self.katsayi
            serit_kesme_hizi *= self.katsayi
            
            logger.info(f"Katsayı ({self.katsayi}) sonrası hızlar - Kesme: {serit_kesme_hizi:.1f}, İnme: {serit_inme_hizi:.1f}")

            # Hız sınırlarını uygula
            new_serit_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(serit_inme_hizi, SPEED_LIMITS['inme']['max']))
            new_serit_kesme_hizi = max(SPEED_LIMITS['kesme']['min'], min(serit_kesme_hizi, SPEED_LIMITS['kesme']['max']))
            
            logger.info(f"Sınırlandırılmış hızlar - Kesme: {new_serit_kesme_hizi:.1f}, İnme: {new_serit_inme_hizi:.1f}")

            # Modbus'a yaz
            try:
                # Önce inme hızını yaz
                logger.info(f"İnme hızı yazılıyor: {new_serit_inme_hizi:.1f}")
                inme_hizi_is_negative = new_serit_inme_hizi < 0
                reverse_calculate_value(modbus_client, new_serit_inme_hizi, 'serit_inme_hizi', inme_hizi_is_negative)
                logger.info("İnme hızı başarıyla yazıldı")
                
                # 110ms bekle
                time.sleep(0.110)
                
                # Sonra kesme hızını yaz
                logger.info(f"Kesme hızı yazılıyor: {new_serit_kesme_hizi:.1f}")
                kesme_hizi_is_negative = new_serit_kesme_hizi < 0
                reverse_calculate_value(modbus_client, new_serit_kesme_hizi, 'serit_kesme_hizi', kesme_hizi_is_negative)
                logger.info("Kesme hızı başarıyla yazıldı")
                
            except Exception as e:
                logger.error(f"Modbus yazma hatası: {str(e)}")
                logger.exception("Detaylı hata:")
                raise
            
            # Son güncelleme zamanını kaydet
            self.last_update_time = time.time()
            
            return last_modbus_write_time, new_serit_inme_hizi
            
        except Exception as e:
            logger.error(f"Linear kontrol hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            return last_modbus_write_time, None

    def _log_kesim_baslangic(self):
        self.cutting_start_time = time.time() * 1000
        self.is_cutting = True
        start_time_str = get_current_time_ms()
        logger.info("\n" + "="*60)
        logger.info("YENİ KESİM BAŞLADI (Linear Kontrol)")
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
            logger.info("KESİM BİTTİ (Linear Kontrol)")
            logger.info("-"*60)
            logger.info(f"Bitiş Zamanı     : {end_time_str}")
            logger.info(f"Toplam Süre      : {elapsed_str}")
            logger.info("="*60 + "\n")
        
        self.is_cutting = False
        self.cutting_start_time = None


# Global controller nesnesi
linear_controller = LinearController()

def adjust_speeds_linear(processed_data, modbus_client, last_modbus_write_time, speed_adjustment_interval, prev_current):
    """Linear kontrol için hız ayarlama fonksiyonu"""
    return linear_controller.adjust_speeds(
        processed_data=processed_data,
        modbus_client=modbus_client,
        last_modbus_write_time=last_modbus_write_time,
        speed_adjustment_interval=speed_adjustment_interval,
        prev_current=prev_current
    )