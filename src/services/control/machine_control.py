"""
Machine control module for positioning and vise operations.

This module controls specific registers and bits on the machine via Modbus.
Uses SYNCHRONOUS Modbus calls (like old project) for reliable Qt integration.
"""

import logging
import threading
import time
from typing import Optional

from pymodbus.client import ModbusTcpClient

logger = logging.getLogger(__name__)

# Connection settings
CONNECT_TIMEOUT = 1.0  # Connection timeout in seconds
CONNECT_COOLDOWN = 1.0  # Minimum seconds between connection attempts


class MachineControl:
    """
    Machine control class for positioning operations.

    Uses singleton pattern with synchronous Modbus calls.
    Controls specific registers and bits for:
    - Vise control (rear/front open/close)
    - Material positioning (forward/backward)
    - Saw positioning (up/down)
    - Cutting start/stop
    - Coolant control
    """

    _instance: Optional['MachineControl'] = None
    _lock = threading.Lock()

    # Register addresses
    CONTROL_REGISTER = 20
    COOLANT_REGISTER = 2000
    KONVEYOR_REGISTER = 102

    # Bit positions (0-based)
    CHIP_CLEANING_BIT = 3        # 102.3: Chip cleaning
    CUTTING_START_BIT = 3        # 20.3: Start cutting
    CUTTING_STOP_BIT = 4         # 20.4: Stop cutting
    REAR_VISE_OPEN_BIT = 5       # 20.5: Rear vise open
    FRONT_VISE_OPEN_BIT = 6      # 20.6: Front vise open
    MATERIAL_FORWARD_BIT = 7     # 20.7: Material forward
    MATERIAL_BACKWARD_BIT = 8    # 20.8: Material backward
    SAW_UP_BIT = 9               # 20.9: Saw up
    SAW_DOWN_BIT = 10            # 20.10: Saw down
    COOLANT_BIT = 1              # 2000.1: Coolant

    def __new__(cls, host: str = '192.168.2.147', port: int = 502):
        """Thread-safe singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, host: str = '192.168.2.147', port: int = 502):
        """Initialize MachineControl with Modbus connection."""
        if self._initialized:
            return

        with MachineControl._lock:
            if self._initialized:
                return

            self.host = host
            self.port = port
            self.client = ModbusTcpClient(
                host=host,
                port=port,
                timeout=CONNECT_TIMEOUT
            )
            self.connected = False

            # Connection cooldown tracking
            self._last_connect_attempt: float = 0

            # Try to connect (with cooldown tracking)
            try:
                self._last_connect_attempt = time.monotonic()
                self.connected = self.client.connect()
                if self.connected:
                    logger.info(f"MachineControl connected to {host}:{port}")
                else:
                    logger.warning(f"MachineControl failed to connect to {host}:{port}")
            except Exception as e:
                logger.error(f"MachineControl connection error: {e}")
                self.connected = False

            self._initialized = True

    @property
    def is_connected(self) -> bool:
        """Check if Modbus is connected."""
        try:
            return self.client.is_socket_open()
        except Exception:
            return False

    def _should_attempt_connect(self) -> bool:
        """Check if enough time has passed since last connection attempt."""
        elapsed = time.monotonic() - self._last_connect_attempt
        if elapsed >= CONNECT_COOLDOWN:
            return True
        logger.debug(
            f"MachineControl: Skipping connection attempt, cooldown active ({elapsed:.1f}s / {CONNECT_COOLDOWN:.1f}s)"
        )
        return False

    def _ensure_connected(self) -> bool:
        """Ensure Modbus connection is active."""
        try:
            if not self.client.is_socket_open():
                # Check cooldown before attempting reconnection
                if not self._should_attempt_connect():
                    return False  # Skip during cooldown
                self._last_connect_attempt = time.monotonic()
                self.connected = self.client.connect()
                if self.connected:
                    logger.info("MachineControl reconnected")
            return self.client.is_socket_open()
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            return False

    def _read_register(self, register: int) -> Optional[int]:
        """Read a single register (synchronous)."""
        try:
            if not self._ensure_connected():
                return None

            result = self.client.read_holding_registers(address=register, count=1)
            if result.isError():
                logger.error(f"Register read error ({register}): {result}")
                return None

            return result.registers[0]
        except Exception as e:
            logger.error(f"Register read exception ({register}): {e}")
            return None

    def _write_register(self, register: int, value: int) -> bool:
        """Write a single register (synchronous)."""
        try:
            if not self._ensure_connected():
                return False

            result = self.client.write_register(address=register, value=value)
            if result.isError():
                logger.error(f"Register write error ({register}): {result}")
                return False

            return True
        except Exception as e:
            logger.error(f"Register write exception ({register}): {e}")
            return False

    def _set_bit(self, register: int, bit_position: int, value: bool) -> bool:
        """Set a specific bit in a register."""
        try:
            current_value = self._read_register(register)
            if current_value is None:
                logger.error(f"Failed to read register {register}")
                return False

            bit_mask = 1 << bit_position

            if value:
                new_value = current_value | bit_mask
            else:
                new_value = current_value & ~bit_mask

            success = self._write_register(register, new_value)
            if success:
                logger.debug(f"Register {register}, bit {bit_position} set to {value}")
            else:
                logger.error(f"Failed to set register {register}, bit {bit_position}")

            return success

        except Exception as e:
            logger.error(f"Bit set error: {e}")
            return False

    def _get_bit(self, register: int, bit_position: int) -> Optional[bool]:
        """Get a specific bit value from a register."""
        try:
            current_value = self._read_register(register)
            if current_value is None:
                return None

            bit_value = (current_value >> bit_position) & 1
            return bool(bit_value)

        except Exception as e:
            logger.error(f"Bit read error: {e}")
            return None

    def _write_register_atomic(
        self,
        register: int,
        set_bits: list,
        clear_bits: list
    ) -> bool:
        """Atomically set and clear multiple bits in a single register write."""
        try:
            current_value = self._read_register(register)
            if current_value is None:
                logger.error(f"Failed to read register {register} (atomic)")
                return False

            new_value = current_value
            for b in set_bits:
                new_value |= (1 << b)
            for b in clear_bits:
                new_value &= ~(1 << b)

            if new_value == current_value:
                logger.debug(f"Register {register} no change needed (0x{current_value:04X})")
                return True

            success = self._write_register(register, new_value)
            if success:
                logger.info(f"Register {register} atomic write: 0x{current_value:04X} -> 0x{new_value:04X}")
            else:
                logger.error(f"Register {register} atomic write failed")

            return success

        except Exception as e:
            logger.error(f"Atomic write error: {e}")
            return False

    # ========================================================================
    # Vise Control (Mengene)
    # ========================================================================

    def open_rear_vise_exclusive(self) -> bool:
        """Open rear vise and close front vise (single write)."""
        return self._write_register_atomic(
            self.CONTROL_REGISTER,
            set_bits=[self.REAR_VISE_OPEN_BIT],
            clear_bits=[self.FRONT_VISE_OPEN_BIT]
        )

    def open_front_vise_exclusive(self) -> bool:
        """Open front vise and close rear vise (single write)."""
        return self._write_register_atomic(
            self.CONTROL_REGISTER,
            set_bits=[self.FRONT_VISE_OPEN_BIT],
            clear_bits=[self.REAR_VISE_OPEN_BIT]
        )

    def close_both_vises(self) -> bool:
        """Close both vises (single write)."""
        return self._write_register_atomic(
            self.CONTROL_REGISTER,
            set_bits=[],
            clear_bits=[self.REAR_VISE_OPEN_BIT, self.FRONT_VISE_OPEN_BIT]
        )

    def open_rear_vise(self) -> bool:
        """Open rear vise."""
        return self._set_bit(self.CONTROL_REGISTER, self.REAR_VISE_OPEN_BIT, True)

    def close_rear_vise(self) -> bool:
        """Close rear vise."""
        return self._set_bit(self.CONTROL_REGISTER, self.REAR_VISE_OPEN_BIT, False)

    def open_front_vise(self) -> bool:
        """Open front vise."""
        return self._set_bit(self.CONTROL_REGISTER, self.FRONT_VISE_OPEN_BIT, True)

    def close_front_vise(self) -> bool:
        """Close front vise."""
        return self._set_bit(self.CONTROL_REGISTER, self.FRONT_VISE_OPEN_BIT, False)

    def is_rear_vise_open(self) -> Optional[bool]:
        """Check if rear vise is open."""
        return self._get_bit(self.CONTROL_REGISTER, self.REAR_VISE_OPEN_BIT)

    def is_front_vise_open(self) -> Optional[bool]:
        """Check if front vise is open."""
        return self._get_bit(self.CONTROL_REGISTER, self.FRONT_VISE_OPEN_BIT)

    # ========================================================================
    # Material Positioning (Malzeme Konumlandırma)
    # ========================================================================

    def move_material_forward(self) -> bool:
        """Move material forward."""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_FORWARD_BIT, True)

    def stop_material_forward(self) -> bool:
        """Stop material forward movement."""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_FORWARD_BIT, False)

    def move_material_backward(self) -> bool:
        """Move material backward."""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_BACKWARD_BIT, True)

    def stop_material_backward(self) -> bool:
        """Stop material backward movement."""
        return self._set_bit(self.CONTROL_REGISTER, self.MATERIAL_BACKWARD_BIT, False)

    def is_material_moving_forward(self) -> Optional[bool]:
        """Check if material is moving forward."""
        return self._get_bit(self.CONTROL_REGISTER, self.MATERIAL_FORWARD_BIT)

    def is_material_moving_backward(self) -> Optional[bool]:
        """Check if material is moving backward."""
        return self._get_bit(self.CONTROL_REGISTER, self.MATERIAL_BACKWARD_BIT)

    # ========================================================================
    # Saw Positioning (Testere Konumlandırma)
    # ========================================================================

    def move_saw_up(self) -> bool:
        """Move saw up."""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_UP_BIT, True)

    def stop_saw_up(self) -> bool:
        """Stop saw upward movement."""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_UP_BIT, False)

    def move_saw_down(self) -> bool:
        """Move saw down."""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_DOWN_BIT, True)

    def stop_saw_down(self) -> bool:
        """Stop saw downward movement."""
        return self._set_bit(self.CONTROL_REGISTER, self.SAW_DOWN_BIT, False)

    def is_saw_moving_up(self) -> Optional[bool]:
        """Check if saw is moving up."""
        return self._get_bit(self.CONTROL_REGISTER, self.SAW_UP_BIT)

    def is_saw_moving_down(self) -> Optional[bool]:
        """Check if saw is moving down."""
        return self._get_bit(self.CONTROL_REGISTER, self.SAW_DOWN_BIT)

    # ========================================================================
    # Cutting Control (Kesim Kontrol)
    # ========================================================================

    def start_cutting(self) -> bool:
        """Start cutting operation."""
        return self._set_bit(self.CONTROL_REGISTER, self.CUTTING_START_BIT, True)

    def stop_cutting(self) -> bool:
        """Stop cutting operation."""
        return self._set_bit(self.CONTROL_REGISTER, self.CUTTING_STOP_BIT, True)

    def is_cutting_active(self) -> Optional[bool]:
        """Check if cutting is active."""
        return self._get_bit(self.CONTROL_REGISTER, self.CUTTING_START_BIT)

    # ========================================================================
    # Coolant Control (Soğutma Sıvısı)
    # ========================================================================

    def start_coolant(self) -> bool:
        """Start coolant."""
        return self._set_bit(self.COOLANT_REGISTER, self.COOLANT_BIT, True)

    def stop_coolant(self) -> bool:
        """Stop coolant."""
        return self._set_bit(self.COOLANT_REGISTER, self.COOLANT_BIT, False)

    def is_coolant_active(self) -> Optional[bool]:
        """Check if coolant is active."""
        return self._get_bit(self.COOLANT_REGISTER, self.COOLANT_BIT)

    # ========================================================================
    # Chip Cleaning (Talaş Temizlik)
    # ========================================================================

    def start_chip_cleaning(self) -> bool:
        """Start chip cleaning."""
        return self._set_bit(self.KONVEYOR_REGISTER, self.CHIP_CLEANING_BIT, True)

    def stop_chip_cleaning(self) -> bool:
        """Stop chip cleaning."""
        return self._set_bit(self.KONVEYOR_REGISTER, self.CHIP_CLEANING_BIT, False)

    def is_chip_cleaning_active(self) -> Optional[bool]:
        """Check if chip cleaning is active."""
        return self._get_bit(self.KONVEYOR_REGISTER, self.CHIP_CLEANING_BIT)

    # ========================================================================
    # Speed Control (Hız Kontrol)
    # ========================================================================

    # Speed register addresses
    CUTTING_SPEED_REGISTER = 2066  # Kesme hızı
    DESCENT_SPEED_REGISTER = 2041  # İnme hızı

    def write_cutting_speed(self, value: int) -> bool:
        """
        Write cutting speed to register 2066.

        Args:
            value: Speed value (direct integer, no conversion)

        Returns:
            True if successful
        """
        try:
            modbus_value = int(value)
            logger.debug(f"Writing cutting speed: {value} -> register {self.CUTTING_SPEED_REGISTER}")
            success = self._write_register(self.CUTTING_SPEED_REGISTER, modbus_value)
            if success:
                logger.info(f"Cutting speed set to {value}")
            return success
        except Exception as e:
            logger.error(f"Cutting speed write error: {e}")
            return False

    def write_descent_speed(self, value: float) -> bool:
        """
        Write descent speed to register 2041.

        Args:
            value: Speed value (will be multiplied by 100)

        Returns:
            True if successful
        """
        try:
            modbus_value = int(value * 100)
            logger.debug(f"Writing descent speed: {value} -> {modbus_value} (x100) -> register {self.DESCENT_SPEED_REGISTER}")
            success = self._write_register(self.DESCENT_SPEED_REGISTER, modbus_value)
            if success:
                logger.info(f"Descent speed set to {value} (modbus: {modbus_value})")
            return success
        except Exception as e:
            logger.error(f"Descent speed write error: {e}")
            return False

    def read_cutting_speed(self) -> Optional[int]:
        """Read current cutting speed from register 2066."""
        return self._read_register(self.CUTTING_SPEED_REGISTER)

    def read_descent_speed(self) -> Optional[float]:
        """Read current descent speed from register 2041 (divided by 100)."""
        raw = self._read_register(self.DESCENT_SPEED_REGISTER)
        if raw is not None:
            return raw / 100.0
        return None

    # ========================================================================
    # Status Methods
    # ========================================================================

    def get_control_register_status(self) -> Optional[dict]:
        """Get all bit statuses from control register."""
        try:
            current_value = self._read_register(self.CONTROL_REGISTER)
            if current_value is None:
                return None

            return {
                'chip_cleaning': bool((current_value >> self.CHIP_CLEANING_BIT) & 1),
                'cutting_start': bool((current_value >> self.CUTTING_START_BIT) & 1),
                'cutting_stop': bool((current_value >> self.CUTTING_STOP_BIT) & 1),
                'rear_vise_open': bool((current_value >> self.REAR_VISE_OPEN_BIT) & 1),
                'front_vise_open': bool((current_value >> self.FRONT_VISE_OPEN_BIT) & 1),
                'material_forward': bool((current_value >> self.MATERIAL_FORWARD_BIT) & 1),
                'material_backward': bool((current_value >> self.MATERIAL_BACKWARD_BIT) & 1),
                'saw_up': bool((current_value >> self.SAW_UP_BIT) & 1),
                'saw_down': bool((current_value >> self.SAW_DOWN_BIT) & 1)
            }

        except Exception as e:
            logger.error(f"Control register status error: {e}")
            return None
