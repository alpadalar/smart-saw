# src/utils/speed/buffer.py
import math
from dataclasses import dataclass
from typing import Tuple

@dataclass
class SpeedAdjustment:
    kesme_hizi: float = 0.0
    inme_hizi: float = 0.0

class SpeedBuffer:
    def __init__(self):
        self.kesme_hizi_delta = 0.0
        self.inme_hizi_delta = 0.0
        self.threshold = 1.0

    def add_to_buffer(self, kesme_hizi_increment: float, inme_hizi_increment: float):
        """Hız değişimlerini tampona ekler"""
        self.kesme_hizi_delta += kesme_hizi_increment
        self.inme_hizi_delta += inme_hizi_increment

    def should_adjust(self) -> bool:
        """Eşik kontrolü"""
        return (abs(self.kesme_hizi_delta) >= self.threshold or 
                abs(self.inme_hizi_delta) >= self.threshold)

    def get_and_clear(self) -> SpeedAdjustment:
        """Tampondaki değişimleri alır ve tamponu temizler"""
        adjustment = SpeedAdjustment(
            kesme_hizi=math.floor(self.kesme_hizi_delta),
            inme_hizi=math.floor(self.inme_hizi_delta)
        )
        
        # Kalan ondalık kısımları sakla
        self.kesme_hizi_delta -= adjustment.kesme_hizi
        self.inme_hizi_delta -= adjustment.inme_hizi
        
        return adjustment