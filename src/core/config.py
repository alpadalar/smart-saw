# src/core/config.py
import os
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

@dataclass
class DatabaseConfig:
    # SQLite
    sqlite_path: str = "data/testere_{}.db"  # {} makine_id için
    total_db_path: str = "data/total.db"
    raw_db_path: str = "data/raw.db"
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "testere"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

@dataclass
class ModbusConfig:
    host: str = "localhost"
    port: int = 502
    timeout: float = 1.0
    retry_count: int = 3

@dataclass
class ControlConfig:
    default_controller: str = "EXPERT"
    speed_adjustment_interval: float = 1.0
    loop_delay: float = 0.1
    min_speed: float = 5.0
    max_speed: float = 101.0

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "smart_saw.log"
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class StorageConfig:
    data_dir: str = "data"
    backup_dir: str = "backup"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    backup_interval: int = 3600  # 1 saat
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

@dataclass
class Config:
    modbus: ModbusConfig
    control: ControlConfig
    logging: LoggingConfig
    storage: StorageConfig
    debug: bool = False

def load_config() -> Config:
    """Konfigürasyon dosyasını yükler ve Config nesnesini döndürür"""
    # .env dosyasını yükle
    load_dotenv()
    
    # Modbus konfigürasyonu
    modbus_config = ModbusConfig(
        host=os.getenv("MODBUS_HOST", "localhost"),
        port=int(os.getenv("MODBUS_PORT", "502")),
        timeout=float(os.getenv("MODBUS_TIMEOUT", "1.0")),
        retry_count=int(os.getenv("MODBUS_RETRY_COUNT", "3"))
    )
    
    # Kontrol konfigürasyonu
    control_config = ControlConfig(
        default_controller=os.getenv("DEFAULT_CONTROLLER", "EXPERT"),
        speed_adjustment_interval=float(os.getenv("SPEED_ADJUSTMENT_INTERVAL", "1.0")),
        loop_delay=float(os.getenv("LOOP_DELAY", "0.1")),
        min_speed=float(os.getenv("MIN_SPEED", "5.0")),
        max_speed=float(os.getenv("MAX_SPEED", "101.0"))
    )
    
    # Loglama konfigürasyonu
    logging_config = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        file=os.getenv("LOG_FILE", "smart_saw.log"),
        log_dir=os.getenv("LOG_DIR", "logs"),
        max_file_size=int(os.getenv("LOG_MAX_SIZE", str(10 * 1024 * 1024))),
        backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
    )
    
    # Veritabanı konfigürasyonu
    database_config = DatabaseConfig(
        sqlite_path=os.getenv("SQLITE_PATH", "data/testere_{}.db"),
        total_db_path=os.getenv("TOTAL_DB_PATH", "data/total.db"),
        raw_db_path=os.getenv("RAW_DB_PATH", "data/raw.db"),
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_db=os.getenv("POSTGRES_DB", "testere"),
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )
    
    # Depolama konfigürasyonu
    storage_config = StorageConfig(
        data_dir=os.getenv("DATA_DIR", "data"),
        backup_dir=os.getenv("BACKUP_DIR", "backup"),
        max_file_size=int(os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024))),
        backup_interval=int(os.getenv("BACKUP_INTERVAL", "3600")),
        database=database_config
    )
    
    # Ana konfigürasyon
    return Config(
        modbus=modbus_config,
        control=control_config,
        logging=logging_config,
        storage=storage_config,
        debug=os.getenv("DEBUG", "False").lower() == "true"
    )

# Varsayılan konfigürasyon nesnesi
config = load_config()

def get_config() -> Config:
    """Global konfigürasyon nesnesini döndürür"""
    return config