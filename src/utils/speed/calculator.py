# src/utils/speed/calculator.py
from dataclasses import dataclass
import math
from typing import Tuple
from core.constants import KESME_HIZI_REGISTER_ADDRESS, INME_HIZI_REGISTER_ADDRESS

@dataclass
class ModbusSpeedCommand:
    """Modbus'a yazılacak hız komutu"""
    register_address: int
    value: int

class SpeedCalculator:
    """
    Kesme ve inme hızlarını Modbus değerlerine dönüştüren sınıf.
    Sadece hız hesaplamaları ve dönüşümlerinden sorumludur.
    """
    
    @staticmethod
    def calculate_kesme_hizi(real_speed: float) -> ModbusSpeedCommand:
        """
        Gerçek kesme hızını Modbus değerine dönüştürür
        :param real_speed: m/dk cinsinden kesme hızı
        :return: Modbus komutu
        """
        modbus_value = math.ceil(real_speed / 0.0754)
        return ModbusSpeedCommand(
            register_address=KESME_HIZI_REGISTER_ADDRESS,
            value=modbus_value
        )

    @staticmethod
    def calculate_inme_hizi(real_speed: float) -> ModbusSpeedCommand:
        """
        Gerçek inme hızını Modbus değerine dönüştürür
        :param real_speed: mm/dk cinsinden inme hızı
        :return: Modbus komutu
        """
        # İnme hızı hesaplaması
        base_value = math.ceil((real_speed / -0.06) + 65535)
        
        # İşaret biti ayarla
        sign_bit = 0 if real_speed < 0 else (1 << 15)
        modbus_value = sign_bit | (base_value & 0x7FFF)
        
        return ModbusSpeedCommand(
            register_address=INME_HIZI_REGISTER_ADDRESS,
            value=modbus_value
        )