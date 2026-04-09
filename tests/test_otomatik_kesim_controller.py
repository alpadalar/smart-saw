"""Unit tests for OtomatikKesimController (Phase 26).

Tests use __new__ + manual attribute injection to avoid QApplication
dependency (same pattern as test_machine_control_auto_cutting.py).
"""

from unittest.mock import MagicMock

import pytest

from src.domain.enums import ControlMode


async def _noop_coro(*args, **kwargs):
    """No-op coroutine for mocking async set_mode calls."""


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def controller():
    """Create OtomatikKesimController with mocked dependencies.

    Uses __new__ + manual attribute injection to avoid requiring a running
    QApplication (and the full PySide6 widget hierarchy).
    """
    from src.gui.controllers.otomatik_kesim_controller import OtomatikKesimController

    ctrl = OtomatikKesimController.__new__(OtomatikKesimController)

    # Dependencies — control_manager.set_mode must return a real coroutine so
    # asyncio.run_coroutine_threadsafe does not raise TypeError
    ctrl.control_manager = MagicMock()
    ctrl.control_manager.set_mode.side_effect = lambda mode: _noop_coro(mode)
    ctrl.data_pipeline = None
    ctrl.event_loop = MagicMock()
    ctrl.machine_control = MagicMock()

    # Parameter state
    ctrl._p_value = ""
    ctrl._x_value = ""
    ctrl._l_value = ""
    ctrl._c_value = ""
    ctrl._s_value = ""

    # Control state
    ctrl._params_enabled = True
    ctrl._cutting_active = False
    ctrl._previous_count = None
    ctrl._reset_in_progress = False
    ctrl._reset_start = 0.0
    ctrl._reset_progress = 0.0

    # Timers
    ctrl._polling_timer = MagicMock()
    ctrl._reset_tick_timer = MagicMock()

    # UI widgets (all mocked)
    ctrl.labelCounter = MagicMock()
    ctrl.labelTotal = MagicMock()
    ctrl.labelComplete = MagicMock()
    ctrl.progressWidget = MagicMock()
    ctrl.progressWidget._progress = 0.0
    ctrl.progressWidget._complete = False
    ctrl.btnStart = MagicMock()
    ctrl.btnReset = MagicMock()
    ctrl.btnManual = MagicMock()
    ctrl.btnAI = MagicMock()
    ctrl.labelValidationError = MagicMock()
    ctrl.frameP = MagicMock()
    ctrl.frameX = MagicMock()
    ctrl.frameL = MagicMock()
    ctrl.frameC = MagicMock()
    ctrl.frameS = MagicMock()
    ctrl.labelPValue = MagicMock()
    ctrl.labelXValue = MagicMock()
    ctrl.labelLValue = MagicMock()
    ctrl.labelCValue = MagicMock()
    ctrl.labelSValue = MagicMock()

    # Mock _set_params_enabled at fixture level so tests that call
    # _on_polling_timer without explicitly re-mocking it don't fail due to
    # missing _frame_style Qt style strings.  Tests that need to assert on
    # _set_params_enabled re-assign it with a fresh MagicMock().
    ctrl._set_params_enabled = MagicMock(side_effect=lambda enabled: setattr(ctrl, "_params_enabled", enabled))

    return ctrl


# ---------------------------------------------------------------------------
# Validation tests (D-09)
# ---------------------------------------------------------------------------


def test_validate_params_missing_p(controller):
    """_validate_params returns Turkish error when P is empty."""
    controller._p_value = ""
    controller._l_value = "100.0"
    controller._x_value = "5"
    assert controller._validate_params() == "P (hedef adet) girilmedi"


def test_validate_params_missing_l(controller):
    """_validate_params returns Turkish error when L is empty."""
    controller._p_value = "10"
    controller._l_value = ""
    controller._x_value = "5"
    assert controller._validate_params() == "L (uzunluk) girilmedi"


def test_validate_params_missing_x(controller):
    """_validate_params returns Turkish error when X is empty."""
    controller._p_value = "10"
    controller._l_value = "100.0"
    controller._x_value = ""
    assert controller._validate_params() == "X (paketteki adet) girilmedi"


def test_validate_params_valid(controller):
    """_validate_params returns None when all mandatory params are present."""
    controller._p_value = "10"
    controller._l_value = "500.0"
    controller._x_value = "5"
    assert controller._validate_params() is None


# ---------------------------------------------------------------------------
# Counter and polling tests (D-13, D-14, D-15)
# ---------------------------------------------------------------------------


def test_counter_label_format(controller):
    """_on_polling_timer with count=3, target=10 sets labelCounter to '3 / 10'."""
    controller._p_value = "10"
    controller._x_value = "1"
    controller.machine_control.read_kesilmis_adet.return_value = 3
    controller._on_polling_timer()
    controller.labelCounter.setText.assert_called_with("3 / 10")


def test_params_disabled_during_cut(controller):
    """_on_polling_timer with count=3 (>0, < target) disables param frames."""
    controller._p_value = "10"
    controller._x_value = "1"
    controller.machine_control.read_kesilmis_adet.return_value = 3
    controller._set_params_enabled = MagicMock()
    controller._on_polling_timer()
    controller._set_params_enabled.assert_called_with(False)


def test_params_enabled_when_idle(controller):
    """_on_polling_timer with count=0 enables param frames."""
    controller._p_value = "10"
    controller._x_value = "1"
    controller.machine_control.read_kesilmis_adet.return_value = 0
    controller._set_params_enabled = MagicMock()
    controller._on_polling_timer()
    controller._set_params_enabled.assert_called_with(True)


def test_cutting_complete(controller):
    """_on_polling_timer with count >= target calls _on_cutting_complete."""
    controller._p_value = "5"
    controller._x_value = "2"
    controller.machine_control.read_kesilmis_adet.return_value = 10  # 5*2 = target
    controller._on_cutting_complete = MagicMock()
    controller._on_polling_timer()
    controller._on_cutting_complete.assert_called_once()


def test_polling_skips_when_no_machine_control(controller):
    """_on_polling_timer returns early when machine_control is None."""
    controller.machine_control = None
    controller._on_polling_timer()  # Should not raise
    controller.labelCounter.setText.assert_not_called()


def test_polling_skips_when_read_returns_none(controller):
    """_on_polling_timer returns early when read_kesilmis_adet returns None."""
    controller._p_value = "10"
    controller._x_value = "1"
    controller.machine_control.read_kesilmis_adet.return_value = None
    controller._on_polling_timer()
    controller.labelCounter.setText.assert_not_called()


# ---------------------------------------------------------------------------
# ML mode tests (D-16, D-17, D-18)
# ---------------------------------------------------------------------------


def test_ml_mode_toggle(controller):
    """_switch_to_mode(ControlMode.ML) checks btnAI and unchecks btnManual."""
    controller._switch_to_mode(ControlMode.ML)
    controller.btnAI.setChecked.assert_called_with(True)
    controller.btnManual.setChecked.assert_called_with(False)


def test_manual_mode_toggle(controller):
    """_switch_to_mode(ControlMode.MANUAL) checks btnManual and unchecks btnAI."""
    controller._switch_to_mode(ControlMode.MANUAL)
    controller.btnManual.setChecked.assert_called_with(True)
    controller.btnAI.setChecked.assert_called_with(False)


def test_ml_reset_on_count_decrease(controller):
    """_on_polling_timer triggers _trigger_ml_state_reset when count decreases."""
    controller._previous_count = 10
    controller._p_value = "20"
    controller._x_value = "1"
    controller.machine_control.read_kesilmis_adet.return_value = 1  # decreased
    controller._trigger_ml_state_reset = MagicMock()
    controller._on_polling_timer()
    controller._trigger_ml_state_reset.assert_called_once()


def test_ml_no_reset_on_first_poll(controller):
    """First poll (previous_count=None) does NOT trigger ML reset (Pitfall 4)."""
    controller._previous_count = None  # first poll
    controller._p_value = "20"
    controller._x_value = "1"
    controller.machine_control.read_kesilmis_adet.return_value = 5
    controller._trigger_ml_state_reset = MagicMock()
    controller._on_polling_timer()
    controller._trigger_ml_state_reset.assert_not_called()


def test_ml_no_reset_on_count_increase(controller):
    """Count increase (normal cutting) does NOT trigger ML reset."""
    controller._previous_count = 3
    controller._p_value = "20"
    controller._x_value = "1"
    controller.machine_control.read_kesilmis_adet.return_value = 5  # increased
    controller._trigger_ml_state_reset = MagicMock()
    controller._on_polling_timer()
    controller._trigger_ml_state_reset.assert_not_called()


def test_ml_no_reset_when_count_zero(controller):
    """Count decrease to zero (idle) does NOT trigger ML reset."""
    controller._previous_count = 5
    controller._p_value = "20"
    controller._x_value = "1"
    # count=0 means not cutting (count > 0 guard in condition)
    controller.machine_control.read_kesilmis_adet.return_value = 0
    controller._trigger_ml_state_reset = MagicMock()
    controller._on_polling_timer()
    controller._trigger_ml_state_reset.assert_not_called()


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


def test_total_label_recalc(controller):
    """_update_total_label with P=5, X=10 shows 'Toplam: 50 adet'."""
    controller._p_value = "5"
    controller._x_value = "10"
    controller._update_total_label()
    controller.labelTotal.setText.assert_called_with("Toplam: 50 adet")


def test_get_target(controller):
    """_get_target with P=5, X=10 returns 50."""
    controller._p_value = "5"
    controller._x_value = "10"
    assert controller._get_target() == 50


def test_get_target_empty(controller):
    """_get_target returns 0 when P or X is empty."""
    controller._p_value = ""
    controller._x_value = ""
    assert controller._get_target() == 0


def test_get_target_partial_empty(controller):
    """_get_target returns 0 when only one value is set."""
    controller._p_value = "5"
    controller._x_value = ""
    assert controller._get_target() == 0
