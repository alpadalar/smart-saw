import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class SawHealthCalculator:
    """
    Testere sağlığı hesaplayıcı sınıfı.
    Kırık yüzdesi ve aşınma yüzdesini kullanarak genel testere sağlığını hesaplar.
    """
    
    def __init__(self):
        # Kırık yüzdesinin ağırlığı (daha etkili)
        self.BROKEN_WEIGHT = 0.7
        # Aşınma yüzdesinin ağırlığı
        self.WEAR_WEIGHT = 0.3
        
        # Maksimum kabul edilebilir değerler
        self.MAX_BROKEN_PERCENTAGE = 50.0  # %50'den fazla kırık kritik
        self.MAX_WEAR_PERCENTAGE = 80.0    # %80'den fazla aşınma kritik
        
    def calculate_broken_percentage(self, detected_teeth: int, detected_broken: int) -> float:
        """
        Tespit edilen diş ve kırık sayısından kırık yüzdesini hesaplar.
        
        Args:
            detected_teeth: Tespit edilen toplam diş sayısı
            detected_broken: Tespit edilen kırık diş sayısı
            
        Returns:
            Kırık yüzdesi (0.0 - 100.0)
        """
        try:
            if detected_teeth <= 0:
                return 0.0
            
            broken_percentage = (detected_broken / detected_teeth) * 100.0
            return min(broken_percentage, 100.0)  # Maksimum %100
            
        except Exception as e:
            logger.error(f"Kırık yüzdesi hesaplama hatası: {e}")
            return 0.0
    
    def calculate_saw_health(self, 
                           detected_teeth: int, 
                           detected_broken: int, 
                           wear_percentage: float) -> float:
        """
        Testere sağlığı yüzdesini hesaplar.
        
        Args:
            detected_teeth: Tespit edilen toplam diş sayısı
            detected_broken: Tespit edilen kırık diş sayısı
            wear_percentage: Aşınma yüzdesi
            
        Returns:
            Testere sağlığı yüzdesi (0.0 - 100.0)
        """
        try:
            # Kırık yüzdesini hesapla
            broken_percentage = self.calculate_broken_percentage(detected_teeth, detected_broken)
            
            # Aşınma yüzdesini normalize et (0-100 arası)
            normalized_wear = min(wear_percentage, 100.0)
            
            # Kırık ve aşınma etkilerini hesapla
            broken_impact = (broken_percentage / 100.0) * self.BROKEN_WEIGHT
            wear_impact = (normalized_wear / 100.0) * self.WEAR_WEIGHT
            
            # Toplam etki (0.0 - 1.0 arası)
            total_impact = broken_impact + wear_impact
            
            # Testere sağlığı = 100 - (toplam etki * 100)
            saw_health = max(0.0, 100.0 - (total_impact * 100.0))
            
            logger.debug(f"Saw health calculation: broken={broken_percentage:.2f}%, "
                        f"wear={normalized_wear:.2f}%, health={saw_health:.2f}%")
            
            return saw_health
            
        except Exception as e:
            logger.error(f"Testere sağlığı hesaplama hatası: {e}")
            return 100.0  # Hata durumunda %100 sağlıklı varsay
    
    def get_health_status(self, saw_health: float) -> str:
        """
        Testere sağlığı yüzdesine göre durum metni döndürür.
        
        Args:
            saw_health: Testere sağlığı yüzdesi
            
        Returns:
            Durum metni
        """
        if saw_health >= 80.0:
            return "Sağlıklı"
        elif saw_health >= 60.0:
            return "İyi"
        elif saw_health >= 40.0:
            return "Orta"
        elif saw_health >= 20.0:
            return "Kritik"
        else:
            return "Tehlikeli"
    
    def get_health_color(self, saw_health: float) -> str:
        """
        Testere sağlığı yüzdesine göre renk döndürür.
        
        Args:
            saw_health: Testere sağlığı yüzdesi
            
        Returns:
            CSS renk kodu
        """
        if saw_health >= 80.0:
            return "#00FF00"  # Yeşil
        elif saw_health >= 60.0:
            return "#90EE90"  # Açık yeşil
        elif saw_health >= 40.0:
            return "#FFFF00"  # Sarı
        elif saw_health >= 20.0:
            return "#FFA500"  # Turuncu
        else:
            return "#FF0000"  # Kırmızı 