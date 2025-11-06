# src/hardware/modbus/client.py
import logging
import threading
import time
from datetime import datetime
from typing import Optional, List, Generator

from pymodbus.client import ModbusTcpClient

from core.logger import logger

class ModbusClient:
    _instance: Optional['ModbusClient'] = None
    _lock = threading.Lock()  # Thread-safe singleton creation için
    
    def __new__(cls, *args, **kwargs):
        # Thread-safe singleton pattern
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False  # İlk oluşturmada flag set et
        return cls._instance
    
    def __init__(self, host='192.168.2.147', port=502):
        """ModbusClient başlatılır (thread-safe)"""
        # Double-check locking pattern
        if not self._initialized:
            with ModbusClient._lock:
                if not self._initialized:
                    self.client = ModbusTcpClient(host=host, port=port)
                    self.connected = False
                    # Global uygulama logger'ını kullan (konsol + dosya)
                    self.logger = logger
                    self.last_write_time = time.time()
                    self.write_interval = 0.1
                    self._last_reconnect_attempt = 0
                    self._reconnect_interval = 2.0  # Minimum 2 seconds between reconnection attempts
                    # Okuma hızını izlemek için sayaçlar (hafif ve thread-safe kullanım)
                    self._reads_in_current_sec = 0
                    self._reads_prev_sec = 0
                    self._last_sec = int(time.time())
                    self._initialized = True
            
    def connect(self) -> bool:
        """Modbus sunucusuna bağlanır"""
        try:
            # Check if we should attempt reconnection (rate limiting)
            current_time = time.time()
            if current_time - self._last_reconnect_attempt < self._reconnect_interval:
                return False
            
            self._last_reconnect_attempt = current_time
            
            if not self.connected:
                self.connected = self.client.connect()
                if self.connected:
                    self.logger.info("Modbus bağlantısı başarılı.")
                    # Add small delay after successful connection
                    time.sleep(0.15)  # 150ms delay for connection stabilization
            return self.connected
        except Exception as e:
            self.logger.error(f"Modbus bağlantı hatası: {e}")
            return False
            
    def disconnect(self):
        """Modbus bağlantısını kapatır"""
        if self.connected:
            self.client.close()
            self.connected = False
            
    @property
    def is_connected(self) -> bool:
        return self.client.is_socket_open()

    def read_registers(self, address: int, count: int) -> Optional[List[int]]:
        """Modbus registerlarını okur"""
        try:
            if not self.client.is_socket_open():
                self.logger.debug("Modbus soketi kapalı, bağlanmayı deniyorum...")
                if self.connect():
                    # Connection successful, small delay already added in connect()
                    pass
                else:
                    # Connection failed or rate limited
                    return None
            
            if self.client.is_socket_open():
                kwargs = {
                    'address': address,
                    'count': count
                }
                response = self.client.read_holding_registers(**kwargs)
                if not response.isError():
                    return response.registers
                else:
                    self.logger.error(f"Register okuma hatası: {response}")
                    # Mark connection as failed
                    self.connected = False
                    return None
            else:
                self.logger.error("Modbus bağlantısı kapalı")
                return None
        except Exception as e:
            self.logger.error(f"Veri okuma hatası: {e}")
            # Mark connection as failed on exception
            self.connected = False
            return None

    def write_register(self, address: int, value: int) -> bool:
        """Modbus registerına yazar"""
        current_time = time.time()
        if current_time - self.last_write_time < self.write_interval:
            self.logger.debug(f"Write interval henüz dolmadı. Kalan süre: {self.write_interval - (current_time - self.last_write_time):.3f}s")
            return False
            
        try:
            if not self.client.is_socket_open():
                self.logger.debug("Modbus soketi kapalı, bağlanmayı deniyorum...")
                self.connect()
            if self.client.is_socket_open():
                kwargs = {
                    'address': address,
                    'value': value
                }
                self.logger.debug(f"Register yazılıyor - Adres: {address}, Değer: {value}")
                result = self.client.write_register(**kwargs)
                if not result.isError():
                    self.last_write_time = current_time
                    self.logger.debug(f"Register yazma başarılı - Adres: {address}, Değer: {value}")
                    return True
                else:
                    self.logger.debug(f"Register yazma başarısız - Adres: {address}, Değer: {value}, Hata: {result}")
                return False
            else:
                self.logger.error("Modbus bağlantısı kapalı")
                return False
        except Exception as e:
            self.logger.error(f"Register yazma hatası: {e}")
            return False

    def read_all(self):
        """Tüm registerları okur"""
        try:
            if not self.client.is_socket_open():
                self.logger.debug("Modbus soketi kapalı, bağlanmayı deniyorum...")
                if self.connect():
                    # Connection successful, small delay already added in connect()
                    pass
                else:
                    # Connection failed or rate limited
                    return None
            
            if self.client.is_socket_open():
                kwargs = {
                    'address': 1000,
                    'count': 42
                }
                response = self.client.read_holding_registers(**kwargs)
                if not response.isError():
                    # Başarılı okuma: saniyelik sayaçları güncelle ve gerekirse logla
                    now_sec = int(time.time())
                    if now_sec != self._last_sec:
                        # Önceki saniyenin toplamını logla
                        self.logger.info(f"Modbus okuma hızı: {self._reads_in_current_sec} okuma/sn")
                        self._reads_prev_sec = self._reads_in_current_sec
                        self._reads_in_current_sec = 0
                        self._last_sec = now_sec
                    self._reads_in_current_sec += 1
                    self.logger.debug(f"Modbus verisi başarıyla okundu. Register sayısı: {len(response.registers)}")
                    self.logger.debug("Modbus registerları okunuyor...")
                    
                    return {
                        'makine_id': response.registers[0],  # 1000
                        'serit_id': response.registers[1],  # 1001
                        'serit_dis_mm': response.registers[2],  # 1002
                        'serit_tip': str(response.registers[3]),  # 1003
                        'serit_marka': str(response.registers[4]),  # 1004
                        'serit_malz': str(response.registers[5]),  # 1005
                        'malzeme_cinsi': str(response.registers[6]),  # 1006
                        'malzeme_sertlik': str(response.registers[7]),  # 1007
                        'kesit_yapisi': str(response.registers[8]),  # 1008
                        'a_mm': response.registers[9],  # 1009
                        'b_mm': response.registers[10],  # 1010
                        'c_mm': response.registers[11],  # 1011
                        'd_mm': response.registers[12],  # 1012
                        'kafa_yuksekligi_mm': response.registers[13],  # 1013
                        'kesilen_parca_adeti': response.registers[14],  # 1014
                        'serit_motor_akim_a': response.registers[15],  # 1015
                        'serit_motor_tork_percentage': response.registers[16],  # 1016
                        'inme_motor_akim_a': response.registers[17],  # 1017
                        'inme_motor_tork_percentage': response.registers[18],  # 1018
                        'mengene_basinc_bar': response.registers[19],  # 1019
                        'serit_gerginligi_bar': response.registers[20],  # 1020
                        'ivme_olcer_x': response.registers[21],  # 1021
                        'ivme_olcer_y': response.registers[22],  # 1022
                        'ivme_olcer_z': response.registers[23],  # 1023
                        'serit_sapmasi': response.registers[24],  # 1024
                        'ortam_sicakligi_c': response.registers[25],  # 1025
                        'ortam_nem_percentage': response.registers[26],  # 1026
                        'sogutma_sivi_sicakligi_c': response.registers[27],  # 1027
                        'hidrolik_yag_sicakligi_c': response.registers[28],  # 1028
                        'serit_sicakligi_c': response.registers[29],  # 1029
                        'testere_durumu': response.registers[30],  # 1030
                        'alarm_status': response.registers[31],  # 1031
                        'alarm_bilgisi': str(response.registers[32]),  # 1032
                        'serit_kesme_hizi': response.registers[33],  # 1033
                        'serit_inme_hizi': response.registers[34],  # 1034
                        'ivme_olcer_x_hz': response.registers[35],  # 1035
                        'ivme_olcer_y_hz': response.registers[36],  # 1036
                        'ivme_olcer_z_hz': response.registers[37],  # 1037
                        'fark_hz_x': response.registers[38],  # 1038
                        'fark_hz_y': response.registers[39],  # 1039
                        'fark_hz_z': response.registers[40],  # 1040
                        'malzeme_genisligi': response.registers[41]  # 1041
                    }
                else:
                    self.logger.error(f"Register okuma hatası: {response}")
                    # Mark connection as failed
                    self.connected = False
                    return None
            return None
        except Exception as e:
            self.logger.error(f"Veri okuma hatası: {e}")
            # Mark connection as failed on exception
            self.connected = False
            return None

    def read_continuous(self, address: int, count: int, interval: float = 0.1) -> Generator[List[int], None, None]:
        """Sürekli register okuma işlemi yapar"""
        while True:
            if self.client.is_socket_open():
                try:
                    kwargs = {
                        'address': address,
                        'count': count
                    }
                    response = self.client.read_holding_registers(**kwargs)
                    if not response.isError():
                        yield response.registers
                    time.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Veri okuma hatası: {e}")
                    time.sleep(interval)
            else:
                self.logger.error("Modbus bağlantısı kapalı, yeniden bağlanmaya çalışılıyor...")
                time.sleep(1)
                self.connect()