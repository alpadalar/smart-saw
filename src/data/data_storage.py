# src/data/data_storage.py
import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, Optional

class DataStorage:
    def __init__(self, path: str = "data"):
        """Veri depolama sınıfı
        
        Args:
            path (str): Veritabanı dosyalarının kaydedileceği dizin
        """
        self.logger = logging.getLogger(__name__)
        
        # Veritabanı dizinini oluştur
        if not os.path.exists(path):
            os.makedirs(path)
        
        # Veritabanı dosya yolları
        self.sensor_db = os.path.join(path, "sensor_data.db")
        self.cut_db = os.path.join(path, "cut_data.db")
        
        # Veritabanlarını oluştur
        self._create_databases()
        
    def _create_databases(self):
        """Veritabanı tablolarını oluşturur"""
        try:
            # Sensör veritabanı
            with sqlite3.connect(self.sensor_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        serit_motor_akim REAL,
                        serit_motor_tork REAL,
                        inme_motor_akim REAL,
                        inme_motor_tork REAL,
                        mengene_basinc REAL,
                        serit_gerginlik REAL,
                        serit_sapma REAL,
                        ortam_sicaklik REAL,
                        ortam_nem REAL,
                        sogutma_sivi_sicaklik REAL,
                        hidrolik_yag_sicaklik REAL,
                        ivme_x REAL,
                        ivme_y REAL,
                        ivme_z REAL,
                        frekans_x REAL,
                        frekans_y REAL,
                        frekans_z REAL
                    )
                """)
                
            # Kesim veritabanı
            with sqlite3.connect(self.cut_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cut_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        serit_id INTEGER,
                        malzeme_cinsi TEXT,
                        malzeme_sertlik TEXT,
                        kesit_yapisi TEXT,
                        a_mm REAL,
                        b_mm REAL,
                        c_mm REAL,
                        d_mm REAL,
                        kafa_yukseklik REAL,
                        kesme_hizi REAL,
                        inme_hizi REAL,
                        malzeme_genisligi REAL,
                        testere_durum INTEGER,
                        parca_adet INTEGER
                    )
                """)
                
            self.logger.info("SQLite veritabanları başarıyla oluşturuldu")
            
        except Exception as e:
            self.logger.error(f"Veritabanı oluşturma hatası: {e}")
            raise
            
    def store_data(self, processed_data: Dict):
        """İşlenmiş veriyi veritabanına kaydeder"""
        try:
            data_dict = processed_data.to_dict()
            
            # Sensör verilerini kaydet
            self._insert_sensor_data({
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
            self._insert_cut_data({
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
                'malzeme_genisligi': data_dict.get('malzeme_genisligi'),
                'testere_durum': data_dict.get('testere_durumu'),
                'parca_adet': data_dict.get('kesilen_parca_adeti')
            })
            
        except Exception as e:
            self.logger.error(f"Veri kaydetme hatası: {e}")
            
    def _insert_sensor_data(self, data: Dict):
        """Sensör verilerini kaydeder"""
        try:
            with sqlite3.connect(self.sensor_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sensor_data (
                        timestamp, serit_motor_akim, serit_motor_tork,
                        inme_motor_akim, inme_motor_tork, mengene_basinc,
                        serit_gerginlik, serit_sapma, ortam_sicaklik,
                        ortam_nem, sogutma_sivi_sicaklik, hidrolik_yag_sicaklik,
                        ivme_x, ivme_y, ivme_z, frekans_x, frekans_y, frekans_z
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('timestamp'),
                    data.get('serit_motor_akim'),
                    data.get('serit_motor_tork'),
                    data.get('inme_motor_akim'),
                    data.get('inme_motor_tork'),
                    data.get('mengene_basinc'),
                    data.get('serit_gerginlik'),
                    data.get('serit_sapma'),
                    data.get('ortam_sicaklik'),
                    data.get('ortam_nem'),
                    data.get('sogutma_sivi_sicaklik'),
                    data.get('hidrolik_yag_sicaklik'),
                    data.get('ivme_x'),
                    data.get('ivme_y'),
                    data.get('ivme_z'),
                    data.get('frekans_x'),
                    data.get('frekans_y'),
                    data.get('frekans_z')
                ))
                
        except Exception as e:
            self.logger.error(f"Sensör verisi kaydetme hatası: {e}")
            
    def _insert_cut_data(self, data: Dict):
        """Kesim verilerini kaydeder"""
        try:
            with sqlite3.connect(self.cut_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cut_data (
                        timestamp, serit_id, malzeme_cinsi, malzeme_sertlik,
                        kesit_yapisi, a_mm, b_mm, c_mm, d_mm, kafa_yukseklik,
                        kesme_hizi, inme_hizi, malzeme_genisligi, testere_durum, parca_adet
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('timestamp'),
                    data.get('serit_id'),
                    data.get('malzeme_cinsi'),
                    data.get('malzeme_sertlik'),
                    data.get('kesit_yapisi'),
                    data.get('a_mm'),
                    data.get('b_mm'),
                    data.get('c_mm'),
                    data.get('d_mm'),
                    data.get('kafa_yukseklik'),
                    data.get('kesme_hizi'),
                    data.get('inme_hizi'),
                    data.get('malzeme_genisligi'),
                    data.get('testere_durum'),
                    data.get('parca_adet')
                ))
                
        except Exception as e:
            self.logger.error(f"Kesim verisi kaydetme hatası: {e}")
            
    def get_last_sensor_data(self):
        """Son sensör verilerini getirir"""
        try:
            with sqlite3.connect(self.sensor_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1")
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Sensör verisi okuma hatası: {e}")
            return None
            
    def get_last_cut_data(self):
        """Son kesim verilerini getirir"""
        try:
            with sqlite3.connect(self.cut_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cut_data ORDER BY id DESC LIMIT 1")
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Kesim verisi okuma hatası: {e}")
            return None
            
    def close(self):
        """Veritabanı bağlantılarını kapatır"""
        pass  # SQLite with bloğu otomatik olarak bağlantıyı kapatır 