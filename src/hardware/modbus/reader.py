# src/hardware/modbus/reader.py
from datetime import datetime
import time
from typing import Generator, List, Optional
from core.logger import logger
from .client import ModbusClient

class ModbusReader:
    def __init__(self, start_address: int, number_of_bits: int):
        self.client = ModbusClient()  # Singleton instance
        self.start_address = start_address
        self.number_of_bits = number_of_bits
        
    def read_data(self, interval: float = 0.1, stop_flag=None) -> Generator[List[int], None, None]:
        """
        Modbus'tan sürekli veri okur
        """
        while True:
            if stop_flag and stop_flag():
                logger.info(f"{datetime.now()}: Modbus veri okuma durduruluyor...")
                break

            if self.client.is_connected:
                data = self.client.read_registers(self.start_address, self.number_of_bits)
                if data:
                    yield data
                time.sleep(interval)
            else:
                logger.warning(f"{datetime.now()}: Bağlantı koptu, bekleniyor...")
                time.sleep(1)