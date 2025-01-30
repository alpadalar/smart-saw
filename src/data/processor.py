# src/data/processor.py
from datetime import datetime
from typing import Dict, Any, Optional
from core.logger import logger

class DataProcessor:
    """Ham modbus verilerini işleyip dönüştüren sınıf"""
    
    def process_data(self, row_data: Dict[str, Any], fuzzy_output_value: Optional[float] = None) -> Dict[str, Any]:
        """
        Ham veriyi işler ve dönüştürür
        
        Args:
            row_data: İşlenecek ham veri
            fuzzy_output_value: Opsiyonel fuzzy çıktı değeri
            
        Returns:
            Dict: İşlenmiş veri
        """
        try:
            # Milisaniye hassasiyetinde zaman damgası ekle
            row_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # Integer dönüşümleri
            row_data['testere_durumu'] = int(row_data['testere_durumu'])
            row_data['alarm_status'] = int(row_data['alarm_status'])
            
            # Hex formatı
            row_data['alarm_bilgisi'] = f"0x{int(row_data['alarm_bilgisi']):04x}"
            
            # 1/10 ölçekli dönüşümler
            row_data['kafa_yuksekligi_mm'] = row_data['kafa_yuksekligi_mm'] / 10.0
            row_data['serit_motor_akim_a'] = row_data['serit_motor_akim_a'] / 10.0
            row_data['serit_motor_tork_percentage'] = row_data['serit_motor_tork_percentage'] / 10.0
            row_data['mengene_basinc_bar'] = row_data['mengene_basinc_bar'] / 10.0
            row_data['serit_gerginligi_bar'] = row_data['serit_gerginligi_bar'] / 10.0
            row_data['ortam_sicakligi_c'] = row_data['ortam_sicakligi_c'] / 10.0
            row_data['ortam_nem_percentage'] = row_data['ortam_nem_percentage'] / 10.0
            row_data['sogutma_sivi_sicakligi_c'] = row_data['sogutma_sivi_sicakligi_c'] / 10.0
            row_data['hidrolik_yag_sicakligi_c'] = row_data['hidrolik_yag_sicakligi_c'] / 10.0
            
            # 1/100 ölçekli dönüşümler
            row_data['inme_motor_akim_a'] = row_data['inme_motor_akim_a'] / 100.0
            row_data['serit_sapmasi'] = row_data['serit_sapmasi'] / 100.0
            
            # İvme ölçer verileri
            row_data['ivme_olcer_x'] = row_data['ivme_olcer_x'] / 1.0
            row_data['ivme_olcer_y'] = row_data['ivme_olcer_y'] / 1.0
            row_data['ivme_olcer_z'] = row_data['ivme_olcer_z'] / 1.0
            
            # Hız hesaplamaları
            row_data['serit_kesme_hizi'] = row_data['serit_kesme_hizi'] * 0.0754
            
            if row_data['serit_inme_hizi'] == 0:
                row_data['serit_inme_hizi'] = 0.0
            else:
                row_data['serit_inme_hizi'] = (row_data['serit_inme_hizi'] - 65535) * -0.06
            
            # Özel hesaplamalar
            if row_data['inme_motor_akim_a'] > 15:
                row_data['inme_motor_akim_a'] = 655.35 - row_data['inme_motor_akim_a']
            
            if abs(row_data['serit_sapmasi']) > 1.5:
                row_data['serit_sapmasi'] = abs(row_data['serit_sapmasi']) - 655.35
            
            return row_data
            
        except Exception as e:
            logger.error(f"Veri işleme hatası: {str(e)}")
            raise

