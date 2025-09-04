# src/hardware/machine_control.py
"""
Makine kontrol modülü
Bu modül, makinedeki belirli register ve bitleri kontrol etmek için kullanılır.
"""

from typing import Optional
from core.logger import logger
from .modbus.client import ModbusClient


class MachineControl:
    """
    Makine kontrol sınıfı
    Belirtilen register ve bitleri kontrol eder
    """
    
    # Register adresleri
    CONTROL_REGISTER = 20
    COOLANT_REGISTER = 2000
    KONVEYOR_REGISTER = 102
    
    # Bit pozisyonları (0'dan başlar)
    CHIP_CLEANING_BIT = 3        # 102.3: Talaş temizlik
    CUTTING_START_BIT = 3        # 20.3: Kesim başlat
    CUTTING_STOP_BIT = 4         # 20.4: Kesim durdur
    REAR_VISE_OPEN_BIT = 5       # 20.5: Mengene kontrol arka mengeneyi aç
    FRONT_VISE_OPEN_BIT = 6      # 20.6: Mengene kontrol ön mengeneyi aç
    MATERIAL_FORWARD_BIT = 7     # 20.7: Malzeme konumlandırma öne sür
    MATERIAL_BACKWARD_BIT = 8    # 20.8: Malzeme konumlandırma arkaya sür
    SAW_UP_BIT = 9               # 20.9: Testere konumlandırma yukarı kaldır
    SAW_DOWN_BIT = 10            # 20.10: Testere konumlandırma aşağı indir
    COOLANT_BIT = 1              # 2000.1: Soğutma sıvısı
    
    def __init__(self):
        """MachineControl sınıfını başlatır"""
        self.client = ModbusClient()
        self.logger = logger
        # Modbus bağlantısını garanti altına al
        try:
            if not self.client.is_connected:
                self.client.connect()
        except Exception as e:
            self.logger.error(f"Modbus bağlantısı başlatılırken hata: {e}")
        # Uygulama başlarken mevcut (default) register ve bit değerlerini sadece oku ve logla
        try:
            self.log_default_states()
        except Exception as e:
            self.logger.error(f"Başlangıç durumları loglanırken hata: {e}")
        
    def _set_bit(self, register: int, bit_position: int, value: bool) -> bool:
        """
        Belirtilen registerda belirtilen biti ayarlar
        
        Args:
            register: Register adresi
            bit_position: Bit pozisyonu (0'dan başlar)
            value: Bit değeri (True/False)
            
        Returns:
            bool: İşlem başarı durumu
        """
        try:
            # Önce mevcut register değerini oku
            current_value = self.client.read_registers(register, 1)
            if current_value is None:
                self.logger.error(f"Register {register} okunamadı")
                return False
                
            current_value = current_value[0]
            
            # Bit maskesi oluştur
            bit_mask = 1 << bit_position
            
            if value:
                # Biti 1 yap
                new_value = current_value | bit_mask
            else:
                # Biti 0 yap
                new_value = current_value & ~bit_mask
                
            # Yeni değeri yaz
            success = self.client.write_register(register, new_value)
            if success:
                self.logger.debug(f"Register {register}, bit {bit_position} {value} olarak ayarlandı")
                # Yazım sonrası doğrulama: register'ı geri oku ve bit durumlarını logla
                try:
                    verify = self.client.read_registers(register, 1)
                    if verify is not None:
                        read_back = verify[0]
                        self.logger.info(
                            f"Register {register} yazım sonrası raw=0x{read_back:04X} ({read_back}), hedef bit {bit_position}={(read_back >> bit_position) & 1}"
                        )
                        # Bilinen registerlar için ayrıntılı bit log'u
                        if register == self.CONTROL_REGISTER:
                            self.logger.info(
                                " - chip_cleaning(20.2): %s" % bool((read_back >> self.CHIP_CLEANING_BIT) & 1)
                            )
                            self.logger.info(
                                " - cutting_start(20.3): %s" % bool((read_back >> self.CUTTING_START_BIT) & 1)
                            )
                            self.logger.info(
                                " - cutting_stop(20.4): %s" % bool((read_back >> self.CUTTING_STOP_BIT) & 1)
                            )
                            self.logger.info(
                                " - rear_vise_open(20.5): %s" % bool((read_back >> self.REAR_VISE_OPEN_BIT) & 1)
                            )
                            self.logger.info(
                                " - front_vise_open(20.6): %s" % bool((read_back >> self.FRONT_VISE_OPEN_BIT) & 1)
                            )
                            self.logger.info(
                                " - material_forward(20.7): %s" % bool((read_back >> self.MATERIAL_FORWARD_BIT) & 1)
                            )
                            self.logger.info(
                                " - material_backward(20.8): %s" % bool((read_back >> self.MATERIAL_BACKWARD_BIT) & 1)
                            )
                            self.logger.info(
                                " - saw_up(20.9): %s" % bool((read_back >> self.SAW_UP_BIT) & 1)
                            )
                            self.logger.info(
                                " - saw_down(20.10): %s" % bool((read_back >> self.SAW_DOWN_BIT) & 1)
                            )
                        elif register == self.COOLANT_REGISTER:
                            self.logger.info(
                                " - coolant(2000.1): %s" % bool((read_back >> self.COOLANT_BIT) & 1)
                            )
                    else:
                        self.logger.warning(f"Register {register} doğrulama okuması başarısız")
                except Exception as e:
                    self.logger.error(f"Yazım sonrası doğrulama hatası: {e}")
            else:
                self.logger.error(f"Register {register}, bit {bit_position} ayarlanamadı")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Bit ayarlama hatası: {e}")
            return False
    
    def _get_bit(self, register: int, bit_position: int) -> Optional[bool]:
        """
        Belirtilen registerda belirtilen bitin değerini okur
        
        Args:
            register: Register adresi
            bit_position: Bit pozisyonu (0'dan başlar)
            
        Returns:
            Optional[bool]: Bit değeri veya None (hata durumunda)
        """
        try:
            current_value = self.client.read_registers(register, 1)
            if current_value is None:
                return None
                
            bit_value = (current_value[0] >> bit_position) & 1
            return bool(bit_value)
            
        except Exception as e:
            self.logger.error(f"Bit okuma hatası: {e}")
            return None

    def _write_register_atomic(self, register: int, set_bits: list[int], clear_bits: list[int]) -> bool:
        """
        Aynı register üzerinde bir veya daha fazla biti tek yazımda set/clear yapar.
        Yazım sonrası doğrulama log'u üretir.
        """
        try:
            current_value_list = self.client.read_registers(register, 1)
            if current_value_list is None:
                self.logger.error(f"Register {register} okunamadı (atomic write)")
                return False
            current_value = current_value_list[0]
            new_value = current_value
            for b in set_bits:
                new_value |= (1 << b)
            for b in clear_bits:
                new_value &= ~(1 << b)
            if new_value == current_value:
                # Değişiklik yok ama yine de doğrulamayı loglayalım
                self.logger.debug(f"Register {register} atomic değişiklik yok (0x{current_value:04X})")
                return True
            success = self.client.write_register(register, new_value)
            if not success:
                self.logger.error(f"Register {register} atomic yazım başarısız")
                return False
            # Doğrulama
            verify = self.client.read_registers(register, 1)
            if verify is not None:
                read_back = verify[0]
                self.logger.info(
                    f"Register {register} atomic sonrası raw=0x{read_back:04X} ({read_back})"
                )
            return True
        except Exception as e:
            self.logger.error(f"Atomic yazım hatası: {e}")
            return False

    # Mengene için atomik yardımcılar (karşılıklı dışlayıcı)
    def open_rear_vise_exclusive(self) -> bool:
        """Arka mengeneyi açar ve ön mengeneyi kapatır (tek yazım)."""
        return self._write_register_atomic(
            self.CONTROL_REGISTER,
            set_bits=[self.REAR_VISE_OPEN_BIT],
            clear_bits=[self.FRONT_VISE_OPEN_BIT]
        )

    def open_front_vise_exclusive(self) -> bool:
        """Ön mengeneyi açar ve arka mengeneyi kapatır (tek yazım)."""
        return self._write_register_atomic(
            self.CONTROL_REGISTER,
            set_bits=[self.FRONT_VISE_OPEN_BIT],
            clear_bits=[self.REAR_VISE_OPEN_BIT]
        )

    def close_both_vises(self) -> bool:
        """Her iki mengene bitini kapatır (tek yazım)."""
        return self._write_register_atomic(
            self.CONTROL_REGISTER,
            set_bits=[],
            clear_bits=[self.REAR_VISE_OPEN_BIT, self.FRONT_VISE_OPEN_BIT]
        )

    def log_default_states(self) -> None:
        """
        Tanımlı tüm register ve bitlerin mevcut (default) değerlerini okur ve loglar.
        Donanıma herhangi bir yazma işlemi yapılmaz.
        """
        # Kontrol register'ı
        try:
            control_value_list = self.client.read_registers(self.CONTROL_REGISTER, 1)
            if control_value_list is None:
                self.logger.warning(f"CONTROL_REGISTER ({self.CONTROL_REGISTER}) okunamadı")
            else:
                control_value = control_value_list[0]
                self.logger.info(
                    f"CONTROL_REGISTER {self.CONTROL_REGISTER} raw=0x{control_value:04X} ({control_value})"
                )
                self.logger.info(
                    " - chip_cleaning(20.2): %s" % bool((control_value >> self.CHIP_CLEANING_BIT) & 1)
                )
                self.logger.info(
                    " - cutting_start(20.3): %s" % bool((control_value >> self.CUTTING_START_BIT) & 1)
                )
                self.logger.info(
                    " - cutting_stop(20.4): %s" % bool((control_value >> self.CUTTING_STOP_BIT) & 1)
                )
                self.logger.info(
                    " - rear_vise_open(20.5): %s" % bool((control_value >> self.REAR_VISE_OPEN_BIT) & 1)
                )
                self.logger.info(
                    " - front_vise_open(20.6): %s" % bool((control_value >> self.FRONT_VISE_OPEN_BIT) & 1)
                )
                self.logger.info(
                    " - material_forward(20.7): %s" % bool((control_value >> self.MATERIAL_FORWARD_BIT) & 1)
                )
                self.logger.info(
                    " - material_backward(20.8): %s" % bool((control_value >> self.MATERIAL_BACKWARD_BIT) & 1)
                )
                self.logger.info(
                    " - saw_up(20.9): %s" % bool((control_value >> self.SAW_UP_BIT) & 1)
                )
                self.logger.info(
                    " - saw_down(20.10): %s" % bool((control_value >> self.SAW_DOWN_BIT) & 1)
                )
        except Exception as e:
            self.logger.error(f"CONTROL_REGISTER okunurken hata: {e}")

        # Soğutma register'ı
        try:
            coolant_value_list = self.client.read_registers(self.COOLANT_REGISTER, 1)
            if coolant_value_list is None:
                self.logger.warning(f"COOLANT_REGISTER ({self.COOLANT_REGISTER}) okunamadı")
            else:
                coolant_value = coolant_value_list[0]
                self.logger.info(
                    f"COOLANT_REGISTER {self.COOLANT_REGISTER} raw=0x{coolant_value:04X} ({coolant_value})"
                )
                self.logger.info(
                    " - coolant(2000.1): %s" % bool((coolant_value >> self.COOLANT_BIT) & 1)
                )
        except Exception as e:
            self.logger.error(f"COOLANT_REGISTER okunurken hata: {e}")
    
    # Talaş temizlik fonksiyonları
    def start_chip_cleaning(self) -> bool:
        """Talaş temizliği başlatır"""
        return self._set_bit(self.KONVEYOR_REGISTER, self.CHIP_CLEANING_BIT, True)
    
    def stop_chip_cleaning(self) -> bool:
        """Talaş temizliği durdurur"""
        return self._set_bit(self.KONVEYOR_REGISTER, self.CHIP_CLEANING_BIT, False)
    
    def is_chip_cleaning_active(self) -> Optional[bool]:
        """Talaş temizliği aktif mi kontrol eder"""
        return self._get_bit(self.KONVEYOR_REGISTER, self.CHIP_CLEANING_BIT)
    
    # Kesim kontrol fonksiyonları
    def start_cutting(self) -> bool:
        """Kesim işlemini başlatır"""
        return self._set_bit(self.CONTROL_REGISTER, self.CUTTING_START_BIT, True)
    
    def stop_cutting(self) -> bool:
        """Kesim işlemini durdurur"""
        return self._set_bit(self.CONTROL_REGISTER, self.CUTTING_STOP_BIT, True)
    
    def is_cutting_active(self) -> Optional[bool]:
        """Kesim işlemi aktif mi kontrol eder"""
        return self._get_bit(self.CONTROL_REGISTER, self.CUTTING_START_BIT)
    
    # Mengene kontrol fonksiyonları
    def open_rear_vise(self) -> bool:
        """Arka mengeneyi açar"""
        return self._set_bit(self.CONTROL_REGISTER, self.REAR_VISE_OPEN_BIT, True)
    
    def close_rear_vise(self) -> bool:
        """Arka mengeneyi kapatır"""
        return self._set_bit(self.CONTROL_REGISTER, self.REAR_VISE_OPEN_BIT, False)
    
    def open_front_vise(self) -> bool:
        """Ön mengeneyi açar"""
        return self._set_bit(self.CONTROL_REGISTER, self.FRONT_VISE_OPEN_BIT, True)
    
    def close_front_vise(self) -> bool:
        """Ön mengeneyi kapatır"""
        return self._set_bit(self.CONTROL_REGISTER, self.FRONT_VISE_OPEN_BIT, False)
    
    def is_rear_vise_open(self) -> Optional[bool]:
        """Arka mengene açık mı kontrol eder"""
        return self._get_bit(self.CONTROL_REGISTER, self.REAR_VISE_OPEN_BIT)
    
    def is_front_vise_open(self) -> Optional[bool]:
        """Ön mengene açık mı kontrol eder"""
        return self._get_bit(self.CONTROL_REGISTER, self.FRONT_VISE_OPEN_BIT)
    
    # Malzeme konumlandırma fonksiyonları
    def move_material_forward(self) -> bool:
        """Malzemeyi öne sürer"""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_FORWARD_BIT, True)
    
    def stop_material_forward(self) -> bool:
        """Malzeme öne sürme işlemini durdurur"""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_FORWARD_BIT, False)
    
    def move_material_backward(self) -> bool:
        """Malzemeyi arkaya sürer"""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_BACKWARD_BIT, True)
    
    def stop_material_backward(self) -> bool:
        """Malzeme arkaya sürme işlemini durdurur"""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_BACKWARD_BIT, False)
    
    def is_material_moving_forward(self) -> Optional[bool]:
        """Malzeme öne doğru hareket ediyor mu kontrol eder"""
        return self._get_bit(self.CONTROL_REGISTER, self.MATERIAL_FORWARD_BIT)
    
    def is_material_moving_backward(self) -> Optional[bool]:
        """Malzeme arkaya doğru hareket ediyor mu kontrol eder"""
        return self._get_bit(self.CONTROL_REGISTER, self.MATERIAL_BACKWARD_BIT)
    
    # Testere konumlandırma fonksiyonları
    def move_saw_up(self) -> bool:
        """Testereyi yukarı kaldırır"""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_UP_BIT, True)
    
    def stop_saw_up(self) -> bool:
        """Testere yukarı hareket işlemini durdurur"""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_UP_BIT, False)
    
    def move_saw_down(self) -> bool:
        """Testereyi aşağı indirir"""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_DOWN_BIT, True)
    
    def stop_saw_down(self) -> bool:
        """Testere aşağı hareket işlemini durdurur"""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_DOWN_BIT, False)
    
    def is_saw_moving_up(self) -> Optional[bool]:
        """Testere yukarı hareket ediyor mu kontrol eder"""
        return self._get_bit(self.CONTROL_REGISTER, self.SAW_UP_BIT)
    
    def is_saw_moving_down(self) -> Optional[bool]:
        """Testere aşağı hareket ediyor mu kontrol eder"""
        return self._get_bit(self.CONTROL_REGISTER, self.SAW_DOWN_BIT)
    
    # Soğutma sıvısı kontrol fonksiyonları
    def start_coolant(self) -> bool:
        """Soğutma sıvısını başlatır"""
        return self._set_bit(self.COOLANT_REGISTER, self.COOLANT_BIT, True)
    
    def stop_coolant(self) -> bool:
        """Soğutma sıvısını durdurur"""
        return self._set_bit(self.COOLANT_REGISTER, self.COOLANT_BIT, False)
    
    def is_coolant_active(self) -> Optional[bool]:
        """Soğutma sıvısı aktif mi kontrol eder"""
        return self._get_bit(self.COOLANT_REGISTER, self.COOLANT_BIT)
    
    # Genel durum kontrolü
    def get_control_register_status(self) -> Optional[dict]:
        """
        Kontrol registerının tüm bit durumlarını döner
        
        Returns:
            Optional[dict]: Bit durumları sözlüğü veya None (hata durumunda)
        """
        try:
            current_value = self.client.read_registers(self.CONTROL_REGISTER, 1)
            if current_value is None:
                return None
                
            status = {
                'chip_cleaning': bool((current_value[0] >> self.CHIP_CLEANING_BIT) & 1),
                'cutting_start': bool((current_value[0] >> self.CUTTING_START_BIT) & 1),
                'cutting_stop': bool((current_value[0] >> self.CUTTING_STOP_BIT) & 1),
                'rear_vise_open': bool((current_value[0] >> self.REAR_VISE_OPEN_BIT) & 1),
                'front_vise_open': bool((current_value[0] >> self.FRONT_VISE_OPEN_BIT) & 1),
                'material_forward': bool((current_value[0] >> self.MATERIAL_FORWARD_BIT) & 1),
                'material_backward': bool((current_value[0] >> self.MATERIAL_BACKWARD_BIT) & 1),
                'saw_up': bool((current_value[0] >> self.SAW_UP_BIT) & 1),
                'saw_down': bool((current_value[0] >> self.SAW_DOWN_BIT) & 1)
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Kontrol register durumu okunamadı: {e}")
            return None
    
    def get_coolant_status(self) -> Optional[bool]:
        """
        Soğutma sıvısı durumunu döner
        
        Returns:
            Optional[bool]: Soğutma sıvısı durumu veya None (hata durumunda)
        """
        return self.is_coolant_active()
