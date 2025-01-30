# src/data/storage.py
from typing import Dict, Any
import sqlite3
import psycopg2
from datetime import datetime
from core.logger import logger
from core.config import Config

class LocalStorage:
    """SQLite veritabanı işlemleri"""
    
    def __init__(self):
        self.db_path = Config.SQLITE_PATH
        self.total_db = Config.TOTAL_DB_PATH
        self.raw_db = Config.RAW_DB_PATH
        
        # Veritabanlarını ve tabloları oluştur
        self._initialize_databases()
        
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
                serit_tip TEXT,
                serit_marka TEXT,
                serit_malz TEXT,
                malzeme_cinsi TEXT,
                malzeme_sertlik TEXT,
                kesit_yapisi TEXT,
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
                ivme_olcer_x REAL,
                ivme_olcer_y REAL,
                ivme_olcer_z REAL,
                ivme_olcer_x_hz REAL,
                ivme_olcer_y_hz REAL,
                ivme_olcer_z_hz REAL,
                testere_durumu INTEGER,
                alarm_status INTEGER,
                alarm_bilgisi TEXT,
                serit_kesme_hizi REAL,
                serit_inme_hizi REAL
            )
            """
            
            # Ana veritabanı için
            conn = sqlite3.connect(self.db_path.format(1))  # Başlangıçta makine_id=1 için
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            conn.close()
            
            # Total veritabanı için
            conn = sqlite3.connect(self.total_db)
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            conn.close()
            
            # Raw veritabanı için
            conn = sqlite3.connect(self.raw_db)
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            conn.close()
            
            logger.info("SQLite veritabanları başarıyla oluşturuldu")
            
        except Exception as e:
            logger.error(f"SQLite veritabanı oluşturma hatası: {str(e)}")
            raise

    def save_data(self, data: Dict[str, Any]) -> bool:
        """Veriyi SQLite'a kaydeder"""
        try:
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
    """PostgreSQL veritabanı işlemleri"""
    
    def __init__(self):
        self.connection_params = {
            'host': Config.POSTGRES_HOST,
            'port': Config.POSTGRES_PORT,
            'database': Config.POSTGRES_DB,
            'user': Config.POSTGRES_USER,
            'password': Config.POSTGRES_PASSWORD
        }
        
        # Tabloyu oluştur
        self._initialize_table()
        
    def _initialize_table(self):
        """PostgreSQL tablosunu oluşturur"""
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
                ivme_olcer_x REAL,
                ivme_olcer_y REAL,
                ivme_olcer_z REAL,
                ivme_olcer_x_hz REAL,
                ivme_olcer_y_hz REAL,
                ivme_olcer_z_hz REAL,
                testere_durumu INTEGER,
                alarm_status INTEGER,
                alarm_bilgisi VARCHAR(10),
                serit_kesme_hizi REAL,
                serit_inme_hizi REAL
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
        """Veriyi PostgreSQL'e kaydeder"""
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
    
    def __init__(self):
        self.local_storage = LocalStorage()
        self.remote_storage = RemoteStorage()
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Veriyi hem local hem remote veritabanlarına kaydeder"""
        local_success = self.local_storage.save_data(data)
        remote_success = self.remote_storage.save_data(data)
        
        return local_success and remote_success

