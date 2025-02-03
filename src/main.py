# src/main.py
import sys
import time
import signal
import threading
from queue import Queue
from typing import Optional, Dict
from datetime import datetime

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
from models import ProcessedData, SystemState
from gui.controller import SimpleGUI

class SmartSaw:
    def __init__(self):
        """Smart Saw uygulamasını başlatır"""
        # Konfigürasyon yükle
        self.config: Config = load_config()
        
        # Logger'ı ayarla
        setup_logger(self.config.logging)
        logger.info("Smart Saw başlatılıyor...")
        
        # Kontrol sistemi factory'sini al
        self.controller_factory = get_controller_factory()
        self.controller_factory.set_controller(ControllerType[self.config.control.default_controller.upper()])
        
        # Modbus bağlantısını kur
        self.modbus_client = ModbusClient(
            host=self.config.modbus.host,
            port=self.config.modbus.port
        )
        
        # Veri işleme bileşenlerini oluştur
        self.data_mapper = DataMapper()
        self.data_processor = DataProcessor()
        self.data_storage = DataStorage(self.config.storage)
        
        # GUI'yi oluştur
        self.gui = SimpleGUI()
        
        # Durum değişkenleri
        self.is_running = False
        self.last_modbus_write_time = 0
        self.prev_current = 0
        self.system_state = SystemState.IDLE
        
        # Thread'ler
        self.control_thread: Optional[threading.Thread] = None
        self.data_thread: Optional[threading.Thread] = None
        
        # Thread güvenliği için lock
        self.lock = threading.Lock()
        
        # Son işlenmiş veri
        self.last_processed_data: Dict = {}
        
        # Sinyal yakalayıcıları
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        logger.info("Başlatma tamamlandı")

    def start_control_loop(self):
        """Kontrol döngüsünü başlatır"""
        logger.info("Kontrol döngüsü başlatılıyor...")
        
        while self.is_running:
            try:
                with self.lock:
                    # Ham veriyi oku
                    raw_data = self.modbus_client.read_all()
                    
                    # Veriyi işle
                    mapped_data = self.data_mapper.map_data(raw_data)
                    processed_data: ProcessedData = self.data_processor.process_data(mapped_data)
                    
                    # Son veriyi güncelle
                    self.last_processed_data = processed_data
                    
                    # Kontrol sistemini çalıştır
                    if self.controller_factory.active_controller:
                        self.last_modbus_write_time, output = self.controller_factory.adjust_speeds(
                            processed_data=processed_data,
                            modbus_client=self.modbus_client,
                            last_modbus_write_time=self.last_modbus_write_time,
                            speed_adjustment_interval=self.config.control.speed_adjustment_interval,
                            prev_current=self.prev_current
                        )
                        
                        # Önceki akımı güncelle
                        self.prev_current = processed_data.get('serit_motor_akim_a', 0)
                
                # Döngü gecikmesi
                time.sleep(self.config.control.loop_delay)
                
            except ControllerError as e:
                logger.error(f"Kontrol sistemi hatası: {str(e)}")
                self.handle_control_error()
                
            except ModbusError as e:
                logger.error(f"Modbus iletişim hatası: {str(e)}")
                self.handle_modbus_error()
                
            except Exception as e:
                logger.error(f"Beklenmeyen hata: {str(e)}")
                self.handle_unexpected_error()

    def start_data_loop(self):
        """Veri kayıt ve GUI güncelleme döngüsünü başlatır"""
        logger.info("Veri döngüsü başlatılıyor...")
        
        while self.is_running:
            try:
                with self.lock:
                    if self.last_processed_data:
                        # Veriyi kaydet
                        self.data_storage.store_data(self.last_processed_data)
                        
                        # GUI'yi güncelle
                        self.gui.update_data(self.last_processed_data)
                
                # Döngü gecikmesi
                time.sleep(0.1)  # 100ms güncelleme aralığı
                
            except Exception as e:
                logger.error(f"Veri işleme hatası: {str(e)}")

    def start(self):
        """Uygulamayı başlatır"""
        while True:
            try:
                # Modbus bağlantısını aç
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
        
        # Kontrol thread'ini başlat
        self.control_thread = threading.Thread(target=self.start_control_loop)
        self.control_thread.daemon = True
        self.control_thread.start()
        
        # Veri thread'ini başlat
        self.data_thread = threading.Thread(target=self.start_data_loop)
        self.data_thread.daemon = True
        self.data_thread.start()
        
        # GUI'yi ana thread'de başlat
        self.gui.start()

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
            if self.control_thread and self.control_thread.is_alive():
                self.control_thread.join(timeout=2)
            if self.data_thread and self.data_thread.is_alive():
                self.data_thread.join(timeout=2)
            
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