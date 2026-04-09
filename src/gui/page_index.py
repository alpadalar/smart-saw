"""Page index constants for sidebar navigation."""

from enum import IntEnum


class PageIndex(IntEnum):
    """Named page indices for QStackedWidget navigation.

    Values must match the addWidget() insertion order in MainController._setup_ui().
    """
    KONTROL_PANELI = 0
    OTOMATIK_KESIM = 1
    KONUMLANDIRMA  = 2
    SENSOR         = 3
    IZLEME         = 4
    ALARM          = 5
    KAMERA         = 6
