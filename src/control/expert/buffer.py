# src/control/expert_adjustment/buffer.py
import time
from collections import deque
from .constants import BUFFER_SURESI

class VeriBuffer:
    def __init__(self):
        self.akim_buffer = deque()
        self.sapma_buffer = deque()
        self.son_veri_zamani = None
    
    def veri_ekle(self, akim, sapma):
        current_time = time.time()
        
        if self.son_veri_zamani is None:
            self.son_veri_zamani = current_time
        
        self.akim_buffer.append((current_time, akim))
        self.sapma_buffer.append((current_time, sapma))
        
        # Eski verileri temizle
        while self.akim_buffer and current_time - self.akim_buffer[0][0] > BUFFER_SURESI:
            self.akim_buffer.popleft()
        while self.sapma_buffer and current_time - self.sapma_buffer[0][0] > BUFFER_SURESI:
            self.sapma_buffer.popleft()
    
    def ortalamalari_al(self):
        if not self.akim_buffer or not self.sapma_buffer:
            return None, None
        
        ort_akim = sum(akim for _, akim in self.akim_buffer) / len(self.akim_buffer)
        ort_sapma = sum(sapma for _, sapma in self.sapma_buffer) / len(self.sapma_buffer)
        
        return ort_akim, ort_sapma