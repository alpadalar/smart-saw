"""Tests for PageIndex IntEnum.

Verifies all 7 named page index constants, int subclass behavior,
and total member count.
"""

import pytest

from src.gui.page_index import PageIndex


def test_page_index_values():
    """All 7 PageIndex members must have their specified integer values."""
    assert PageIndex.KONTROL_PANELI == 0
    assert PageIndex.OTOMATIK_KESIM == 1
    assert PageIndex.KONUMLANDIRMA == 2
    assert PageIndex.SENSOR == 3
    assert PageIndex.IZLEME == 4
    assert PageIndex.ALARM == 5
    assert PageIndex.KAMERA == 6


def test_page_index_is_int():
    """All PageIndex members must be instances of int (IntEnum property)."""
    for member in PageIndex:
        assert isinstance(member, int), f"{member.name} is not an int instance"


def test_page_index_count():
    """PageIndex must have exactly 7 members."""
    assert len(PageIndex) == 7
