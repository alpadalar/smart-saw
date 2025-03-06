"""
Fuzzy kontrol sisteminin üyelik fonksiyonlarını ve kurallarını görselleştirir.
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Proje dizinini Python path'ine ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from control.fuzzy.membership import FuzzyMembership
from control.fuzzy.rules import FuzzyRules

class FuzzyVisualizer:
    def __init__(self):
        self.membership = FuzzyMembership()
        self.rules = FuzzyRules()
        
        # Türkçe karakter desteği için
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
    def plot_membership_functions(self):
        """Tüm üyelik fonksiyonlarını görselleştirir"""
        # Tek bir figür oluştur
        plt.figure(figsize=(15, 10))
        
        # Akım üyelik fonksiyonları
        plt.subplot(221)
        x_akim = self.membership.akim
        akim_funcs = {
            'Çok Düşük': self.membership.akim_cd,
            'Düşük': self.membership.akim_d,
            'İdeal': self.membership.akim_id,
            'Yüksek': self.membership.akim_y,
            'Çok Yüksek': self.membership.akim_cy
        }
        for name, values in akim_funcs.items():
            plt.plot(x_akim, values, label=name)
        plt.title('Akım Üyelik Fonksiyonları')
        plt.xlabel('Akım (A)')
        plt.ylabel('Üyelik Derecesi')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Sapma üyelik fonksiyonları
        plt.subplot(222)
        x_sapma = self.membership.sapma
        sapma_funcs = {
            'Negatif': self.membership.sapma_n,
            'İdeal': self.membership.sapma_id,
            'Pozitif': self.membership.sapma_p
        }
        for name, values in sapma_funcs.items():
            plt.plot(x_sapma, values, label=name)
        plt.title('Sapma Üyelik Fonksiyonları')
        plt.xlabel('Sapma (mm)')
        plt.ylabel('Üyelik Derecesi')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Katsayı üyelik fonksiyonları
        plt.subplot(223)
        x_katsayi = self.membership.katsayi
        katsayi_funcs = {
            'Çok Düşür': self.membership.katsayi_cd,
            'Düşür': self.membership.katsayi_d,
            'Değişim Yok': self.membership.katsayi_dy,
            'Yükselt': self.membership.katsayi_y,
            'Çok Yükselt': self.membership.katsayi_cy
        }
        for name, values in katsayi_funcs.items():
            plt.plot(x_katsayi, values, label=name)
        plt.title('Katsayı Üyelik Fonksiyonları')
        plt.xlabel('Katsayı')
        plt.ylabel('Üyelik Derecesi')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Boş alt grafik
        plt.subplot(224)
        plt.text(0.5, 0.5, 'Titreşim üyelik fonksiyonları\nşu anda devre dışı',
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes)
        plt.axis('off')
        
        # Düzeni ayarla
        plt.tight_layout()
        plt.show()
        
    def print_fuzzy_rules(self):
        """Fuzzy kuralları yazdırır"""
        print("\n" + "="*50)
        print("Fuzzy Kontrol Kuralları:")
        print("="*50)
        
        # Kuralları gruplandırarak yazdır
        rules_by_type = {
            "Akım Kuralları": [],
            "Sapma Kuralları": [],
            "Titreşim Kuralları": [],
            "Kombine Kurallar": []
        }
        
        # Kuralları sınıflandır
        for i, rule in enumerate(self.rules.rule_list, 1):
            rule_str = f"{i}. EĞER {rule}"
            if "VE" in rule_str:
                rules_by_type["Kombine Kurallar"].append(rule_str)
            elif "akım" in rule_str:
                rules_by_type["Akım Kuralları"].append(rule_str)
            elif "sapma" in rule_str:
                rules_by_type["Sapma Kuralları"].append(rule_str)
            elif "titreşim" in rule_str:
                rules_by_type["Titreşim Kuralları"].append(rule_str)
        
        # Gruplandırılmış kuralları yazdır
        for rule_type, rules in rules_by_type.items():
            if rules:
                print(f"\n{rule_type}:")
                print("-"*20)
                for rule in rules:
                    print(rule)
        
        print("\n" + "="*50)

def main():
    """Ana fonksiyon - görselleştirmeyi başlatır"""
    visualizer = FuzzyVisualizer()
    visualizer.plot_membership_functions()
    visualizer.print_fuzzy_rules()

if __name__ == "__main__":
    main() 