# src/main.py
import os
import signal
import shutil
import sys
import threading
import time
from datetime import datetime
from typing import Optional, Dict

# Ensure '/src' is on sys.path for absolute imports like `from core ...`
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from core import (
    logger,
    setup_logger,
    load_config,
    Config,
    ControllerError,
    ModbusError
)
from control import (
    ControllerType,
    get_controller_factory,
    ControllerFactory
)
from hardware import ModbusClient
from data import (
    DataProcessor,
    DataStorage,
    DataMapper
)
from data.cutting_tracker import get_cutting_tracker
from models import ProcessedData, SystemState

from control import ControllerFactory
from gui.pyside_app import SimpleGUI

from core.constants import TestereState

from thingsboard.sender import create_sender_from_env

from core.camera import CameraModule


class SmartSaw:
    def __init__(self):
        """Smart Saw başlatılır"""
        # Konfigürasyon yükleme
        self.config = load_config()
        
        # Logger'ı başlat
        setup_logger(self.config.logging)
        logger.info("Smart Saw başlatılıyor...")
        

        # Recordings klasörünü temizle (thread-safe)
        self._cleanup_old_recordings()
        
        # KAMERANIN YUKARI CIKARKEN DUZENLENECEK
        # Kesim takibi için değişkenler
        self.current_kesim_id = -1  # Başlangıçta kesim yok
        self.previous_testere_durumu = None
        self.is_recording_upward = False  # Yukarı çıkış kaydı durumu
        

        
        # Modbus istemcisi
        self.modbus_client = ModbusClient(
            host='192.168.1.147',
            port=502
        )
        
        # Veri depolama ve işleme
        self.data_storage = DataStorage(self.config)
        self.data_mapper = DataMapper()
        self.data_processor = DataProcessor()
        
        # Kesim takipçisi
        self.cutting_tracker = get_cutting_tracker()
        
        # Kontrol sistemi
        self.controller_factory = ControllerFactory(modbus_client=self.modbus_client)
        # Başlangıçta kontrol sistemini kapalı olarak başlat
        self.controller_factory.set_controller(None)
        
        # GUI - controller factory'yi aktarıyoruz
        self.gui = SimpleGUI(controller_factory=self.controller_factory)

        # --- ThingsBoard entegrasyonu (HTTP) ---
        self.tb = None
        self.tb_enabled = False
        self._tb_last_sent_ms = 0
        self._tb_period_ms = 1000  # ms; 1000=1 saniye. Gerekirse 200-500 ms yap.
        self._tb_field_map = None  
        self._tb_prefix = None  

        try:
            # ThingsBoard sender'ı oluştur
            self.tb = create_sender_from_env()
            if self.tb and self.tb.access_token:
                self.tb_enabled = True
                logger.info(f"ThingsBoard sender aktif: {self.tb.base_url}")
            else:
                logger.warning("ThingsBoard sender pasif: TB_TOKEN boş veya geçersiz.")
        except Exception as e:
            logger.error(f"ThingsBoard sender başlatılamadı: {e}")
            self.tb = None
            self.tb_enabled = False
        
        # Kontrol ve veri döngüleri
        self.control_loop = None
        self.data_loop = None
        
        # Thread güvenliği için lock
        self.lock = threading.Lock()
        
        # Durum değişkenleri
        self.is_running = False  # Thread'ler start() metodunda başlatılacak
        self.last_modbus_write_time = 0
        self.prev_current = 0
        self.last_processed_data = None
        
        # Başlatma (sadece kurulum, thread'ler henüz başlamaz)
        self._setup_database()
        self._setup_modbus()
        # Thread'leri oluştur ama başlatma - start() metodunda başlatılacak
        self.control_loop = None
        self.data_loop = None

        # Kamera/detection/vision/wear: yukarı çıkış başlayınca tetiklenecek
        try:
            # Tek kamera module instance kullan
            self.camera_module = CameraModule()
            self.vision_service = None
            self.wear_calculator = None
            logger.info("Kamera modülü başlatıldı. Detection ve vision servisleri şerit yukarı çıkarken başlatılacak.")
        except Exception as e:
            logger.error(f"Kamera modülü başlatılamadı: {e}")


        logger.info("Başlatma tamamlandı")
    
    def _cleanup_old_recordings(self, max_recordings: int = 4):
        """
        Recordings klasöründeki eski kayıtları temizler.
        En yeni max_recordings kadar klasör kalır, gerisi silinir.
        Thread-safe olarak çalışır.
        """
        try:
            recordings_dir = os.path.join(os.getcwd(), "recordings")
            
            # Recordings klasörü yoksa oluştur
            if not os.path.exists(recordings_dir):
                os.makedirs(recordings_dir)
                logger.info("Recordings klasörü oluşturuldu.")
                return
            
            # Tüm recording klasörlerini listele
            recording_folders = []
            for item in os.listdir(recordings_dir):
                item_path = os.path.join(recordings_dir, item)
                if os.path.isdir(item_path):
                    # Klasör adının tarih formatında olup olmadığını kontrol et (YYYYMMDD-HHMMSS)
                    if len(item) == 15 and item[8] == '-':
                        try:
                            # Tarih formatını kontrol et
                            datetime.strptime(item, '%Y%m%d-%H%M%S')
                            recording_folders.append(item)
                        except ValueError:
                            # Geçersiz tarih formatı, bu klasörü atla
                            continue
            
            # Klasörleri tarihe göre sırala (en yeni önce)
            recording_folders.sort(reverse=True)
            
            logger.info(f"Recordings klasöründe {len(recording_folders)} kayıt bulundu.")
            
            # Eğer max_recordings'den fazla klasör varsa, eski olanları sil
            if len(recording_folders) > max_recordings:
                folders_to_delete = recording_folders[max_recordings:]
                deleted_count = 0
                
                for folder in folders_to_delete:
                    folder_path = os.path.join(recordings_dir, folder)
                    try:
                        # Klasörü ve içindeki tüm dosyaları sil
                        shutil.rmtree(folder_path)
                        deleted_count += 1
                        logger.info(f"Eski recording klasörü silindi: {folder}")
                    except Exception as e:
                        logger.error(f"Klasör silme hatası ({folder}): {e}")
                
                logger.info(f"Toplam {deleted_count} eski recording klasörü silindi. {max_recordings} yeni klasör korundu.")
            else:
                logger.info(f"Recordings klasörü temizliği gerekmiyor. {len(recording_folders)} klasör mevcut (limit: {max_recordings}).")
                
        except Exception as e:
            logger.error(f"Recordings temizleme hatası: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
    def _on_wear_update(self, wear_percentage: float):
        """Callback for wear percentage updates - sends to GUI."""
        try:
            if hasattr(self, 'gui') and self.gui:
                # Update the wear percentage label in the camera page
                if hasattr(self.gui, '_camera_page') and self.gui._camera_page:
                    self.gui._camera_page.update_wear_percentage(wear_percentage)
        except Exception as e:
            logger.error(f"Wear update callback hatası: {e}")
        
    def _setup_database(self):
        """Veritabanı başlatma"""
        try:
            # DataStorage sınıfı zaten veritabanını oluşturuyor
            pass
        except Exception as e:
            logger.error(f"Veritabanı başlatma hatası: {e}")
            raise
            
    def _setup_modbus(self):
        """Modbus bağlantısını hazırlar (ilk deneme, başarısız olması normal)"""
        try:
            # İlk bağlantı denemesi - başarısız olabilir, sorun değil
            # start() metodunda tekrar denenecek
            self.modbus_client.connect()
            logger.info("İlk Modbus bağlantı denemesi başarılı")
        except Exception as e:
            # Exception raise etme - start() metodunda tekrar denenecek
            logger.warning(f"İlk Modbus bağlantı denemesi başarısız: {e}")
            logger.info("Modbus bağlantısı start() metodunda tekrar denenecek")

    def _start_control_loop(self):
        """Kontrol döngüsü thread'ini başlatır (sadece bir kez çağrılmalı)"""
        if self.control_loop is None or not self.control_loop.is_alive():
            try:
                # is_running flag start() metodunda ayarlanacak, burada ayarlama
                self.control_loop = threading.Thread(target=self.start_control_loop)
                self.control_loop.daemon = True
                self.control_loop.start()
                logger.info("Kontrol döngüsü thread'i başlatıldı")
            except Exception as e:
                logger.error(f"Kontrol döngüsü başlatma hatası: {e}")
                raise
        else:
            logger.warning("Kontrol döngüsü zaten çalışıyor")
            
    def _start_data_loop(self):
        """Veri döngüsü thread'ini başlatır (sadece bir kez çağrılmalı)"""
        if self.data_loop is None or not self.data_loop.is_alive():
            try:
                self.data_loop = threading.Thread(target=self.start_data_loop)
                self.data_loop.daemon = True
                self.data_loop.start()
                logger.info("Veri döngüsü thread'i başlatıldı")
            except Exception as e:
                logger.error(f"Veri döngüsü başlatma hatası: {e}")
                raise
        else:
            logger.warning("Veri döngüsü zaten çalışıyor")

    def _lazy_init_vision_services(self):
        """Vision service ve wear calculator'ı lazy olarak başlatır (lock dışında çağrılmalı)"""
        try:
            if self.vision_service is None:
                from vision.service import VisionService
                logger.info("VisionService başlatılıyor...")
                self.vision_service = VisionService(
                    recordings_root=os.path.join(os.getcwd(), "recordings"),
                    watchdog_interval_s=0.2,
                )
                self.vision_service.start()
                logger.info("VisionService başlatıldı")
            
            if self.wear_calculator is None:
                from core.wear_calculator import WearCalculator
                logger.info("WearCalculator başlatılıyor...")
                self.wear_calculator = WearCalculator(
                    recordings_root=os.path.join(os.getcwd(), "recordings"),
                    update_callback=self._on_wear_update
                )
                self.wear_calculator.start()
                if hasattr(self, 'gui') and self.gui:
                    self.gui.wear_calculator = self.wear_calculator
                logger.info("WearCalculator başlatıldı")
        except Exception as e:
            logger.error(f"Vision services başlatma hatası: {e}")
    
    def start_control_loop(self):
        """Kontrol döngüsünü başlatır"""
        logger.info("Kontrol döngüsü başlatılıyor...")
        
        vision_services_started = False  # Vision services sadece bir kez başlatılsın
        
        while self.is_running:
            try:
                with self.lock:
                    # Ham veriyi oku
                    raw_data = self.modbus_client.read_all()
                    if raw_data is None:
                        logger.warning("Modbus verisi okunamadı")
                        time.sleep(1)
                        continue
                    
                    # Ham modbus verisini direkt olarak kullan
                    base_data = raw_data.copy()
                    
                    # Aktif kontrolcüyü geçici değişkende tut
                    current_controller = self.controller_factory.active_controller.value if self.controller_factory.active_controller else None
                    
                    # Kesim durumunu kontrol et ve kesim ID'sini güncelle (thread-safe)
                    current_testere_durumu = base_data.get('testere_durumu', 0)
                    
                    # Kesim başlangıcını kontrol et (3: KESIM_YAPILIYOR)
                    if current_testere_durumu == 3 and self.previous_testere_durumu != 3:
                        # Yeni kesim başladı (kesim_id güncellemesi lock içinde)
                        self.current_kesim_id += 1
                        logger.info(f"Yeni kesim başladı. Kesim ID: {self.current_kesim_id}")
                    
                    # Yukarı çıkış durumunu kontrol et (5: SERIT_YUKARI_CIKIYOR) ve kayıt/model yönetimini yap
                    should_start_vision_services = False
                    if current_testere_durumu == TestereState.SERIT_YUKARI_CIKIYOR.value and self.previous_testere_durumu != TestereState.SERIT_YUKARI_CIKIYOR.value:
                        # Yukarı çıkış başladı, kaydı ve modelleri başlat
                        if not self.is_recording_upward:
                            logger.info("Şerit yukarı çıkıyor, kamera kaydı başlatılıyor...")
                            if self.camera_module.start_recording():
                                self.is_recording_upward = True
                                # Detection kayıtla birlikte başlasın
                                try:
                                    self.camera_module.start_detection()
                                except Exception as _e:
                                    logger.error(f"Detection başlatma hatası: {_e}")

                                # Vision services'i lock DIŞINDA başlatmak için flag set et
                                if not vision_services_started:
                                    should_start_vision_services = True
                                    vision_services_started = True
                    elif current_testere_durumu != TestereState.SERIT_YUKARI_CIKIYOR.value and self.previous_testere_durumu == TestereState.SERIT_YUKARI_CIKIYOR.value:
                        # Yukarı çıkış bitti, yalnızca kaydı durdur (modeller çalışmaya devam)
                        if self.is_recording_upward:
                            logger.info("Şerit yukarı çıkış tamamlandı, kamera kaydı durduruluyor...")
                            try:
                                self.camera_module.stop_recording()
                            except Exception as _e:
                                logger.error(f"Kamera kaydı durdurma hatası: {_e}")
                            self.is_recording_upward = False
                    # Önceki durumu güncelle
                    self.previous_testere_durumu = current_testere_durumu
                    
                    # Ek alanları ekle
                    base_data.update({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                        'makine_id': 1,  # Varsayılan makine ID'si
                        'serit_id': 1,  # Varsayılan şerit ID'si
                        'serit_tip': '',
                        'serit_marka': '',
                        'serit_malz': '',
                        'malzeme_cinsi': '',
                        'malzeme_sertlik': '',
                        'kesit_yapisi': '',
                        'fuzzy_output': 0.0,
                        'kesme_hizi_degisim': 0.0,
                        'modbus_connected': self.modbus_client.is_connected,
                        'modbus_ip': '192.168.1.147',
                        'kesim_turu': current_controller if current_testere_durumu == 3 else None,
                        'kesim_id': self.current_kesim_id if current_testere_durumu == 3 else None

                    })
                    
                    # Veriyi işle
                    processed_data = self.data_processor.process_data(base_data)
                    
                    # Son veriyi güncelle
                    self.last_processed_data = dict(processed_data)
                    
                    # Kesim durumunu takip et
                    testere_durumu = int(processed_data.get('testere_durumu', 0))
                    is_cutting = testere_durumu == TestereState.KESIM_YAPILIYOR.value
                    active_controller = self.controller_factory.active_controller
                    controller_name = active_controller.value if active_controller else None
                    
                    # Kesim takipçisini güncelle
                    self.cutting_tracker.update_cutting_state(is_cutting, controller_name)
                    
                    # Kontrol sistemini çalıştır
                    if self.controller_factory.active_controller:
                        try:
                            logger.debug(f"Aktif kontrol sistemi: {self.controller_factory.active_controller.value}")
                            current = float(processed_data.get('serit_motor_akim_a', 0))
                            logger.debug(f"Mevcut akım: {current:.2f}A")
                            
                            self.last_modbus_write_time, output = self.controller_factory.adjust_speeds(
                                processed_data=processed_data,
                                modbus_client=self.modbus_client,
                                last_modbus_write_time=self.last_modbus_write_time,
                                speed_adjustment_interval=self.config.control.speed_adjustment_interval,
                                prev_current=self.prev_current
                            )
                            
                            # Önceki akımı güncelle
                            self.prev_current = current
                            
                            # Kontrol çıktısını kaydet
                            if output is not None:
                                # Fuzzy değerlerini güncelle
                                self.last_processed_data['fuzzy_output'] = output
                                self.last_processed_data['kesme_hizi_degisim'] = output
                            else:
                                logger.debug("Kontrol çıktısı: None")
                            
                        except Exception as e:
                            logger.error(f"Hız ayarlama hatası: {str(e)}")
                            logger.exception("Detaylı hata:")
                    else:
                        logger.debug("Kontrol sistemi aktif değil")
                
                # Lock DIŞINDA vision services başlat (performans için)
                if should_start_vision_services:
                    self._lazy_init_vision_services()
                
                # Döngü gecikmesi
                time.sleep(self.config.control.loop_delay)
                
            except Exception as e:
                logger.error(f"Beklenmeyen hata: {str(e)}")
                logger.exception("Detaylı hata:")
                self.handle_unexpected_error()

    def start_data_loop(self):
        """Veri kayıt ve GUI güncelleme döngüsünü başlatır"""
        logger.info("Veri döngüsü başlatılıyor...")
        
        last_saved_timestamp = None  # Son kaydedilen veri timestamp'i
        
        while self.is_running:
            try:
                snapshot_to_send = None # ThingsBoard için hazırlanan gönderilecek veri
                data_to_save = None
                data_to_update = None
                should_save = False

                # Thread-safe veri okuma
                with self.lock:
                    if self.last_processed_data:
                        # Modbus bağlantısı kontrolü - bağlantı yoksa kaydetme
                        is_connected = self.last_processed_data.get('modbus_connected', False)
                        current_timestamp = self.last_processed_data.get('timestamp')
                        
                        # Sadece yeni veri ise ve bağlantı varsa kaydet
                        if is_connected and current_timestamp != last_saved_timestamp:
                            # Veriyi kopyala (lock içinde)
                            data_to_save = dict(self.last_processed_data)
                            data_to_update = dict(self.last_processed_data)
                            should_save = True
                            last_saved_timestamp = current_timestamp
                        elif not is_connected:
                            # Bağlantı yoksa sadece GUI güncelle (eski veri göster)
                            data_to_update = dict(self.last_processed_data)
                        # Bağlantı var ama timestamp aynı ise hiçbir şey yapma
                        
                        if self.tb_enabled and is_connected:
                            now_ms = int(time.time() * 1000)
                            if (now_ms - self._tb_last_sent_ms) >= self._tb_period_ms:
                                snapshot_to_send = dict(self.last_processed_data)
                                self._tb_last_sent_ms = now_ms
                
                # Lock dışında işlemleri yap
                if should_save and data_to_save:
                    try:
                        # Veriyi kaydet
                        if not self.data_storage.save_data(data_to_save):
                            logger.error("Veri kaydedilemedi")
                    except Exception as e:
                        logger.error(f"Veri kaydetme hatası: {str(e)}")
                
                # GUI'yi her zaman güncelle (bağlantı durumu göstermek için)
                if data_to_update:
                    try:
                        self.gui.update_data(data_to_update)
                    except Exception as e:
                        logger.error(f"GUI güncelleme hatası: {str(e)}")

                if snapshot_to_send is not None and self.tb_enabled and self.tb is not None:
                    try:
                        # 'timestamp' string ise sender.send_processed_row ms'e çevirir ve ts/values ile yollar
                        ok = self.tb.send_processed_row(snapshot_to_send, field_map=self._tb_field_map)
                        if not ok:
                            logger.warning("ThingsBoard gönderimi başarısız (HTTP 2xx değil).")
                    except Exception as e:
                        logger.error(f"ThingsBoard gönderim hatası: {e}")                
                
                # Döngü gecikmesi
                time.sleep(0.1)  # 100ms güncelleme aralığı
                
            except Exception as e:
                logger.error(f"Veri işleme hatası: {str(e)}")

    def start(self):
        """Uygulamayı başlatır"""
        try:
            # SIGINT (Ctrl+C) yakala: Qt loop sonlandırılsın, sonra shutdown
            signal.signal(signal.SIGINT, self.handle_shutdown)

            # GUI'yi başlat (pencereyi gösterir)
            self.gui.start()
            
            # GUI'nin hazır olmasını bekle
            self.gui.gui_ready.wait()
            
            # Modbus bağlantısını kur (ayrı thread'ler de bağlanmaya çalışıyor, burada ilk deneme)
            while True:
                try:
                    logger.info("Modbus bağlantısı kuruluyor...")
                    self.modbus_client.connect()
                    logger.info("Modbus bağlantısı başarılı.")
                    break
                except Exception as e:
                    logger.error(f"Modbus bağlantı hatası: {str(e)}")
                    logger.info("1 saniye sonra tekrar denenecek...")
                    time.sleep(1)
                    continue

            # Çalışma bayrağını ayarla (thread'ler başlamadan önce)
            self.is_running = True
            
            # Thread'leri başlat (kontrol ve veri döngüleri) - sadece bir kez
            logger.info("Kontrol ve veri döngüleri başlatılıyor...")
            self._start_control_loop()
            self._start_data_loop()

            # Thread'lerin başladığını bildir
            self.gui.threads_ready.set()
            
            # Qt event loop'u ANA THREAD'de çalıştır
            exit_code = self.gui.exec()
            logger.info(f"Qt event loop kapandı, kod: {exit_code}")
            
        except Exception as e:
            logger.error(f"Başlatma hatası: {str(e)}")
            self.shutdown()

    def handle_control_error(self):
        """Kontrol sistemi hatalarını yönetir"""
        # Hata sayacını artır
        # Belirli bir sayıda hata olursa sistemi durdur
        pass

    def handle_modbus_error(self):
        """Modbus hatalarını yönetir"""
        while self.is_running:
            try:
                logger.warning("Modbus bağlantısı koptu. Yeniden bağlanmaya çalışılıyor...")
                self.modbus_client.disconnect()
                time.sleep(1)  # 1 saniye bekle
                self.modbus_client.connect()
                logger.info("Modbus bağlantısı başarıyla yeniden kuruldu.")
                return
            except Exception as e:
                logger.error(f"Modbus yeniden bağlanma hatası: {str(e)}")
                time.sleep(1)  # 1 saniye bekle ve tekrar dene

    def handle_unexpected_error(self):
        """Beklenmeyen hataları yönetir"""
        # Hatayı logla ve sistemi güvenli şekilde durdur
        self.shutdown()

    def handle_shutdown(self, signum, frame):
        """Kapatma sinyallerini yakalar"""
        logger.info("Kapatma sinyali alındı. Sistem kapatılıyor...")
        try:
            # Qt loop'u sonlandır
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is not None:
                app.quit()
        except Exception:
            pass
        self.shutdown()

    def shutdown(self):
        """Sistemi güvenli şekilde kapatır"""
        self.is_running = False
        
        try:

            # Vision service ve wear calculator'ı kapat
            if hasattr(self, 'vision_service') and self.vision_service:
                logger.info("Vision service kapatılıyor...")
                self.vision_service.stop()
            
            if hasattr(self, 'wear_calculator') and self.wear_calculator:
                logger.info("Wear calculator kapatılıyor...")
                self.wear_calculator.stop()
            
            # Kamera modülünü kapat
            if hasattr(self, 'camera_module') and self.camera_module:
                logger.info("Kamera modülü kapatılıyor...")
                # Kayıt varsa durdur
                if self.is_recording_upward:
                    try:
                        self.camera_module.stop_recording()
                    except Exception as e:
                        logger.error(f"Kamera kaydı durdurma hatası: {e}")
                # Kamerayı kapat
                self.camera_module.close()
            
            # Kontrol istatistiklerini logla
            stats = self.controller_factory.get_stats()
            logger.info("Kontrol sistemi istatistikleri:")
            for controller_type, controller_stats in stats.items():
                logger.info(f"\n{controller_type}:")
                for key, value in controller_stats.items():
                    logger.info(f"  {key}: {value}")
            
            # Thread'leri bekle
            if self.control_loop and self.control_loop.is_alive():
                self.control_loop.join(timeout=2)
            if self.data_loop and self.data_loop.is_alive():
                self.data_loop.join(timeout=2)
            
            # Modbus bağlantısını kapat
            if self.modbus_client:
                self.modbus_client.disconnect()

            if getattr(self, "tb", None):
                try:
                    self.tb.close()
                except Exception:
                    pass
            
            # Veri depolama sistemini kapat
            self.data_storage.close()
            
            logger.info("Sistem güvenli şekilde kapatıldı.")
            
        except Exception as e:
            logger.error(f"Kapatma sırasında hata: {str(e)}")
        
        finally:
            sys.exit(0)


if __name__ == "__main__":
    smart_saw = SmartSaw()
    smart_saw.start()