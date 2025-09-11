from typing import Optional, Tuple
import time
from core.logger import logger
from core.constants import (
    KESME_HIZI_REGISTER_ADDRESS,
    INME_HIZI_REGISTER_ADDRESS,
)


def read_band_speeds(modbus_client) -> Optional[Tuple[float, float]]:
    """
    Kesme hızı ve inme hızı register'larını okuyup ölçekleyerek döner.

    Returns:
        Optional[Tuple[float, float]]: (cutting_speed, descent_speed)
            cutting_speed: mm/s
            descent_speed: mm/s
        Hata durumunda None döner.
    """
    try:
        if not modbus_client or not getattr(modbus_client, 'is_connected', False):
            logger.debug("Modbus bağlantısı yok (speed_reader)")
            return None

        start_time = time.time()

        # Kesme hızı oku (2066), ölçek: /10
        cut_regs = modbus_client.read_registers(address=KESME_HIZI_REGISTER_ADDRESS, count=1)
        # İnme hızı oku (2041), ölçek: /100
        desc_regs = modbus_client.read_registers(address=INME_HIZI_REGISTER_ADDRESS, count=1)

        read_ms = (time.time() - start_time) * 1000.0

        if not cut_regs or not desc_regs:
            logger.debug(
                f"Hız registerları okunamadı (cut:{bool(cut_regs)} desc:{bool(desc_regs)}). Süre: {read_ms:.1f}ms"
            )
            return None

        raw_cut = cut_regs[0]
        raw_desc = desc_regs[0]

        try:
            cutting_speed = float(raw_cut) / 1.0
        except Exception:
            cutting_speed = 0.0

        try:
            descent_speed = float(raw_desc) / 100.0
        except Exception:
            descent_speed = 0.0

        # Negatif veya aşırı değerleri filtrele
        if cutting_speed < 0:
            cutting_speed = 0.0
        if descent_speed < 0:
            descent_speed = 0.0

        logger.debug(
            f"Register hızları okundu: kesme={cutting_speed:.2f} mm/s, inme={descent_speed:.2f} mm/s (Süre: {read_ms:.1f}ms)"
        )

        return cutting_speed, descent_speed

    except Exception as e:
        logger.error(f"Hız register okuma hatası: {e}")
        return None


