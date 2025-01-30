# src/core/exceptions.py

class ControllerNotFoundError(Exception):
    """Kontrol sistemi bulunamadığında fırlatılır"""
    pass

class ControllerError(Exception):
    """Kontrol sistemi çalışırken hata oluştuğunda fırlatılır"""
    pass

class ModbusError(Exception):
    """Modbus iletişiminde hata oluştuğunda fırlatılır"""
    pass

class ConfigError(Exception):
    """Konfigürasyon hatalarında fırlatılır"""
    pass

class DataError(Exception):
    """Veri işleme hatalarında fırlatılır"""
    pass