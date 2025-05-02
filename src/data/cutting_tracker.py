# src/data/cutting_tracker.py
import sqlite3
import time
import threading
from datetime import datetime
from typing import Dict, Optional, Tuple
from core.logger import logger
from utils.helpers import get_current_time_ms, calculate_elapsed_time_ms, format_time

class CuttingTracker:
    """Kesim işlemlerini takip eden sınıf"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CuttingTracker, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Sınıfı başlatır"""
        self.thread_local = threading.local()
        self.lock = threading.Lock()
        
        # Kesim bilgileri
        self.is_cutting = False
        self.cutting_start_time = None
        self.last_cutting_start = None
        self.last_cutting_end = None
        self.last_cutting_duration = None  # ms cinsinden
        self.cutting_count = 0
        self.active_controller = None
        
        # Veritabanı bağlantısını oluştur
        self._setup_database()
    
    def _setup_database(self):
        """Veritabanı oluşturur"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Kesim bilgilerini saklayacak tablo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cutting_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cutting_start TEXT,
                    cutting_end TEXT,
                    duration_ms INTEGER,
                    controller TEXT
                )
            ''')
            
            # Uygulamayı her başlattığımızda son kesimleri almak için
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cutting_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cutting_count INTEGER DEFAULT 0,
                    last_start TEXT,
                    last_end TEXT,
                    last_duration_ms INTEGER
                )
            ''')
            
            # İstatistik verisi yoksa ilk satırı ekle
            cursor.execute('SELECT COUNT(*) FROM cutting_stats')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO cutting_stats (cutting_count, last_start, last_end, last_duration_ms)
                    VALUES (0, NULL, NULL, NULL)
                ''')
            
            # Son istatistikleri yükle
            cursor.execute('''
                SELECT cutting_count, last_start, last_end, last_duration_ms
                FROM cutting_stats
                ORDER BY id DESC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                self.cutting_count = row[0]
                self.last_cutting_start = row[1]
                self.last_cutting_end = row[2]
                self.last_cutting_duration = row[3]
                
            conn.commit()
            logger.info("Kesim takip veritabanı başarıyla oluşturuldu")
            
        except Exception as e:
            logger.error(f"Kesim takip veritabanı oluşturma hatası: {str(e)}")
    
    def _get_db_connection(self):
        """Thread-safe veritabanı bağlantısı döndürür"""
        if not hasattr(self.thread_local, 'db'):
            try:
                self.thread_local.db = sqlite3.connect('data/cutting_info.db')
            except Exception as e:
                logger.error(f"Kesim veritabanı bağlantı hatası: {str(e)}")
                return None
        
        return self.thread_local.db
    
    def start_cutting(self, controller_name: str = None):
        """Kesim başlangıcını kaydeder"""
        with self.lock:
            if self.is_cutting:
                return
            
            self.is_cutting = True
            self.cutting_start_time = datetime.now()
            self.last_cutting_start = self.cutting_start_time
            self.active_controller = controller_name
            
            start_time_str = self.cutting_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            try:
                conn = self._get_db_connection()
                cursor = conn.cursor()
                
                # Yeni kesim kaydı başlat
                cursor.execute('''
                    INSERT INTO cutting_info (cutting_start, controller)
                    VALUES (?, ?)
                ''', (start_time_str, controller_name))
                
                # İstatistik tablosunu güncelle
                cursor.execute('''
                    UPDATE cutting_stats
                    SET last_start = ?
                    WHERE id = (SELECT MAX(id) FROM cutting_stats)
                ''', (start_time_str,))
                
                conn.commit()
                logger.info(f"Kesim başlangıcı kaydedildi: {start_time_str}")
            
            except Exception as e:
                logger.error(f"Kesim başlangıcı kaydetme hatası: {str(e)}")
    
    def end_cutting(self):
        """Kesim bitişini kaydeder"""
        with self.lock:
            if not self.is_cutting:
                return
            
            self.is_cutting = False
            end_time = datetime.now()
            self.last_cutting_end = end_time
            
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # Süre hesapla
            if self.cutting_start_time:
                duration_ms = int((end_time - self.cutting_start_time).total_seconds() * 1000)
                self.last_cutting_duration = duration_ms
                
                try:
                    conn = self._get_db_connection()
                    cursor = conn.cursor()
                    
                    # Son kesim kaydını güncelle
                    cursor.execute('''
                        UPDATE cutting_info
                        SET cutting_end = ?, duration_ms = ?
                        WHERE id = (SELECT MAX(id) FROM cutting_info)
                    ''', (end_time_str, duration_ms))
                    
                    # Kesim sayacını artır
                    self.cutting_count += 1
                    
                    # İstatistik tablosunu güncelle
                    cursor.execute('''
                        UPDATE cutting_stats
                        SET cutting_count = ?, last_end = ?, last_duration_ms = ?
                        WHERE id = (SELECT MAX(id) FROM cutting_stats)
                    ''', (self.cutting_count, end_time_str, duration_ms))
                    
                    conn.commit()
                    logger.info(f"Kesim bitişi kaydedildi: {end_time_str}, Süre: {format_time(duration_ms)}")
                
                except Exception as e:
                    logger.error(f"Kesim bitişi kaydetme hatası: {str(e)}")
    
    def update_cutting_state(self, is_cutting: bool, controller_name: str = None):
        """Kesim durumunu günceller"""
        if is_cutting and not self.is_cutting:
            self.start_cutting(controller_name)
        elif not is_cutting and self.is_cutting:
            self.end_cutting()
    
    def get_cutting_info(self):
        """Güncel kesim bilgilerini döndürür"""
        with self.lock:
            try:
                # Son kesim süresini hesapla
                formatted_duration = None
                if self.last_cutting_duration:
                    formatted_duration = format_time(self.last_cutting_duration)
                
                return {
                    "cutting_active": self.is_cutting,
                    "last_cutting_start": self.last_cutting_start,
                    "last_cutting_end": self.last_cutting_end,
                    "last_cutting_duration_ms": self.last_cutting_duration,
                    "last_cutting_duration_formatted": formatted_duration,
                    "cutting_count": self.cutting_count,
                    "active_controller": self.active_controller
                }
            except Exception as e:
                logger.error(f"Kesim bilgisi alma hatası: {str(e)}")
                return {
                    "cutting_active": False,
                    "cutting_count": 0
                }
    
    def get_cutting_history(self, limit: int = 10):
        """Son kesim geçmişini döndürür"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cutting_start, cutting_end, duration_ms, controller
                FROM cutting_info
                WHERE cutting_end IS NOT NULL
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                result.append({
                    "start_time": row[0],
                    "end_time": row[1],
                    "duration_ms": row[2],
                    "duration_formatted": format_time(row[2]) if row[2] else None,
                    "controller": row[3]
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Kesim geçmişi alma hatası: {str(e)}")
            return []
    
    def __del__(self):
        """Yıkıcı metod"""
        if hasattr(self.thread_local, 'db'):
            try:
                self.thread_local.db.close()
            except Exception:
                pass

# Global instance
cutting_tracker = CuttingTracker()

def get_cutting_tracker():
    """Global kesim takip nesnesini döndürür"""
    return cutting_tracker 