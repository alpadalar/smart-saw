# src/data/mapper.py
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

from core import logger
from models.data_models import (
    ModbusRegisters,
    RawData,
    ProcessedData,
    SpeedData
)

@dataclass
class DataMapper:
    """Ham veriyi işlenmiş veriye dönüştürür"""
    
    def __init__(self):
        self.registers = ModbusRegisters()
        self._last_processed_data: Optional[ProcessedData] = None

    def map_data(self, raw_data: Dict[int, float]) -> ProcessedData:
        """
        Ham modbus verisini işlenmiş veriye dönüştürür
        
        Args:
            raw_data: Ham modbus register değerleri
            
        Returns:
            ProcessedData: İşlenmiş veri
        """
        try:
            # Timestamp oluştur
            current_time = datetime.now()
            
            # Register değerlerini al
            serit_motor_akim = raw_data.get(
                self.registers.REGISTERS['SERIT_MOTOR_AKIM'], 
                0.0
            )
            serit_sapma = raw_data.get(
                self.registers.REGISTERS['SERIT_SAPMA'], 
                0.0
            )
            kafa_yukseklik = raw_data.get(
                self.registers.REGISTERS['KAFA_YUKSEKLIK'], 
                0.0
            )
            testere_durum = int(raw_data.get(
                self.registers.REGISTERS['TESTERE_DURUM'], 
                0
            ))
            kesme_hiz = raw_data.get(
                self.registers.REGISTERS['KESME_HIZ'], 
                0.0
            )
            inme_hiz = raw_data.get(
                self.registers.REGISTERS['INME_HIZ'], 
                0.0
            )
            
            # Değerleri ölçek ve birimlere dönüştür
            processed_data = ProcessedData(
                timestamp=current_time,
                serit_motor_akim_a=self._scale_current(serit_motor_akim),
                serit_sapmasi=self._scale_deviation(serit_sapma),
                kafa_yuksekligi_mm=self._scale_height(kafa_yukseklik),
                testere_durumu=testere_durum,
                serit_kesme_hizi=self._scale_speed(kesme_hiz),
                serit_inme_hizi=self._scale_speed(inme_hiz)
            )
            
            # Son işlenmiş veriyi sakla
            self._last_processed_data = processed_data
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Veri dönüştürme hatası: {str(e)}")
            # Hata durumunda son geçerli veriyi veya varsayılan değerleri döndür
            return self._last_processed_data or ProcessedData(
                timestamp=datetime.now()
            )

    def _scale_current(self, raw_value: float) -> float:
        """Akım değerini ölçeklendirir (0-65535 -> 0-100A)"""
        try:
            return (raw_value / 65535) * 100.0
        except:
            return 0.0

    def _scale_deviation(self, raw_value: float) -> float:
        """Sapma değerini ölçeklendirir (0-65535 -> -10mm - +10mm)"""
        try:
            return ((raw_value / 65535) * 20.0) - 10.0
        except:
            return 0.0

    def _scale_height(self, raw_value: float) -> float:
        """Yükseklik değerini ölçeklendirir (0-65535 -> 0-300mm)"""
        try:
            return (raw_value / 65535) * 300.0
        except:
            return 0.0

    def _scale_speed(self, raw_value: float) -> float:
        """Hız değerini ölçeklendirir (0-65535 -> 0-100mm/s)"""
        try:
            return (raw_value / 65535) * 100.0
        except:
            return 0.0

    def get_last_processed_data(self) -> Optional[ProcessedData]:
        """Son işlenmiş veriyi döndürür"""
        return self._last_processed_data

    def map_speed_data(self, speed_data: Dict[str, float]) -> SpeedData:
        """
        Hız verilerini SpeedData nesnesine dönüştürür
        
        Args:
            speed_data: Ham hız değerleri
            
        Returns:
            SpeedData: İşlenmiş hız verisi
        """
        return SpeedData(
            kesme_hizi=speed_data.get('kesme_hizi', 0.0),
            inme_hizi=speed_data.get('inme_hizi', 0.0),
            timestamp=datetime.now()
        )

    def reverse_map_speeds(self, speed_data: SpeedData) -> Dict[int, float]:
        """
        SpeedData nesnesini modbus register değerlerine dönüştürür
        
        Args:
            speed_data: İşlenmiş hız verisi
            
        Returns:
            Dict[int, float]: Register adresi -> değer eşlemesi
        """
        try:
            # Hızları 0-65535 aralığına dönüştür
            kesme_hiz_raw = (speed_data.kesme_hizi / 100.0) * 65535
            inme_hiz_raw = (speed_data.inme_hizi / 100.0) * 65535
            
            return {
                self.registers.REGISTERS['KESME_HIZ']: kesme_hiz_raw,
                self.registers.REGISTERS['INME_HIZ']: inme_hiz_raw
            }
            
        except Exception as e:
            logger.error(f"Hız değeri dönüştürme hatası: {str(e)}")
            return {
                self.registers.REGISTERS['KESME_HIZ']: 0,
                self.registers.REGISTERS['INME_HIZ']: 0
            }