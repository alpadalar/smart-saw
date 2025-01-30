# src/core/logger.py
import os
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

def setup_logger(config) -> logging.Logger:
    """Logger'ı yapılandırır ve döndürür"""
    # Log dizinini oluştur
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Log dosya yolunu oluştur
    log_file = os.path.join(log_dir, config.file)
    
    # Logger'ı yapılandır
    logger = logging.getLogger("SmartSaw")
    logger.setLevel(getattr(logging, config.level.upper()))
    
    # Dosya handler'ı
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.max_size,
        backupCount=config.backup_count
    )
    file_handler.setFormatter(CustomFormatter())
    
    # Konsol handler'ı
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter())
    
    # Handler'ları ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("Logger başlatıldı")
    return logger

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