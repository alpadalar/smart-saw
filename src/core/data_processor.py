import logging
from typing import Dict, Any, Optional
from datetime import datetime

class ProcessedData:
    def __init__(self, raw_data: Dict = None):
        """İşlenmiş veri sınıfı"""
        self.data = raw_data if raw_data else {}
        
        # Fuzzy verilerini düzenle
        if 'fuzzy_output' not in self.data:
            self.data['fuzzy_output'] = 0.0
        if 'kesme_hizi_degisim' not in self.data:
            self.data['kesme_hizi_degisim'] = 0.0
        
    def __getitem__(self, key):
        return self.data.get(key)
        
    def __setitem__(self, key, value):
        self.data[key] = value
        
    def get(self, key, default=None):
        return self.data.get(key, default)
        
    def to_dict(self):
        return self.data.copy()  # Veriyi kopyalayarak döndür
        
    def copy(self):
        return ProcessedData(self.data.copy())

class DataProcessor:
    def __init__(self, db_manager):
        """Veri işleme sınıfı"""
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
    def process_data(self, raw_data: Dict) -> ProcessedData:
        """Ham veriyi işler"""
        try:
            if not raw_data:
                return ProcessedData()
                
            processed = ProcessedData(raw_data)
            
            # Veriyi kaydet
            self._save_data(processed)
            
            return processed
        except Exception as e:
            self.logger.error(f"Veri işleme hatası: {e}")
            return ProcessedData()
            
    def _save_data(self, processed_data: ProcessedData):
        """İşlenmiş veriyi veritabanına kaydeder"""
        try:
            data_dict = processed_data.to_dict()
            
            # Sensör verilerini kaydet
            self.db_manager.insert_sensor_data({
                'timestamp': data_dict.get('timestamp'),
                'serit_motor_akim': data_dict.get('serit_motor_akim_a'),
                'serit_motor_tork': data_dict.get('serit_motor_tork_percentage'),
                'inme_motor_akim': data_dict.get('inme_motor_akim_a'),
                'inme_motor_tork': data_dict.get('inme_motor_tork_percentage'),
                'mengene_basinc': data_dict.get('mengene_basinc_bar'),
                'serit_gerginlik': data_dict.get('serit_gerginligi_bar'),
                'serit_sapma': data_dict.get('serit_sapmasi'),
                'ortam_sicaklik': data_dict.get('ortam_sicakligi_c'),
                'ortam_nem': data_dict.get('ortam_nem_percentage'),
                'sogutma_sivi_sicaklik': data_dict.get('sogutma_sivi_sicakligi_c'),
                'hidrolik_yag_sicaklik': data_dict.get('hidrolik_yag_sicakligi_c'),
                'ivme_x': data_dict.get('ivme_olcer_x'),
                'ivme_y': data_dict.get('ivme_olcer_y'),
                'ivme_z': data_dict.get('ivme_olcer_z'),
                'frekans_x': data_dict.get('ivme_olcer_x_hz'),
                'frekans_y': data_dict.get('ivme_olcer_y_hz'),
                'frekans_z': data_dict.get('ivme_olcer_z_hz')
            })
            
            # Kesim verilerini kaydet
            self.db_manager.insert_cut_data({
                'timestamp': data_dict.get('timestamp'),
                'serit_id': data_dict.get('serit_id'),
                'malzeme_cinsi': data_dict.get('malzeme_cinsi'),
                'malzeme_sertlik': data_dict.get('malzeme_sertlik'),
                'kesit_yapisi': data_dict.get('kesit_yapisi'),
                'a_mm': data_dict.get('a_mm'),
                'b_mm': data_dict.get('b_mm'),
                'c_mm': data_dict.get('c_mm'),
                'd_mm': data_dict.get('d_mm'),
                'kafa_yukseklik': data_dict.get('kafa_yuksekligi_mm'),
                'kesme_hizi': data_dict.get('serit_kesme_hizi'),
                'inme_hizi': data_dict.get('serit_inme_hizi'),
                'testere_durum': data_dict.get('testere_durumu'),
                'parca_adet': data_dict.get('kesilen_parca_adeti')
            })
            
        except Exception as e:
            self.logger.error(f"Veri kaydetme hatası: {e}") 