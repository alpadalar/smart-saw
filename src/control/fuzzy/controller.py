# src/control/fuzzy/controller.py
import time
import sqlite3
import threading
from datetime import datetime
from collections import deque
from core.logger import logger
from core.constants import (
    SPEED_LIMITS,
    TestereState,
    IDEAL_AKIM,
    MIN_SPEED_UPDATE_INTERVAL,
    BUFFER_SIZE,
    BUFFER_DURATION,
    KATSAYI
)
from utils.helpers import (
    reverse_calculate_value,
    get_current_time_ms,
    calculate_elapsed_time_ms,
    format_time
)
from utils.speed.buffer import SpeedBuffer
from utils.delay_calculator import calculate_control_delay
from .membership import FuzzyMembership
from .rules import FuzzyRules

class FuzzyController:
    def __init__(self):
        """Fuzzy kontrol sistemi başlatılır"""
        self.cutting_start_time = None
        self.is_cutting = False
        self.last_update_time = time.time()
        
        # Thread-local storage için
        self.thread_local = threading.local()
        
        # Veritabanı dizinini oluştur
        import os
        os.makedirs('data', exist_ok=True)
        
        # Kontrol parametreleri
        self.MIN_SPEED_UPDATE_INTERVAL = MIN_SPEED_UPDATE_INTERVAL
        self.IDEAL_AKIM = IDEAL_AKIM
        
        # Fuzzy sistem bileşenleri
        self.membership = FuzzyMembership()
        self.rules = FuzzyRules()
        self.speed_buffer = SpeedBuffer()
        
        # Veri tamponları - constants.py'dan alınan boyut
        self.akim_buffer = deque(maxlen=BUFFER_SIZE)
        self.sapma_buffer = deque(maxlen=BUFFER_SIZE)
        self.titresim_buffer = deque(maxlen=BUFFER_SIZE)
        self.last_buffer_update = time.time()
        
        # Kesme hızı değişim buffer'ı
        self.kesme_hizi_degisim_buffer = 0.0
        # İnme hızı değişim buffer'ı
        self.inme_hizi_degisim_buffer = 0.0
    
    def _get_db(self):
        """Thread-safe veritabanı bağlantısı döndürür"""
        if not hasattr(self.thread_local, 'db'):
            try:
                self.thread_local.db = sqlite3.connect('data/fuzzy_control.db')
                cursor = self.thread_local.db.cursor()
                
                # Fuzzy kontrol verilerini saklayacak tablo
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fuzzy_control_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        akim_input REAL,
                        sapma_input REAL,
                        titresim_input REAL,
                        kesme_hizi REAL,
                        inme_hizi REAL,
                        katsayi REAL,
                        fuzzy_output REAL
                    )
                ''')
                self.thread_local.db.commit()
                logger.debug(f"Thread {threading.get_ident()} için yeni veritabanı bağlantısı oluşturuldu")
                
            except Exception as e:
                logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
                return None
                
        return self.thread_local.db

    def _save_control_data(self, akim: float, sapma: float, titresim: float, kesme_hizi: float, inme_hizi: float, katsayi: float, fuzzy_output: float):
        """Kontrol verilerini veritabanına kaydeder"""
        try:
            db = self._get_db()
            if db:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                cursor = db.cursor()
                cursor.execute('''
                    INSERT INTO fuzzy_control_data 
                    (timestamp, akim_input, sapma_input, titresim_input, kesme_hizi, inme_hizi, katsayi, fuzzy_output)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (current_time, akim, sapma, titresim, kesme_hizi, inme_hizi, katsayi, fuzzy_output))
                
                db.commit()
                logger.debug(f"Fuzzy kontrol verisi kaydedildi - Zaman: {current_time}, Çıktı: {fuzzy_output}")
                
        except Exception as e:
            logger.error(f"Veri kaydetme hatası: {str(e)}")

    def _calculate_speed_change_percentage(self, speed_change, speed_type, current_speed):
        """Hız değişiminin yüzdesini hesaplar"""
        if speed_change > 0:
            speed_range = SPEED_LIMITS[speed_type]['max'] - current_speed
        else:
            speed_range = current_speed - SPEED_LIMITS[speed_type]['min']
        return (speed_change / speed_range) * 100

    def _calculate_speed_change_from_percentage(self, percentage, speed_type):
        """Yüzdeye göre hız değişimini hesaplar"""
        speed_range = SPEED_LIMITS[speed_type]['max'] - SPEED_LIMITS[speed_type]['min']
        return (percentage / 100) * speed_range
        
    def _get_max_titresim(self, processed_data):
        """Üç eksendeki titreşim değerlerinin maksimumunu döndürür"""
        x_hz = float(processed_data.get('ivme_olcer_x_hz', 0))
        y_hz = float(processed_data.get('ivme_olcer_y_hz', 0))
        z_hz = float(processed_data.get('ivme_olcer_z_hz', 0))
        return max(x_hz, y_hz, z_hz)
        
    def _update_buffers(self, akim, sapma, titresim):
        """Veri tamponlarını günceller"""
        current_time = time.time()
        
        # Tamponları güncelle
        self.akim_buffer.append((current_time, akim))
        self.sapma_buffer.append((current_time, sapma))
        self.titresim_buffer.append((current_time, titresim))
            
    def _get_buffer_averages(self):
        """Tamponlardaki verilerin ortalamasını alır"""
        if not self.akim_buffer or not self.sapma_buffer or not self.titresim_buffer:
            return None, None, None
            
        akim_avg = sum(akim for _, akim in self.akim_buffer) / len(self.akim_buffer)
        sapma_avg = sum(sapma for _, sapma in self.sapma_buffer) / len(self.sapma_buffer)
        titresim_avg = sum(titresim for _, titresim in self.titresim_buffer) / len(self.titresim_buffer)
        
        return akim_avg, sapma_avg, titresim_avg



    def kesim_durumu_kontrol(self, testere_durumu, modbus_client=None):
        """Kesim durumunu kontrol eder ve loglama yapar"""
        try:
            current_time = time.time() * 1000
            
            # Kesim durumu değişikliğini kontrol et
            if testere_durumu != TestereState.KESIM_YAPILIYOR.value:
                if self.is_cutting:
                    self._log_kesim_bitis()
                    self.is_cutting = False
                    self.cutting_start_time = None
                return False

            # Kesim başlangıcını kontrol et
            if not self.is_cutting:
                self._log_kesim_baslangic()
                self.is_cutting = True
                self.cutting_start_time = current_time
                
                # İnme hızını register'dan okuyarak dinamik bekleme süresini hesapla
                # Fuzzy için 20mm hedef mesafe kullan
                self.initial_delay = calculate_control_delay(modbus_client, target_distance_mm=20.0)
                logger.info(f"Fuzzy - Register'dan hesaplanan bekleme süresi: {self.initial_delay/1000:.1f} saniye")

            # Başlangıç gecikmesi kontrolü
            if hasattr(self, 'initial_delay') and self.initial_delay > 0:
                if current_time - self.cutting_start_time < self.initial_delay:
                    kalan_sure = int((self.initial_delay - (current_time - self.cutting_start_time)) / 1000)
                    if kalan_sure % 5 == 0:
                        logger.info(f"Fuzzy kontrol sisteminin devreye girmesine {kalan_sure} saniye kaldı...")
                    return False

            return True
            
        except Exception as e:
            logger.error(f"Kesim durumu kontrol hatası: {str(e)}")
            return False

    def hiz_guncelleme_zamani_geldi_mi(self):
        current_time = time.time()
        return current_time - self.last_update_time >= self.MIN_SPEED_UPDATE_INTERVAL

    def calculate_fuzzy_output(self, current_akim, current_sapma, current_titresim, current_kesme_hizi, current_inme_hizi):
        """Fuzzy çıkış değerini hesaplar ve kaydeder"""
        try:
            # Fuzzy çıkış değerini hesapla
            fuzzy_output = self.rules.evaluate(current_akim, current_sapma, current_titresim)
            
            # Verileri kaydet
            self._save_control_data(
                akim=current_akim,
                sapma=current_sapma,
                titresim=current_titresim,
                kesme_hizi=current_kesme_hizi,
                inme_hizi=current_inme_hizi,
                katsayi=KATSAYI,
                fuzzy_output=fuzzy_output
            )
            
            return fuzzy_output
            
        except Exception as e:
            logger.error(f"Fuzzy çıkış hesaplama hatası: {str(e)}")
            return 0.0

    def adjust_speeds(self, processed_data, modbus_client, last_modbus_write_time, 
                     speed_adjustment_interval, prev_current):
        """Hızları ayarlar ve fuzzy çıktısını döndürür"""
        # Kesim durumu kontrolü
        testere_durumu = int(processed_data.get('testere_durumu', 0))
        logger.debug(f"Testere durumu: {testere_durumu}")
        
        # Son işlenen veriyi güncelle
        self.last_processed_data = processed_data
        
        if not self.kesim_durumu_kontrol(testere_durumu, modbus_client):
            logger.debug("Kesim durumu uygun değil veya başlangıç gecikmesi devam ediyor")
            return last_modbus_write_time, None

        # Güncelleme zamanı kontrolü
        if not self.hiz_guncelleme_zamani_geldi_mi():
            logger.debug("Hız güncelleme zamanı gelmedi")
            return last_modbus_write_time, None

        try:
            # Mevcut hızları al
            current_kesme_hizi = float(processed_data.get('serit_kesme_hizi', SPEED_LIMITS['kesme']['min']))
            current_inme_hizi = float(processed_data.get('serit_inme_hizi', SPEED_LIMITS['inme']['min']))
            
            # Akım, sapma ve titreşim değerlerini al
            current_akim = float(processed_data.get('serit_motor_akim_a', self.IDEAL_AKIM))
            current_sapma = float(processed_data.get('serit_sapmasi', 0)) / 5
            current_titresim = self._get_max_titresim(processed_data)
            
            # Tamponları güncelle
            self._update_buffers(current_akim, current_sapma, current_titresim)
            
            # Ortalama değerleri al
            avg_akim, avg_sapma, avg_titresim = self._get_buffer_averages()
            if avg_akim is None or avg_sapma is None or avg_titresim is None:
                logger.warning("Yeterli veri yok, ham değerler kullanılıyor")
                avg_akim, avg_sapma, avg_titresim = current_akim, current_sapma, current_titresim
                
            logger.debug(f"Ortalama akım: {avg_akim:.2f}A, Ortalama sapma: {avg_sapma:.2f}mm, Ortalama titreşim: {avg_titresim:.2f}Hz")
            
            # Fuzzy çıktısını hesapla (değişim miktarı)
            fuzzy_output = self.calculate_fuzzy_output(avg_akim, avg_sapma, avg_titresim, current_kesme_hizi, current_inme_hizi)
            fuzzy_output = fuzzy_output * KATSAYI
            logger.debug(f"Fuzzy değişim çıktısı: {fuzzy_output}")
            
            # İnme hızı için değişimi hesapla
            new_inme_hizi = current_inme_hizi + fuzzy_output  # Direkt değişimi ekle
            
            # İnme hızı sınırlarını uygula
            new_inme_hizi = max(SPEED_LIMITS['inme']['min'], min(new_inme_hizi, SPEED_LIMITS['inme']['max']))
            logger.debug(f"Mevcut inme hızı: {current_inme_hizi:.2f}, Yeni inme hızı: {new_inme_hizi:.2f}")
            
            # İnme hızı değişim yüzdesini hesapla
            inme_hizi_degisim = new_inme_hizi - current_inme_hizi
            inme_degisim_yuzdesi = self._calculate_speed_change_percentage(inme_hizi_degisim, 'inme', current_inme_hizi)
            logger.debug(f"İnme hızı değişim yüzdesi: %{inme_degisim_yuzdesi:.2f}")
            
            # İnme hızı değişimini buffer'a ekle
            self.inme_hizi_degisim_buffer += inme_hizi_degisim
            logger.debug(f"İnme hızı değişim buffer'ı: {self.inme_hizi_degisim_buffer:.2f}")
            
            # Kesme hızı için değişimi hesapla
            current_kesme_hizi = float(processed_data.get('serit_kesme_hizi', SPEED_LIMITS['kesme']['min']))
            
            # Fuzzy çıktısının işaretine göre referans aralığı belirle
            if fuzzy_output < 0:
                # Negatif değişim: mevcut hız ile minimum hız arası
                speed_range = current_kesme_hizi - SPEED_LIMITS['kesme']['min']
                kesme_hizi_degisim = -(speed_range * abs(inme_degisim_yuzdesi) / 100)
                logger.debug(f"Negatif değişim - Aralık: {speed_range:.2f}, Değişim: {kesme_hizi_degisim:.2f}")
            else:
                # Pozitif değişim: mevcut hız ile maksimum hız arası
                speed_range = SPEED_LIMITS['kesme']['max'] - current_kesme_hizi
                kesme_hizi_degisim = (speed_range * abs(inme_degisim_yuzdesi) / 100)
                logger.debug(f"Pozitif değişim - Aralık: {speed_range:.2f}, Değişim: {kesme_hizi_degisim:.2f}")
            
            # Kesme hızı değişimini buffer'a ekle
            self.kesme_hizi_degisim_buffer += kesme_hizi_degisim
            logger.debug(f"Kesme hızı değişim buffer'ı: {self.kesme_hizi_degisim_buffer:.2f}")
            
            # Modbus'a yazma işlemleri
            # İnme hızı için buffer kontrolü - BUFFER BYPASS EDİLDİ
            # if abs(self.inme_hizi_degisim_buffer) >= 1.0:
            #     new_inme_hizi = current_inme_hizi + self.inme_hizi_degisim_buffer
            #     new_inme_hizi = max(SPEED_LIMITS['inme']['min'], 
            #                        min(new_inme_hizi, SPEED_LIMITS['inme']['max']))
            #     
            #     # İnme hızını yaz
            #     inme_hizi_is_negative = new_inme_hizi < 0
            #     reverse_calculate_value(modbus_client, int(new_inme_hizi), 'serit_inme_hizi', inme_hizi_is_negative)
            #     logger.debug(f"Yeni inme hızı değeri Modbus'a yazıldı: {new_inme_hizi:.2f}")
            #     
            #     # Buffer'ı sıfırla
            #     self.inme_hizi_degisim_buffer = 0.0
            
            # BUFFER BYPASS: Direkt hesaplanan hızı gönder (xy.ab formatında)
            if abs(inme_hizi_degisim) > 0.01:  # Minimum değişim kontrolü
                # Hızı 2 ondalık basamağa yuvarla
                new_inme_hizi_rounded = round(new_inme_hizi, 2)
                new_inme_hizi_rounded = max(SPEED_LIMITS['inme']['min'], 
                                           min(new_inme_hizi_rounded, SPEED_LIMITS['inme']['max']))
                
                # İnme hızını direkt yaz (buffer olmadan)
                inme_hizi_is_negative = new_inme_hizi_rounded < 0
                reverse_calculate_value(modbus_client, new_inme_hizi_rounded, 'serit_inme_hizi', inme_hizi_is_negative)
                logger.debug(f"BUFFER BYPASS: İnme hızı direkt gönderildi: {new_inme_hizi_rounded:.2f}")
                
                # Buffer'ı sıfırla (artık kullanılmıyor ama temizlik için)
                self.inme_hizi_degisim_buffer = 0.0
            
            # Kesme hızı için buffer kontrolü
            if abs(self.kesme_hizi_degisim_buffer) >= 0.9:
                new_kesme_hizi = current_kesme_hizi + self.kesme_hizi_degisim_buffer
                
                # Sınırları uygula
                new_kesme_hizi = max(SPEED_LIMITS['kesme']['min'], min(new_kesme_hizi, SPEED_LIMITS['kesme']['max']))
                
                # Kesme hızını yaz
                kesme_hizi_is_negative = new_kesme_hizi < 0
                reverse_calculate_value(modbus_client, int(new_kesme_hizi), 'serit_kesme_hizi', kesme_hizi_is_negative)
                logger.debug(f"Yeni kesme hızı değeri Modbus'a yazıldı: {new_kesme_hizi:.2f} (Buffer: {self.kesme_hizi_degisim_buffer:+.2f})")
                
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
        return state in [TestereState.KESIM_YAPILIYOR.value, TestereState.SERIT_MOTOR_CALISIYOR.value]

    def _log_kesim_baslangic(self):
        self.cutting_start_time = time.time() * 1000
        self.is_cutting = True
        start_time_str = get_current_time_ms()
        logger.info("\n" + "="*60)
        logger.info("YENİ KESİM BAŞLADI (Fuzzy Kontrol)")
        logger.info("-"*60)
        logger.info(f"Başlangıç Zamanı : {start_time_str}")
        logger.info("Kontrol sistemi başlangıç gecikmesi sonrası devreye girecek...")
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
        
        # Delay calculator cache'ini sıfırla - bir sonraki kesim için hazırlık
        from utils.delay_calculator import reset_delay_cache
        reset_delay_cache()
        logger.info("🔄 Delay calculator cache'i sıfırlandı - bir sonraki kesim için hazırlık")

    def __del__(self):
        """Yıkıcı metod - tüm veritabanı bağlantılarını kapatır"""
        if hasattr(self.thread_local, 'db'):
            try:
                self.thread_local.db.close()
            except Exception:
                pass

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

def fuzzy_output(cikis_sim, current_akim, current_sapma):
    """Eski fuzzy_output fonksiyonu için uyumluluk katmanı"""
    return _fuzzy_controller.calculate_fuzzy_output(current_akim, current_sapma, 0, 0, 0)