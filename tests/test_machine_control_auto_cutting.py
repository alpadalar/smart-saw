"""Unit tests for MachineControl auto cutting methods (Phase 25)."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.control.machine_control import MachineControl


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset MachineControl singleton between tests."""
    MachineControl._instance = None
    yield
    MachineControl._instance = None


def _make_connected_mc(mock_client_class):
    """Create MachineControl with a mocked, connected ModbusTcpClient."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.connect.return_value = True
    mock_client.is_socket_open.return_value = True
    return mock_client


# ---------------------------------------------------------------------------
# PLC-04: _write_double_word (FC16 double-word write)
# ---------------------------------------------------------------------------


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_write_double_word_fc16(mock_client_class):
    """_write_double_word(2064, 10000) calls write_registers(address=2064, values=[0x2710, 0x0000])."""
    mock_client = _make_connected_mc(mock_client_class)
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    mock_client.write_registers.return_value = mock_result

    mc = MachineControl()
    result = mc._write_double_word(2064, 10000)

    mock_client.write_registers.assert_called_once_with(
        address=2064, values=[0x2710, 0x0000]
    )
    assert result is True


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_write_double_word_large_value(mock_client_class):
    """_write_double_word(2064, 1000000) calls write_registers(address=2064, values=[0x4240, 0x000F])."""
    mock_client = _make_connected_mc(mock_client_class)
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    mock_client.write_registers.return_value = mock_result

    mc = MachineControl()
    result = mc._write_double_word(2064, 1000000)

    # 1000000 = 0x000F4240: low = 0x4240, high = 0x000F
    mock_client.write_registers.assert_called_once_with(
        address=2064, values=[0x4240, 0x000F]
    )
    assert result is True


# ---------------------------------------------------------------------------
# PLC-01: write_target_adet (FC6 single word write to D2050)
# ---------------------------------------------------------------------------


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_write_target_adet(mock_client_class):
    """write_target_adet(5, 10) calls write_register(address=2050, value=50)."""
    mock_client = _make_connected_mc(mock_client_class)
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    mock_client.write_register.return_value = mock_result

    mc = MachineControl()
    result = mc.write_target_adet(5, 10)

    mock_client.write_register.assert_called_once_with(address=2050, value=50)
    assert result is True


# ---------------------------------------------------------------------------
# PLC-02: write_target_uzunluk (FC16 double-word to D2064/D2065)
# ---------------------------------------------------------------------------


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_write_target_uzunluk_word_order(mock_client_class):
    """write_target_uzunluk(1000.0) calls write_registers(address=2064, values=[0x2710, 0x0000])."""
    mock_client = _make_connected_mc(mock_client_class)
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    mock_client.write_registers.return_value = mock_result

    mc = MachineControl()
    result = mc.write_target_uzunluk(1000.0)

    # 1000mm * 10 = 10000 = 0x2710; D2064=0x2710 (low), D2065=0x0000 (high)
    mock_client.write_registers.assert_called_once_with(
        address=2064, values=[0x2710, 0x0000]
    )
    assert result is True


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_write_target_uzunluk_float_rounding(mock_client_class):
    """write_target_uzunluk(100.3) results in value 1003 (round handles float imprecision)."""
    mock_client = _make_connected_mc(mock_client_class)
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    mock_client.write_registers.return_value = mock_result

    mc = MachineControl()
    mc.write_target_uzunluk(100.3)

    # 100.3 * 10 = 1003.0 (with float drift could be 1002.9999...), round() gives 1003
    # 1003 = 0x000003EB: low = 0x03EB, high = 0x0000
    call_args = mock_client.write_registers.call_args
    values = call_args[1]["values"]
    assert values[0] == 1003  # low word = 1003 (no overflow into high word)
    assert values[1] == 0x0000  # high word = 0


# ---------------------------------------------------------------------------
# PLC-03: read_kesilmis_adet (D2056 Word read)
# ---------------------------------------------------------------------------


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_read_kesilmis_adet(mock_client_class):
    """read_kesilmis_adet() calls read_holding_registers(address=2056, count=1) and returns value."""
    mock_client = _make_connected_mc(mock_client_class)
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    mock_result.registers = [42]
    mock_client.read_holding_registers.return_value = mock_result

    mc = MachineControl()
    value = mc.read_kesilmis_adet()

    mock_client.read_holding_registers.assert_called_once_with(address=2056, count=1)
    assert value == 42


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_read_kesilmis_adet_disconnected(mock_client_class):
    """read_kesilmis_adet() returns None when connection fails."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.connect.return_value = False
    mock_client.is_socket_open.return_value = False

    mc = MachineControl()
    value = mc.read_kesilmis_adet()

    assert value is None


# ---------------------------------------------------------------------------
# CTRL-01: start_auto_cutting (bit 20.13 set)
# ---------------------------------------------------------------------------


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_start_auto_cutting(mock_client_class):
    """start_auto_cutting() reads register 20, sets bit 13, writes back (0x2000)."""
    mock_client = _make_connected_mc(mock_client_class)

    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [0x0000]
    mock_client.read_holding_registers.return_value = read_result

    write_result = MagicMock()
    write_result.isError.return_value = False
    mock_client.write_register.return_value = write_result

    mc = MachineControl()
    result = mc.start_auto_cutting()

    # bit 13 = 1 << 13 = 8192 = 0x2000
    mock_client.write_register.assert_called_once_with(address=20, value=0x2000)
    assert result is True


# ---------------------------------------------------------------------------
# CTRL-02: reset_auto_cutting (bit 20.14 set/clear)
# ---------------------------------------------------------------------------


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_reset_auto_cutting_active(mock_client_class):
    """reset_auto_cutting(True) reads register 20, sets bit 14, writes back (0x4000)."""
    mock_client = _make_connected_mc(mock_client_class)

    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [0x0000]
    mock_client.read_holding_registers.return_value = read_result

    write_result = MagicMock()
    write_result.isError.return_value = False
    mock_client.write_register.return_value = write_result

    mc = MachineControl()
    result = mc.reset_auto_cutting(True)

    # bit 14 = 1 << 14 = 16384 = 0x4000
    mock_client.write_register.assert_called_once_with(address=20, value=0x4000)
    assert result is True


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_reset_auto_cutting_release(mock_client_class):
    """reset_auto_cutting(False) reads register 20 (bit 14 set), clears bit 14, writes back (0x0000)."""
    mock_client = _make_connected_mc(mock_client_class)

    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [0x4000]  # bit 14 already set
    mock_client.read_holding_registers.return_value = read_result

    write_result = MagicMock()
    write_result.isError.return_value = False
    mock_client.write_register.return_value = write_result

    mc = MachineControl()
    result = mc.reset_auto_cutting(False)

    # Clear bit 14: 0x4000 & ~0x4000 = 0x0000
    mock_client.write_register.assert_called_once_with(address=20, value=0x0000)
    assert result is True


# ---------------------------------------------------------------------------
# CTRL-03: cancel_auto_cutting (bit 20.4 set -- reuses CUTTING_STOP_BIT)
# ---------------------------------------------------------------------------


@patch("src.services.control.machine_control.ModbusTcpClient")
def test_cancel_auto_cutting(mock_client_class):
    """cancel_auto_cutting() reads register 20, sets bit 4 (CUTTING_STOP_BIT), writes back (0x0010)."""
    mock_client = _make_connected_mc(mock_client_class)

    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [0x0000]
    mock_client.read_holding_registers.return_value = read_result

    write_result = MagicMock()
    write_result.isError.return_value = False
    mock_client.write_register.return_value = write_result

    mc = MachineControl()
    result = mc.cancel_auto_cutting()

    # bit 4 = 1 << 4 = 16 = 0x0010
    mock_client.write_register.assert_called_once_with(address=20, value=0x0010)
    assert result is True
