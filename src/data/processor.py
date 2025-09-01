# src/data/processor.py
from datetime import datetime
from typing import Dict, Any, Optional
from core.logger import logger
from core.data_processor import ProcessedData

class DataProcessor:
    """Ham modbus verilerini işleyip dönüştüren sınıf"""
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Güvenli float dönüşümü yapar"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Güvenli integer dönüşümü yapar"""
        try:
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            return default
    
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
            # Önce tüm alanları kopyala
            processed_data = row_data.copy()
            
            # Zaman damgası ekle/güncelle
            processed_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # Integer dönüşümleri
            processed_data['testere_durumu'] = self._safe_int(row_data.get('testere_durumu'))
            processed_data['alarm_status'] = self._safe_int(row_data.get('alarm_status'))
            processed_data['makine_id'] = self._safe_int(row_data.get('makine_id', 1))
            processed_data['serit_id'] = self._safe_int(row_data.get('serit_id', 1))
            processed_data['serit_dis_mm'] = self._safe_int(row_data.get('serit_dis_mm'))
            processed_data['a_mm'] = self._safe_int(row_data.get('a_mm'))
            processed_data['b_mm'] = self._safe_int(row_data.get('b_mm'))
            processed_data['c_mm'] = self._safe_int(row_data.get('c_mm'))
            processed_data['d_mm'] = self._safe_int(row_data.get('d_mm'))
            processed_data['kesilen_parca_adeti'] = self._safe_int(row_data.get('kesilen_parca_adeti'))
            
            # String dönüşümleri
            processed_data['serit_tip'] = str(row_data.get('serit_tip', ''))
            processed_data['serit_marka'] = str(row_data.get('serit_marka', ''))
            processed_data['serit_malz'] = str(row_data.get('serit_malz', ''))
            processed_data['malzeme_cinsi'] = str(row_data.get('malzeme_cinsi', ''))
            processed_data['malzeme_sertlik'] = str(row_data.get('malzeme_sertlik', ''))
            processed_data['kesit_yapisi'] = str(row_data.get('kesit_yapisi', ''))
            
            # Alarm bilgisini hex string olarak al
            alarm_bilgisi = row_data.get('alarm_bilgisi', '0x0000')
            if isinstance(alarm_bilgisi, str) and alarm_bilgisi.startswith('0x'):
                processed_data['alarm_bilgisi'] = alarm_bilgisi
            else:
                processed_data['alarm_bilgisi'] = f"0x{self._safe_int(alarm_bilgisi):04x}"
            
            # 1/10 ölçekli dönüşümler
            processed_data['kafa_yuksekligi_mm'] = self._safe_float(row_data.get('kafa_yuksekligi_mm')) / 10.0
            processed_data['serit_motor_akim_a'] = self._safe_float(row_data.get('serit_motor_akim_a')) / 10.0
            processed_data['serit_motor_tork_percentage'] = self._safe_float(row_data.get('serit_motor_tork_percentage')) / 10.0
            processed_data['mengene_basinc_bar'] = self._safe_float(row_data.get('mengene_basinc_bar')) / 10.0
            processed_data['serit_gerginligi_bar'] = self._safe_float(row_data.get('serit_gerginligi_bar')) / 10.0
            processed_data['ortam_sicakligi_c'] = self._safe_float(row_data.get('ortam_sicakligi_c')) / 10.0
            processed_data['ortam_nem_percentage'] = self._safe_float(row_data.get('ortam_nem_percentage')) / 10.0
            processed_data['sogutma_sivi_sicakligi_c'] = self._safe_float(row_data.get('sogutma_sivi_sicakligi_c')) / 10.0
            processed_data['hidrolik_yag_sicakligi_c'] = self._safe_float(row_data.get('hidrolik_yag_sicakligi_c')) / 10.0
            
            # 1/100 ölçekli dönüşümler
            processed_data['inme_motor_akim_a'] = self._safe_float(row_data.get('inme_motor_akim_a')) / 100.0
            processed_data['serit_sapmasi'] = self._safe_float(row_data.get('serit_sapmasi')) / 100.0
            
            # İvme ölçer verileri
            processed_data['ivme_olcer_x'] = self._safe_float(row_data.get('ivme_olcer_x'))
            processed_data['ivme_olcer_y'] = self._safe_float(row_data.get('ivme_olcer_y'))
            processed_data['ivme_olcer_z'] = self._safe_float(row_data.get('ivme_olcer_z'))
            processed_data['ivme_olcer_x_hz'] = self._safe_float(row_data.get('ivme_olcer_x_hz'))
            processed_data['ivme_olcer_y_hz'] = self._safe_float(row_data.get('ivme_olcer_y_hz'))
            processed_data['ivme_olcer_z_hz'] = self._safe_float(row_data.get('ivme_olcer_z_hz'))
            
            # Hız hesaplamaları
            # processed_data['serit_kesme_hizi'] = self._safe_float(row_data.get('serit_kesme_hizi')) * 0.0754

            processed_data['serit_kesme_hizi'] = self._safe_float(row_data.get('serit_kesme_hizi')) / 10.0

            
            inme_hizi = self._safe_float(row_data.get('serit_inme_hizi'))
            if inme_hizi == 0:
                processed_data['serit_inme_hizi'] = 0.0
            elif inme_hizi > 500:
                processed_data['serit_inme_hizi'] = inme_hizi - 65536
            else:
                # processed_data['serit_inme_hizi'] = (inme_hizi - 65535) * -0.06
                processed_data['serit_inme_hizi'] = inme_hizi

            # Malzeme genişliği (1/10 ölçekli)
            processed_data['malzeme_genisligi'] = self._safe_float(row_data.get('malzeme_genisligi')) / 10.0
            
            # Fark frekansları (1/100 ölçekli)
            processed_data['fark_hz_x'] = self._safe_float(row_data.get('fark_hz_x')) / 100.0
            processed_data['fark_hz_y'] = self._safe_float(row_data.get('fark_hz_y')) / 100.0
            processed_data['fark_hz_z'] = self._safe_float(row_data.get('fark_hz_z')) / 100.0
            
            # Özel hesaplamalar
            if processed_data['inme_motor_akim_a'] > 15:
                processed_data['inme_motor_akim_a'] = 655.35 - processed_data['inme_motor_akim_a']
            
            if abs(processed_data['serit_sapmasi']) > 1.5:
                processed_data['serit_sapmasi'] = abs(processed_data['serit_sapmasi']) - 655.35
            
            # Fuzzy değerleri
            if fuzzy_output_value is not None:
                processed_data['fuzzy_output'] = fuzzy_output_value
            else:
                processed_data['fuzzy_output'] = self._safe_float(row_data.get('fuzzy_output', 0.0))
                
            # Maksimum titreşim değeri
            processed_data['max_titresim_hz'] = max(
                processed_data['ivme_olcer_x_hz'],
                processed_data['ivme_olcer_y_hz'],
                processed_data['ivme_olcer_z_hz']
            )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Veri işleme hatası: {str(e)}")
            raise

