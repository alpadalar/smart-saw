# src/core/logger.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

class CustomFormatter(logging.Formatter):
    """Özel log formatı"""
    
    def __init__(self):
        super().__init__()
        self.default_fmt = '%(asctime)s [%(levelname)s] %(message)s'
        self.debug_fmt = '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'
        
        self.formatters = {
            logging.DEBUG: logging.Formatter(self.debug_fmt),
            logging.INFO: logging.Formatter(self.default_fmt),
            logging.WARNING: logging.Formatter(self.default_fmt),
            logging.ERROR: logging.Formatter(self.default_fmt),
            logging.CRITICAL: logging.Formatter(self.default_fmt)
        }

    def format(self, record):
        formatter = self.formatters.get(record.levelno)
        return formatter.format(record)

def setup_logger(config):
    """Logger'ı yapılandırır"""
    # Log seviyesini ayarla
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Formatı ayarla
    formatter = CustomFormatter()
    
    # Konsol handler'ı
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    console_handler.encoding = 'utf-8'
    logger.addHandler(console_handler)
    
    # Log dizinini oluştur
    if not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)
    
    # Günlük log dosyası
    daily_log_file = os.path.join(
        config.log_dir,
        f"testere_{datetime.now().strftime('%Y%m%d')}.log"
    )
    
    # Genel log dosyası
    general_log_file = os.path.join(config.log_dir, config.file)
    
    # Dosya handler'ları
    file_handler = RotatingFileHandler(
        general_log_file,
        maxBytes=config.max_file_size,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)
    
    daily_handler = logging.FileHandler(daily_log_file, encoding='utf-8')
    daily_handler.setFormatter(formatter)
    daily_handler.setLevel(log_level)
    logger.addHandler(daily_handler)
    
    logger.info("Logger başlatıldı")

# Global logger nesnesi
logger = logging.getLogger("SmartSaw")

def get_logger() -> logging.Logger:
    """Global logger nesnesini döndürür"""
    return logger

class LoggerContext:
    """Context manager olarak kullanılabilen logger yardımcısı"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"{self.operation} başlatılıyor...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            elapsed = datetime.now() - self.start_time
            logger.info(f"{self.operation} tamamlandı (Süre: {elapsed.total_seconds():.2f}s)")
        else:
            logger.error(f"{self.operation} hata ile sonlandı: {str(exc_val)}")
            return False  # Exception'ı yeniden fırlat

def log_operation(operation: str):
    """Operasyon decorator'ı"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LoggerContext(operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator