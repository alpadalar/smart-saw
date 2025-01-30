# src/control/fuzzy/rules.py
from .membership import FuzzyMembership
import numpy as np
import skfuzzy as fuzz

class FuzzyRules:
    def __init__(self):
        self.mf = FuzzyMembership()
    
    def evaluate(self, akim_input, sapma_input):
        # Akım üyelik dereceleri
        akim_level_cd = fuzz.interp_membership(self.mf.akim, self.mf.akim_cok_dusuk, akim_input)
        akim_level_d = fuzz.interp_membership(self.mf.akim, self.mf.akim_dusuk, akim_input)
        akim_level_n = fuzz.interp_membership(self.mf.akim, self.mf.akim_normal, akim_input)
        akim_level_y = fuzz.interp_membership(self.mf.akim, self.mf.akim_yuksek, akim_input)
        akim_level_cy = fuzz.interp_membership(self.mf.akim, self.mf.akim_cok_yuksek, akim_input)
        
        # Sapma üyelik dereceleri
        sapma_level_n = fuzz.interp_membership(self.mf.sapma, self.mf.sapma_negatif, sapma_input)
        sapma_level_s = fuzz.interp_membership(self.mf.sapma, self.mf.sapma_sifir, sapma_input)
        sapma_level_p = fuzz.interp_membership(self.mf.sapma, self.mf.sapma_pozitif, sapma_input)
        
        # Kural aktivasyonları
        rule1 = np.fmin(akim_level_cd, self.mf.hiz_artir_cok)  # Çok düşük akım -> Hızı çok artır
        rule2 = np.fmin(akim_level_d, self.mf.hiz_artir)       # Düşük akım -> Hızı artır
        rule3 = np.fmin(akim_level_n, self.mf.hiz_sabit)       # Normal akım -> Hızı sabit tut
        rule4 = np.fmin(akim_level_y, self.mf.hiz_azalt)       # Yüksek akım -> Hızı azalt
        rule5 = np.fmin(akim_level_cy, self.mf.hiz_azalt_cok)  # Çok yüksek akım -> Hızı çok azalt
        
        # Sapma kuralları
        rule6 = np.fmin(sapma_level_n, self.mf.hiz_azalt)      # Negatif sapma -> Hızı azalt
        rule7 = np.fmin(sapma_level_s, self.mf.hiz_sabit)      # Sıfır sapma -> Hızı sabit tut
        rule8 = np.fmin(sapma_level_p, self.mf.hiz_azalt)      # Pozitif sapma -> Hızı azalt
        
        # Kural birleştirme
        aggregated = np.fmax.reduce([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
        
        # Durulaştırma
        hiz_degisimi = fuzz.defuzz(self.mf.hiz_degisimi, aggregated, 'centroid')
        
        return hiz_degisimi