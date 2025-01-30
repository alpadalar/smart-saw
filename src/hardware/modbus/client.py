# src/hardware/modbus/client.py
from pymodbus.client import ModbusTcpClient
from core.logger import logger
from typing import Optional
import time

class ModbusClient:
    _instance: Optional['ModbusClient'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, ip: str = None, port: int = None):
        if not hasattr(self, 'initialized'):
            self.ip = ip
            self.port = port
            self.client = ModbusTcpClient(self.ip, port=self.port)
            self.last_write_time = time.time()
            self.write_interval = 0.1
            self.initialized = True
            
    def connect(self) -> bool:
        try:
            if not self.client.connected:
                return self.client.connect()
            return True
        except Exception as e:
            logger.error(f"Modbus bağlantı hatası: {e}")
            return False
            
    def disconnect(self):
        if self.client.connected:
            self.client.close()
            
    @property
    def is_connected(self) -> bool:
        return self.client.is_socket_open()

    def read_registers(self, address: int, count: int):
        """Register oku"""
        try:
            response = self.client.read_holding_registers(address, count)
            if not response.isError():
                return response.registers
            return None
        except Exception as e:
            logger.error(f"Register okuma hatası: {e}")
            return None

    def write_register(self, address: int, value: int) -> bool:
        """Register yaz"""
        current_time = time.time()
        if current_time - self.last_write_time < self.write_interval:
            return False
            
        try:
            result = self.client.write_register(address, value)
            if not result.isError():
                self.last_write_time = current_time
                return True
            return False
        except Exception as e:
            logger.error(f"Register yazma hatası: {e}")
            return False