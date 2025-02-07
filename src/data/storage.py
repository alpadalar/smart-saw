# src/data/storage.py
from typing import Dict, Any
import sqlite3
import psycopg2
import os
from datetime import datetime
from core.logger import logger
from core.config import Config

class LocalStorage:
    """SQLite veritabanı işlemleri"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.storage.database.sqlite_path
        self.total_db = config.storage.database.total_db_path
        self.raw_db = config.storage.database.raw_db_path
        
        # Veritabanı dizinlerini oluştur
        self._create_directories()
        
        # Veritabanlarını ve tabloları oluştur
        self._initialize_databases()
        
    def _create_directories(self):
        """Veritabanı dizinlerini oluşturur"""
        try:
            # data dizinini oluştur
            data_dir = os.path.dirname(self.total_db)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                logger.info(f"Veritabanı dizini oluşturuldu: {data_dir}")
        except Exception as e:
            logger.error(f"Dizin oluşturma hatası: {str(e)}")
            raise
        
    def _initialize_databases(self):
        """Veritabanlarını ve tabloları oluşturur"""
        try:
            # Tablo oluşturma SQL'i
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS testere_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                makine_id INTEGER,
                serit_id INTEGER,
                serit_dis_mm INTEGER,
                serit_tip VARCHAR(50),
                serit_marka VARCHAR(50),
                serit_malz VARCHAR(50),
                malzeme_cinsi VARCHAR(50),
                malzeme_sertlik VARCHAR(50),
                kesit_yapisi VARCHAR(50),
                a_mm INTEGER,
                b_mm INTEGER,
                c_mm INTEGER,
                d_mm INTEGER,
                kafa_yuksekligi_mm REAL,
                kesilen_parca_adeti INTEGER,
                serit_motor_akim_a REAL,
                serit_motor_tork_percentage REAL,
                inme_motor_akim_a REAL,
                inme_motor_tork_percentage REAL,
                mengene_basinc_bar REAL,
                serit_gerginligi_bar REAL,
                serit_sapmasi REAL,
                ortam_sicakligi_c REAL,
                ortam_nem_percentage REAL,
                sogutma_sivi_sicakligi_c REAL,
                hidrolik_yag_sicakligi_c REAL,
                serit_sicakligi_c REAL,
                ivme_olcer_x REAL,
                ivme_olcer_y REAL,
                ivme_olcer_z REAL,
                ivme_olcer_x_hz REAL,
                ivme_olcer_y_hz REAL,
                ivme_olcer_z_hz REAL,
                max_titresim_hz REAL,
                testere_durumu INTEGER,
                alarm_status INTEGER,
                alarm_bilgisi VARCHAR(10),
                serit_kesme_hizi REAL,
                serit_inme_hizi REAL,
                fuzzy_output REAL,
                kesme_hizi_degisim REAL,
                modbus_connected INTEGER,
                modbus_ip VARCHAR(50)
            )
            """
            
            # Ana veritabanı için
            if not os.path.exists(self.db_path.format(1)):
                conn = sqlite3.connect(self.db_path.format(1))  # Başlangıçta makine_id=1 için
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                conn.close()
                logger.info(f"Ana veritabanı oluşturuldu: {self.db_path.format(1)}")
            
            # Total veritabanı için
            if not os.path.exists(self.total_db):
                conn = sqlite3.connect(self.total_db)
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                conn.close()
                logger.info(f"Total veritabanı oluşturuldu: {self.total_db}")
            
            # Raw veritabanı için
            if not os.path.exists(self.raw_db):
                conn = sqlite3.connect(self.raw_db)
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                conn.close()
                logger.info(f"Raw veritabanı oluşturuldu: {self.raw_db}")
            
            logger.info("SQLite veritabanları kontrol edildi")
            
        except Exception as e:
            logger.error(f"SQLite veritabanı oluşturma hatası: {str(e)}")
            raise

    def save_data(self, data: Dict[str, Any]) -> bool:
        """Veriyi SQLite'a kaydeder"""
        try:
            # Fuzzy verilerini düzenle
            if 'fuzzy_output' not in data:
                data['fuzzy_output'] = 0.0
            
            # Eski fuzzy sütunlarını kaldır
            data.pop('fuzzy_akim_uyelik', None)
            data.pop('fuzzy_sapma_uyelik', None)
            data.pop('fuzzy_hiz_uyelik', None)
            data.pop('fuzzy_kural_aktivasyonlari', None)
            data.pop('fuzzy_sapma_degisimi', None)
            data.pop('fuzzy_hiz_degisimi', None)
            data.pop('controller_output', None)
            data.pop('fuzzy_akim_degisim', None)
            
            # Ana veritabanına kaydet
            conn = sqlite3.connect(self.db_path.format(data['makine_id']))
            cursor = conn.cursor()
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = tuple(data.values())
            
            query = f"INSERT INTO testere_data ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, values)
            conn.commit()
            
            # Total veritabanına kaydet
            total_conn = sqlite3.connect(self.total_db)
            total_cursor = total_conn.cursor()
            total_cursor.execute(query, values)
            total_conn.commit()
            
            # Raw veritabanına kaydet
            raw_conn = sqlite3.connect(self.raw_db)
            raw_cursor = raw_conn.cursor()
            raw_cursor.execute(query, values)
            raw_conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"SQLite kayıt hatası: {str(e)}")
            return False
            
        finally:
            if 'conn' in locals(): conn.close()
            if 'total_conn' in locals(): total_conn.close()
            if 'raw_conn' in locals(): raw_conn.close()


class RemoteStorage:
    """PostgreSQL veritabanı işlemleri (Devre dışı)"""
    
    def __init__(self, config):
        self.enabled = False  # Devre dışı
        self.config = config
        self.connection_params = {
            'host': config.storage.database.postgres_host,
            'port': config.storage.database.postgres_port,
            'database': config.storage.database.postgres_db,
            'user': config.storage.database.postgres_user,
            'password': config.storage.database.postgres_password
        }
    
    def _initialize_table(self):
        """PostgreSQL tablosunu oluşturur (Devre dışı)"""
        if not self.enabled:
            return
            
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS testere_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                makine_id INTEGER,
                serit_id INTEGER,
                serit_dis_mm INTEGER,
                serit_tip VARCHAR(50),
                serit_marka VARCHAR(50),
                serit_malz VARCHAR(50),
                malzeme_cinsi VARCHAR(50),
                malzeme_sertlik VARCHAR(50),
                kesit_yapisi VARCHAR(50),
                a_mm INTEGER,
                b_mm INTEGER,
                c_mm INTEGER,
                d_mm INTEGER,
                kafa_yuksekligi_mm REAL,
                kesilen_parca_adeti INTEGER,
                serit_motor_akim_a REAL,
                serit_motor_tork_percentage REAL,
                inme_motor_akim_a REAL,
                inme_motor_tork_percentage REAL,
                mengene_basinc_bar REAL,
                serit_gerginligi_bar REAL,
                serit_sapmasi REAL,
                ortam_sicakligi_c REAL,
                ortam_nem_percentage REAL,
                sogutma_sivi_sicakligi_c REAL,
                hidrolik_yag_sicakligi_c REAL,
                serit_sicakligi_c REAL,
                ivme_olcer_x REAL,
                ivme_olcer_y REAL,
                ivme_olcer_z REAL,
                ivme_olcer_x_hz REAL,
                ivme_olcer_y_hz REAL,
                ivme_olcer_z_hz REAL,
                max_titresim_hz REAL,
                testere_durumu INTEGER,
                alarm_status INTEGER,
                alarm_bilgisi VARCHAR(10),
                serit_kesme_hizi REAL,
                serit_inme_hizi REAL,
                fuzzy_output REAL,
                kesme_hizi_degisim REAL,
                modbus_connected INTEGER,
                modbus_ip VARCHAR(50)
            )
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("PostgreSQL tablosu başarıyla oluşturuldu")
            
        except Exception as e:
            logger.error(f"PostgreSQL tablo oluşturma hatası: {str(e)}")
            raise
            
        finally:
            if 'conn' in locals():
                conn.close()

    def save_data(self, data: Dict[str, Any]) -> bool:
        """Veriyi PostgreSQL'e kaydeder (Devre dışı)"""
        if not self.enabled:
            return True
            
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s' for _ in data])
            values = tuple(data.values())
            
            query = f"INSERT INTO testere_data ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, values)
            conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL kayıt hatası: {str(e)}")
            return False
            
        finally:
            if 'conn' in locals():
                conn.close()


class DataStorage:
    """Veritabanı işlemlerini yöneten ana sınıf"""
    
    def __init__(self, config):
        self.config = config
        self.local_storage = LocalStorage(config)
        self.remote_storage = RemoteStorage(config)
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Veriyi hem local hem remote veritabanlarına kaydeder"""
        local_success = self.local_storage.save_data(data)
        remote_success = self.remote_storage.save_data(data)
        
        return local_success and remote_success

    def close(self):
        """Veritabanı bağlantılarını kapatır"""
        pass

