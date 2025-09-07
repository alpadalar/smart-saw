# src/main.py
import sys
import os
# Ensure '/src' is on sys.path for absolute imports like `from core ...`
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
import time
import signal
import threading

import shutil
import glob
try:
    import uvicorn
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False
try:
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import RedirectResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from queue import Queue
from typing import Optional, Dict
from datetime import datetime
import subprocess

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
        
        # Web sunucusu
        self.web_server = None
        self.api_app = None

        
        # KAMERANIN YUKARI CIKARKEN DUZENLENECEK
        # Kesim takibi için değişkenler
        self.current_kesim_id = -1  # Başlangıçta kesim yok
        self.previous_testere_durumu = None
        self.is_recording_upward = False  # Yukarı çıkış kaydı durumu
        
        # Kamera modülü
        self.camera = CameraModule()
        

        
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
        self.is_running = False
        self.last_modbus_write_time = 0
        self.prev_current = 0
        self.last_processed_data = None
        
        # Başlatma
        self._setup_database()
        self._setup_modbus()
        self._setup_control_loop()
        self._setup_data_loop()

        # self._setup_web_server()

        # Kamera kaydı ve detection + vision servisi başlat
        try:
            self.camera_module = CameraModule()
            self.camera_module.start_recording()
            self.camera_module.start_detection()
            
            # Vision service: recordings klasörünü izleyip LDC + wear çalıştırır
            from vision.service import VisionService
            self.vision_service = VisionService(
                recordings_root=os.path.join(os.getcwd(), "recordings"),
                real_ldc_root=os.path.join(os.getcwd(), "real_ldc"),
                watchdog_interval_s=0.2,
            )
            self.vision_service.start()
            
            # Wear calculator: CSV'lerden real-time ortalama hesaplar
            from core.wear_calculator import WearCalculator
            self.wear_calculator = WearCalculator(
                recordings_root=os.path.join(os.getcwd(), "recordings"),
                update_callback=self._on_wear_update
            )
            self.wear_calculator.start()
            
            # GUI'ye wear calculator referansını ver
            if hasattr(self, 'gui') and self.gui:
                self.gui.wear_calculator = self.wear_calculator
            
            logger.info("Kamera kaydı, detection, vision servisi ve wear calculator başlatıldı.")
        except Exception as e:
            logger.error(f"Kamera kaydı/detection/vision başlatılamadı: {e}")


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
        """Modbus başlatma"""
        try:
            self.modbus_client.connect()
        except Exception as e:
            logger.error(f"Modbus başlatma hatası: {e}")
            raise
#WEB SERVER KODLARI
    def _setup_web_server(self):
        """Web sunucusunu doğrudan uvicorn ile (ayrı thread'de) başlatır.
        Dosya yazmaz, 'run_server.py' oluşturmaz.
        """
        if not (UVICORN_AVAILABLE and FASTAPI_AVAILABLE):
            logger.warning("FastAPI/uvicorn yok, web sunucusu başlatılmayacak.")
            return
        try:
            # Webui dizini
            current_dir = os.path.dirname(os.path.abspath(__file__))
            webui_dir = os.path.join(current_dir, "webui")
            if not os.path.exists(webui_dir):
                logger.warning(f"Webui dizini bulunamadı: {webui_dir}")

            # Basit FastAPI uygulaması (statik webui servis eder)
            app = FastAPI()
            app.mount("/", StaticFiles(directory=webui_dir, html=True), name="webui")

            @app.get("/")
            async def _redirect_to_index():
                return RedirectResponse(url="/index.html")

            # Uvicorn'u ayrı bir thread'de başlat
            def _start_server():
                try:
                    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
                except Exception as e:
                    logger.error(f"Uvicorn çalışma hatası: {e}")

            self.web_server = threading.Thread(target=_start_server, daemon=True)
            self.web_server.start()
            logger.info("Web sunucusu başlatıldı. http://localhost:8080 adresinden erişebilirsiniz...")

        except Exception as e:
            logger.error(f"Web sunucusu başlatma hatası: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _setup_web_server_thread(self):
        """
        Web sunucusu ayrı bir process olarak çalıştığından, bu metot artık kullanılmıyor.
        """
        pass
#WEB SERVER KODLARI BURAYA KADAR

    def _setup_control_loop(self):
        """Kontrol döngüsü başlatma"""
        try:
            self.control_loop = threading.Thread(target=self.start_control_loop)
            self.control_loop.daemon = True
            self.is_running = True  # Thread'i başlatmadan önce flag'i ayarla
            self.control_loop.start()  # Thread'i başlat
        except Exception as e:
            logger.error(f"Kontrol döngüsü başlatma hatası: {e}")
            raise
            
    def _setup_data_loop(self):
        """Veri döngüsü başlatma"""
        try:
            self.data_loop = threading.Thread(target=self.start_data_loop)
            self.data_loop.daemon = True
            self.data_loop.start()  # Thread'i başlat
        except Exception as e:
            logger.error(f"Veri döngüsü başlatma hatası: {e}")
            raise

    def start_control_loop(self):
        """Kontrol döngüsünü başlatır"""
        logger.info("Kontrol döngüsü başlatılıyor...")
        
        while self.is_running:
            try:
                with self.lock:
                    # Ham veriyi oku
                    raw_data = self.modbus_client.read_all()
                    if raw_data is None:
                        logger.warning("Modbus verisi okunamadı")
                        time.sleep(1)
                        continue
                    
                    # Veriyi işle
                    mapped_data = self.data_mapper.map_data(raw_data)
                    
                    # Ham modbus verisini direkt olarak kullan
                    base_data = raw_data.copy()
                    
                    # Aktif kontrolcüyü geçici değişkende tut
                    current_controller = self.controller_factory.active_controller.value if self.controller_factory.active_controller else None
                    
                    # Kesim durumunu kontrol et ve kesim ID'sini güncelle
                    current_testere_durumu = base_data.get('testere_durumu', 0)
                    
                    # Kesim başlangıcını kontrol et (3: KESIM_YAPILIYOR)
                    if current_testere_durumu == 3 and self.previous_testere_durumu != 3:
                        # Yeni kesim başladı
                        self.current_kesim_id += 1
                        logger.info(f"Yeni kesim başladı. Kesim ID: {self.current_kesim_id}")
                    
                    # Yukarı çıkış durumunu kontrol et (5: SERIT_YUKARI_CIKIYOR)
                    """
                    if current_testere_durumu == 5 and self.previous_testere_durumu != 5:
                        # Yukarı çıkış başladı, kaydı başlat
                        if not self.is_recording_upward:
                            logger.info("Şerit yukarı çıkıyor, kamera kaydı başlatılıyor...")
                            self.camera.start_recording()
                            self.is_recording_upward = True
                    elif current_testere_durumu != 5 and self.previous_testere_durumu == 5:
                        # Yukarı çıkış bitti, kaydı durdur
                        if self.is_recording_upward:
                            logger.info("Şerit yukarı çıkış tamamlandı, kamera kaydı durduruluyor...")
                            self.camera.stop_recording()
                            self.is_recording_upward = False
                    """
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
                
                # Döngü gecikmesi
                time.sleep(self.config.control.loop_delay)
                
            except Exception as e:
                logger.error(f"Beklenmeyen hata: {str(e)}")
                logger.exception("Detaylı hata:")
                self.handle_unexpected_error()

    def start_data_loop(self):
        """Veri kayıt ve GUI güncelleme döngüsünü başlatır"""
        logger.info("Veri döngüsü başlatılıyor...")
        
        
        while self.is_running:
            try:
                snapshot_to_send = None # ThingsBoard için hazırlanan gönderilecek veri

                with self.lock:
                    if self.last_processed_data:
                        try:
                            # Veriyi kaydet
                            if not self.data_storage.save_data(self.last_processed_data):
                                logger.error("Veri kaydedilemedi")
                            
                            # GUI'yi güncelle
                            self.gui.update_data(self.last_processed_data)
                            if self.tb_enabled:
                                now_ms = int(time.time() * 1000)
                                if (now_ms - self._tb_last_sent_ms) >= self._tb_period_ms:
                                    snapshot_to_send = dict(self.last_processed_data)  # kopya
                                    self._tb_last_sent_ms = now_ms
                        except Exception as e:
                            logger.error(f"Veri kaydetme/güncelleme hatası: {str(e)}")

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

            # Çalışma bayrağını ayarla
            self.is_running = True
            
            # Thread'leri başlat (kontrol ve veri döngüleri)
            self._setup_control_loop()
            self._setup_data_loop()
            

            # Web sunucusunu başlat (opsiyonel)
            self._setup_web_server()

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
                self.camera_module.close()
            """
KAMERA YUKARI CIKARKEN KODU
            # Kamera kaydını durdur
            if self.is_recording_upward:
                self.camera.stop_recording()
            self.camera.close()
            """
            
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

            # Web sunucusunu kapat
            # if hasattr(self, 'web_server') and self.web_server and self.web_server.poll() is None:
            #     logger.info("Web sunucusu kapatılıyor...")
            #     try:
            #         self.web_server.terminate()  # Güvenli bir şekilde sonlandır
            #         self.web_server.wait(timeout=3)  # En fazla 3 saniye bekle
            #     except Exception as e:
            #         logger.error(f"Web sunucusu kapatma hatası: {str(e)}")
            #         try:
            #             self.web_server.kill()  # Son çare olarak zorla sonlandır
            #         except:
            #             pass
            
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