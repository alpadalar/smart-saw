# src/control/fuzzy/rules.py
from .membership import FuzzyMembership
import numpy as np
import skfuzzy as fuzz

class FuzzyRules:
    def __init__(self):
        self.mf = FuzzyMembership()
    
    def evaluate(self, akim_input, sapma_input, titresim_input):
        """
        Fuzzy kuralları değerlendirir ve çıktıyı hesaplar
        
        Args:
            akim_input: Mevcut akım değeri
            sapma_input: Mevcut sapma değeri
            titresim_input: Mevcut titreşim değeri
            
        Returns:
            float: Katsayı değeri
        """
        # Akım üyelik dereceleri
        akim_level_cd = fuzz.interp_membership(self.mf.akim, self.mf.akim_cd, akim_input)
        akim_level_d = fuzz.interp_membership(self.mf.akim, self.mf.akim_d, akim_input)
        akim_level_id = fuzz.interp_membership(self.mf.akim, self.mf.akim_id, akim_input)
        akim_level_y = fuzz.interp_membership(self.mf.akim, self.mf.akim_y, akim_input)
        akim_level_cy = fuzz.interp_membership(self.mf.akim, self.mf.akim_cy, akim_input)
        
        # Sapma üyelik dereceleri
        sapma_level_n = fuzz.interp_membership(self.mf.sapma, self.mf.sapma_n, sapma_input)
        sapma_level_id = fuzz.interp_membership(self.mf.sapma, self.mf.sapma_id, sapma_input)
        sapma_level_p = fuzz.interp_membership(self.mf.sapma, self.mf.sapma_p, sapma_input)
        
        # Titreşim üyelik dereceleri (yorum satırı olarak)
        # titresim_level_id = fuzz.interp_membership(self.mf.titresim, self.mf.titresim_id, titresim_input)
        # titresim_level_y = fuzz.interp_membership(self.mf.titresim, self.mf.titresim_y, titresim_input)
        # titresim_level_cy = fuzz.interp_membership(self.mf.titresim, self.mf.titresim_cy, titresim_input)
        
        # Kural aktivasyonları
        # Çok düşük akım kuralları
        rule1 = np.fmin(np.minimum(akim_level_cd, sapma_level_id), self.mf.katsayi_y)
        
        # Düşük akım kuralları
        rule2 = np.fmin(np.minimum(akim_level_d, sapma_level_id), self.mf.katsayi_y)
        
        # İdeal akım kuralları
        rule3 = np.fmin(np.minimum(akim_level_id, sapma_level_id), self.mf.katsayi_dy)
        rule4 = np.fmin(np.minimum(akim_level_id, sapma_level_n), self.mf.katsayi_d)
        rule5 = np.fmin(np.minimum(akim_level_id, sapma_level_p), self.mf.katsayi_d)
        
        # Yüksek akım kuralları
        rule6 = np.fmin(np.minimum(akim_level_y, sapma_level_id), self.mf.katsayi_d)
        rule7 = np.fmin(np.minimum(akim_level_y, sapma_level_n), self.mf.katsayi_d)
        rule8 = np.fmin(np.minimum(akim_level_y, sapma_level_p), self.mf.katsayi_d)
        
        # Çok yüksek akım kuralları
        rule9 = np.fmin(np.minimum(akim_level_cy, sapma_level_id), self.mf.katsayi_d)
        rule10 = np.fmin(np.minimum(akim_level_cy, sapma_level_n), self.mf.katsayi_cd)
        rule11 = np.fmin(np.minimum(akim_level_cy, sapma_level_p), self.mf.katsayi_cd)
        
        # Titreşim kuralları (yorum satırı olarak)
        # rule12 = np.fmin(titresim_level_y, self.mf.katsayi_d)
        # rule13 = np.fmin(titresim_level_cy, self.mf.katsayi_cd)
        
        # Kural birleştirme
        aggregated = np.fmax.reduce([
            rule1, rule2, rule3, rule4, rule5,
            rule6, rule7, rule8, rule9, rule10, rule11
            # , rule12, rule13  # Titreşim kuralları (yorum satırı olarak)
        ])
        
        # Durulaştırma
        katsayi = fuzz.defuzz(self.mf.katsayi, aggregated, 'centroid')
        
        return katsayi