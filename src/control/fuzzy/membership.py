# src/control/fuzzy/membership.py
import numpy as np
import skfuzzy as fuzz

class FuzzyMembership:
    def __init__(self):
        # Evrensel kümeler
        self.akim = np.arange(8, 39, 1)
        self.sapma = np.arange(-1, 1.2, 0.2)
        self.katsayi = np.arange(-1, 1.2, 0.2)
        # self.titresim = np.arange(0, 3, 0.2)  # titreşim için evrensel küme
        
        # Akım üyelik fonksiyonları
        self.akim_cd = fuzz.trimf(self.akim, [4, 8, 12])     # çok düşük
        self.akim_d = fuzz.trimf(self.akim, [10, 13, 16])    # düşük
        self.akim_id = fuzz.trimf(self.akim, [14, 17, 20])   # ideal
        self.akim_y = fuzz.trimf(self.akim, [18, 21, 24])    # yüksek
        self.akim_cy = fuzz.trimf(self.akim, [22, 30, 38])   # çok yüksek
        
        # Sapma üyelik fonksiyonları
        self.sapma_n = fuzz.trimf(self.sapma, [-1.6, -1, -0.2])   # negatif
        self.sapma_id = fuzz.trimf(self.sapma, [-0.4, 0, 0.4])    # ideal
        self.sapma_p = fuzz.trimf(self.sapma, [0.2, 1, 1.8])      # pozitif
        
        # Titreşim üyelik fonksiyonları (yorum satırı olarak)
        # self.titresim_id = fuzz.trimf(self.titresim, [-0.8, 0, 0.8])   # ideal
        # self.titresim_y = fuzz.trimf(self.titresim, [0.1, 1, 1.8])     # yüksek
        # self.titresim_cy = fuzz.trimf(self.titresim, [1.1, 2, 2.8])    # çok yüksek
        
        # Katsayı üyelik fonksiyonları
        self.katsayi_cd = fuzz.trimf(self.katsayi, [-1.4, -1, -0.8])    # çok düşür
        self.katsayi_d = fuzz.trimf(self.katsayi, [-1, -0.6, -0.2])     # düşür
        self.katsayi_dy = fuzz.trimf(self.katsayi, [-0.2, 0, 0.3])      # değişim yok
        self.katsayi_y = fuzz.trimf(self.katsayi, [0.2, 0.5, 1])        # yükselt
        self.katsayi_cy = fuzz.trimf(self.katsayi, [0.8, 1, 1.4])       # çok yükselt

        # Akım üyelik fonksiyonları
        # self.akim_cd = fuzz.trimf(self.akim, [4, 8, 12])  # çok düşük
        # self.akim_d = fuzz.trimf(self.akim, [11, 13, 15])  # düşük
        # self.akim_id = fuzz.trimf(self.akim, [14, 17, 20])  # ideal
        # self.akim_y = fuzz.trimf(self.akim, [19, 21, 23])  # yüksek
        # self.akim_cy = fuzz.trimf(self.akim, [22, 30, 38])  # çok yüksek