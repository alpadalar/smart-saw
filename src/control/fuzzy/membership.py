# src/control/fuzzy/membership.py
import numpy as np
import skfuzzy as fuzz

class FuzzyMembership:
    def __init__(self):
        # Evrensel kümeler
        self.akim = np.arange(0, 31, 1)
        self.sapma = np.arange(-2, 2.1, 0.1)
        self.hiz_degisimi = np.arange(-10, 10.1, 0.1)
        
        # Akım üyelik fonksiyonları
        self.akim_cok_dusuk = fuzz.trimf(self.akim, [0, 0, 10])
        self.akim_dusuk = fuzz.trimf(self.akim, [5, 12, 16])
        self.akim_normal = fuzz.trimf(self.akim, [14, 17, 20])
        self.akim_yuksek = fuzz.trimf(self.akim, [18, 22, 26])
        self.akim_cok_yuksek = fuzz.trimf(self.akim, [24, 30, 30])
        
        # Sapma üyelik fonksiyonları
        self.sapma_negatif = fuzz.trimf(self.sapma, [-2, -1, 0])
        self.sapma_sifir = fuzz.trimf(self.sapma, [-0.2, 0, 0.2])
        self.sapma_pozitif = fuzz.trimf(self.sapma, [0, 1, 2])
        
        # Hız değişimi üyelik fonksiyonları
        self.hiz_azalt_cok = fuzz.trimf(self.hiz_degisimi, [-10, -10, -5])
        self.hiz_azalt = fuzz.trimf(self.hiz_degisimi, [-7, -4, -1])
        self.hiz_sabit = fuzz.trimf(self.hiz_degisimi, [-2, 0, 2])
        self.hiz_artir = fuzz.trimf(self.hiz_degisimi, [1, 4, 7])
        self.hiz_artir_cok = fuzz.trimf(self.hiz_degisimi, [5, 10, 10])