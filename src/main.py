# src/main.py
import sys
import os
import time
import signal
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
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
    get_controller_factory
)
from hardware import ModbusClient
from data import (
    DataProcessor,
    DataStorage,
    DataMapper
)
from data.cutting_tracker import get_cutting_tracker
from models import ProcessedData, SystemState
from gui.qt_controller import SimpleGUI
from control import ControllerFactory
from core.constants import TestereState
from api import create_app, router

class SmartSaw:
    def __init__(self):
        """Smart Saw başlatılır"""
        # Konfigürasyon yükleme
        self.config = load_config()
        
        # Logger'ı başlat
        setup_logger(self.config.logging)
        logger.info("Smart Saw başlatılıyor...")
        
        # Web sunucusu
        self.web_server = None
        self.api_app = None
        
        # Modbus istemcisi
        self.modbus_client = ModbusClient(
            host='192.168.11.186',
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
        
        # Kontrol ve veri döngüleri
        self.control_loop = None
        self.data_loop = None
        self.web_server_thread = None
        
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
        
        logger.info("Başlatma tamamlandı")
        
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
    
    def _setup_web_server(self):
        """Web sunucusu başlatma"""
        try:
            import os
            import subprocess
            import sys
            
            # Mevcut çalışma dizinini ve Python yolunu al
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Webui dizinini bul
            webui_dir = os.path.join(current_dir, "webui")
            if not os.path.exists(webui_dir):
                logger.warning(f"Webui dizini bulunamadı: {webui_dir}")
                
            # Python yorumlayıcı yolu
            python_exe = sys.executable
            
            # Bir komut dosyası oluştur
            server_script = os.path.join(current_dir, "run_server.py")
            
            # Eğer script yoksa, oluştur
            if not os.path.exists(server_script):
                with open(server_script, 'w', encoding='utf-8') as f:
                    f.write("""
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# API modülünü import et
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api import create_app

# FastAPI uygulamasi olustur
app = create_app()

# Webui dizinini bul
current_dir = os.path.dirname(os.path.abspath(__file__))
webui_dir = os.path.join(current_dir, "webui")

# Statik dosyalari monte et
app.mount("/", StaticFiles(directory=webui_dir, html=True), name="webui")

# Ana sayfaya yonlendirme
@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="/index.html")

if __name__ == "__main__":
    print(f"Web arayuzu dosyalari: {webui_dir}")
    print("Web sunucusu baslatiliyor. http://localhost:8080 adresinden erisebilirsiniz...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
""")
            
            # Web sunucusunu ayrı bir süreç olarak başlat
            self.web_server = subprocess.Popen(
                [python_exe, server_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE  # Windows'ta yeni konsol penceresi aç
            )
            
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
                        'modbus_ip': '192.168.11.186'
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
                                logger.debug(f"Kontrol çıktısı: {output}")
                                logger.debug(f"Fuzzy değerleri güncellendi - Output: {output}, Kesme Hızı Değişim: {output}")
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
                with self.lock:
                    if self.last_processed_data:
                        try:
                            # Veriyi kaydet
                            if not self.data_storage.save_data(self.last_processed_data):
                                logger.error("Veri kaydedilemedi")
                            
                            # GUI'yi güncelle
                            self.gui.update_data(self.last_processed_data)
                        except Exception as e:
                            logger.error(f"Veri kaydetme/güncelleme hatası: {str(e)}")
                
                # Döngü gecikmesi
                time.sleep(0.1)  # 100ms güncelleme aralığı
                
            except Exception as e:
                logger.error(f"Veri işleme hatası: {str(e)}")

    def start(self):
        """Uygulamayı başlatır"""
        try:
            # GUI'yi başlat
            self.gui.start()
            
            # GUI'nin hazır olmasını bekle
            self.gui.gui_ready.wait()
            
            # Modbus bağlantısını kur
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
            
            # Thread'leri başlat
            self._setup_control_loop()
            self._setup_data_loop()
            
            # Web sunucusunu başlat
            self._setup_web_server()
            
            # Thread'lerin başladığını bildir
            self.gui.threads_ready.set()
            
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
        self.shutdown()

    def shutdown(self):
        """Sistemi güvenli şekilde kapatır"""
        self.is_running = False
        
        try:
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