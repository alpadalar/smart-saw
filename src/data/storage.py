# src/data/storage.py
from typing import Dict, Any
import sqlite3
try:
    import psycopg2  # optional, only needed if RemoteStorage.enabled
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None
    _PSYCOPG2_AVAILABLE = False
import os
from datetime import datetime
from core.logger import logger
from core.config import Config

class LocalStorage:
    """SQLite veritabanı işlemleri"""
    
    # Güvenli column isimleri whitelist (SQL injection koruması)
    ALLOWED_COLUMNS = {
        'id', 'timestamp', 'makine_id', 'serit_id', 'serit_dis_mm', 'serit_tip',
        'serit_marka', 'serit_malz', 'malzeme_cinsi', 'malzeme_sertlik',
        'kesit_yapisi', 'a_mm', 'b_mm', 'c_mm', 'd_mm', 'kafa_yuksekligi_mm',
        'kesilen_parca_adeti', 'serit_motor_akim_a', 'serit_motor_tork_percentage',
        'inme_motor_akim_a', 'inme_motor_tork_percentage', 'mengene_basinc_bar',
        'serit_gerginligi_bar', 'serit_sapmasi', 'ortam_sicakligi_c',
        'ortam_nem_percentage', 'sogutma_sivi_sicakligi_c', 'hidrolik_yag_sicakligi_c',
        'serit_sicakligi_c', 'ivme_olcer_x', 'ivme_olcer_y', 'ivme_olcer_z',
        'ivme_olcer_x_hz', 'ivme_olcer_y_hz', 'ivme_olcer_z_hz', 'max_titresim_hz',
        'testere_durumu', 'alarm_status', 'alarm_bilgisi', 'serit_kesme_hizi',
        'serit_inme_hizi', 'malzeme_genisligi', 'fark_hz_x', 'fark_hz_y',
        'fark_hz_z', 'fuzzy_output', 'kesme_hizi_degisim', 'modbus_connected',
        'modbus_ip', 'kesim_turu', 'kesim_id'
    }
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.storage.database.sqlite_path
        self.total_db = config.storage.database.total_db_path
        self.raw_db = config.storage.database.raw_db_path
        
        # Thread-local storage için
        import threading
        self._thread_local = threading.local()
        
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
        
    def _add_kesim_turu_column(self, db_path: str):
        """Kesim türü sütununu ekler"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Sütunun var olup olmadığını kontrol et
            cursor.execute("PRAGMA table_info(testere_data)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'kesim_turu' not in columns:
                cursor.execute("ALTER TABLE testere_data ADD COLUMN kesim_turu VARCHAR(20)")
                logger.info(f"Kesim türü sütunu eklendi: {db_path}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Kesim türü sütunu ekleme hatası: {str(e)}")
            raise

    def _add_kesim_id_column(self, db_path: str):
        """Kesim ID sütununu ekler"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Sütunun var olup olmadığını kontrol et
            cursor.execute("PRAGMA table_info(testere_data)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'kesim_id' not in columns:
                cursor.execute("ALTER TABLE testere_data ADD COLUMN kesim_id INTEGER")
                logger.info(f"Kesim ID sütunu eklendi: {db_path}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Kesim ID sütunu ekleme hatası: {str(e)}")
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
                malzeme_genisligi REAL,
                fark_hz_x REAL,
                fark_hz_y REAL,
                fark_hz_z REAL,
                fuzzy_output REAL,
                kesme_hizi_degisim REAL,
                modbus_connected INTEGER,
                modbus_ip VARCHAR(50),
                kesim_turu VARCHAR(20),
                kesim_id INTEGER
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
            else:
                self._add_kesim_turu_column(self.db_path.format(1))
                self._add_kesim_id_column(self.db_path.format(1))
            
            # Total veritabanı için
            if not os.path.exists(self.total_db):
                conn = sqlite3.connect(self.total_db)
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                conn.close()
                logger.info(f"Total veritabanı oluşturuldu: {self.total_db}")
            else:
                self._add_kesim_turu_column(self.total_db)
                self._add_kesim_id_column(self.total_db)
            
            # Raw veritabanı için
            if not os.path.exists(self.raw_db):
                conn = sqlite3.connect(self.raw_db)
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                conn.close()
                logger.info(f"Raw veritabanı oluşturuldu: {self.raw_db}")
            else:
                self._add_kesim_turu_column(self.raw_db)
                self._add_kesim_id_column(self.raw_db)
            
            logger.info("SQLite veritabanları kontrol edildi")
            
        except Exception as e:
            logger.error(f"SQLite veritabanı oluşturma hatası: {str(e)}")
            raise

    def _get_connection(self, db_path: str):
        """Thread-safe connection döndürür"""
        # Her thread için ayrı connection kullan
        if not hasattr(self._thread_local, 'connections'):
            self._thread_local.connections = {}
        
        if db_path not in self._thread_local.connections:
            # Her thread için ayrı connection kullandığımızdan check_same_thread parametresine gerek yok
            conn = sqlite3.connect(db_path)
            self._thread_local.connections[db_path] = conn
        
        return self._thread_local.connections[db_path]
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Veriyi SQLite'a kaydeder (thread-safe, SQL injection korumalı)"""
        conn = None
        total_conn = None
        raw_conn = None
        
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
            
            # Kesim türünü belirle
            testere_durumu = data.get('testere_durumu', 0)
            if testere_durumu == 3:  # KESIM_YAPILIYOR durumu
                active_controller = data.get('active_controller', '')
                data['kesim_turu'] = active_controller if active_controller else 'manual'
            else:
                data['kesim_turu'] = None
            
            # SQL injection koruması - sadece izin verilen column'ları kullan
            safe_data = {}
            for key, value in data.items():
                if key in self.ALLOWED_COLUMNS:
                    safe_data[key] = value
                else:
                    logger.warning(f"İzin verilmeyen column atlandı: {key}")
            
            if not safe_data:
                logger.error("Kaydedilecek geçerli veri yok")
                return False
            
            # SQL query hazırla (güvenli column isimleri ile)
            columns = ', '.join(safe_data.keys())
            placeholders = ', '.join(['?' for _ in safe_data])
            values = tuple(safe_data.values())
            query = f"INSERT INTO testere_data ({columns}) VALUES ({placeholders})"
            
            # Ana veritabanına kaydet (thread-safe connection)
            conn = self._get_connection(self.db_path.format(data['makine_id']))
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            
            # Total veritabanına kaydet (thread-safe connection)
            total_conn = self._get_connection(self.total_db)
            total_cursor = total_conn.cursor()
            total_cursor.execute(query, values)
            total_conn.commit()
            
            # Raw veritabanına kaydet (thread-safe connection)
            raw_conn = self._get_connection(self.raw_db)
            raw_cursor = raw_conn.cursor()
            raw_cursor.execute(query, values)
            raw_conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"SQLite kayıt hatası: {str(e)}")
            return False
    
    def __del__(self):
        """Cleanup - thread-local connection'ları kapat"""
        try:
            if hasattr(self, '_thread_local') and hasattr(self._thread_local, 'connections'):
                for db_path, conn in self._thread_local.connections.items():
                    try:
                        conn.close()
                        logger.debug(f"LocalStorage connection kapatıldı: {db_path}")
                    except Exception:
                        pass
        except Exception:
            pass


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
        if not self.enabled or not _PSYCOPG2_AVAILABLE:
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
                malzeme_genisligi REAL,
                fark_hz_x REAL,
                fark_hz_y REAL,
                fark_hz_z REAL,
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
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

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
        try:
            # LocalStorage connection'ları kapat
            if hasattr(self.local_storage, '_thread_local'):
                if hasattr(self.local_storage._thread_local, 'connections'):
                    for db_path, conn in self.local_storage._thread_local.connections.items():
                        try:
                            conn.close()
                            logger.info(f"Veritabanı bağlantısı kapatıldı: {db_path}")
                        except Exception as e:
                            logger.error(f"Veritabanı kapatma hatası ({db_path}): {e}")
        except Exception as e:
            logger.error(f"DataStorage cleanup hatası: {e}")

