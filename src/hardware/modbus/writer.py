# src/hardware/modbus/writer.py
from typing import Optional
from core.logger import logger
from .client import ModbusClient

class ModbusWriter:
    def __init__(self):
        self.client = ModbusClient()
        
    def write_register(self, address: int, value: int) -> bool:
        """
        Verilen değeri belirtilen adrese yazar
        :param address: Register adresi
        :param value: Yazılacak değer (16-bit integer)
        :return: Yazma işleminin başarı durumu
        """
        try:
            return self.client.write_register(address, value)
        except Exception as e:
            logger.error(f"Register yazma hatası - Adres: {address}, Değer: {value}, Hata: {e}")
            return False