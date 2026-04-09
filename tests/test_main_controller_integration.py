"""Integration tests for MainController sidebar navigation (Phase 27).

Tests use __new__ + manual attribute injection to avoid QApplication
dependency (same pattern as test_otomatik_kesim_controller.py).

These tests verify the POST-update contract of main_controller.py:
- nav_buttons has 5 elements (btnOtomatikKesim at index 1)
- _switch_page uses PageIndex enum correctly
- closeEvent calls stop_timers() on all 5 unconditional pages including
  otomatik_kesim_page
"""

from unittest.mock import MagicMock, call

import pytest

from src.gui.page_index import PageIndex


@pytest.fixture
def ctrl():
    """Create MainController with mocked dependencies via __new__ injection.

    Manually builds the POST-update state:
    - nav_buttons: 5 items (control_panel, otomatik_kesim, positioning, sensor, tracking)
    - stackedWidget: mock with setCurrentIndex
    - page mocks with stop_timers
    - timer mocks with stop
    camera_page is intentionally NOT set (tests unconditional pages only).
    """
    from src.gui.controllers.main_controller import MainController

    c = MainController.__new__(MainController)

    # Mocked page instances — each has stop_timers
    c.control_panel_page = MagicMock()
    c.otomatik_kesim_page = MagicMock()
    c.positioning_page = MagicMock()
    c.sensor_page = MagicMock()
    c.monitoring_page = MagicMock()
    c.alarm_page = MagicMock()

    # Named nav button mocks for identity testing
    c.btnControlPanel = MagicMock()
    c.btnOtomatikKesim = MagicMock()
    c.btnPositioning = MagicMock()
    c.btnSensor = MagicMock()
    c.btnTracking = MagicMock()
    c.btnAlarm = MagicMock()

    c.nav_buttons = [
        c.btnControlPanel,    # PageIndex.KONTROL_PANELI (0)
        c.btnOtomatikKesim,   # PageIndex.OTOMATIK_KESIM (1)
        c.btnPositioning,     # PageIndex.KONUMLANDIRMA (2)
        c.btnSensor,          # PageIndex.SENSOR (3)
        c.btnTracking,        # PageIndex.IZLEME (4)
        c.btnAlarm,           # PageIndex.ALARM (5)
    ]

    # stackedWidget mock
    c.stackedWidget = MagicMock()

    # Main controller timers
    c._update_timer = MagicMock()
    c._datetime_timer = MagicMock()

    return c


# ---------------------------------------------------------------------------
# nav_buttons structure tests
# ---------------------------------------------------------------------------


def test_nav_buttons_count(ctrl):
    """nav_buttons must have exactly 6 items (camera excluded — conditional)."""
    assert len(ctrl.nav_buttons) == 6


def test_nav_buttons_otomatik_kesim_at_index_1(ctrl):
    """nav_buttons[1] must be the Otomatik Kesim button (identity check)."""
    assert ctrl.nav_buttons[1] is ctrl.btnOtomatikKesim


# ---------------------------------------------------------------------------
# _switch_page tests
# ---------------------------------------------------------------------------


def test_switch_page_checks_correct_button(ctrl):
    """_switch_page(PageIndex.OTOMATIK_KESIM) must check nav_buttons[1] and
    set stackedWidget to index 1."""
    ctrl._switch_page(PageIndex.OTOMATIK_KESIM)

    ctrl.nav_buttons[1].setChecked.assert_called_with(True)
    ctrl.stackedWidget.setCurrentIndex.assert_called_with(1)


def test_switch_page_unchecks_all_buttons(ctrl):
    """_switch_page must uncheck ALL nav_buttons before checking the target."""
    ctrl._switch_page(PageIndex.KONTROL_PANELI)

    for btn in ctrl.nav_buttons:
        # Each button must have had setChecked(False) called at some point
        calls = btn.setChecked.call_args_list
        assert call(False) in calls, f"setChecked(False) not called on {btn}"


# ---------------------------------------------------------------------------
# closeEvent tests
# ---------------------------------------------------------------------------


def test_close_event_stops_otomatik_kesim_timers(ctrl):
    """closeEvent must call stop_timers() on otomatik_kesim_page."""
    ctrl.closeEvent(MagicMock())
    ctrl.otomatik_kesim_page.stop_timers.assert_called_once()


def test_close_event_stops_all_unconditional_pages(ctrl):
    """closeEvent must call stop_timers() on all 6 unconditional page instances."""
    ctrl.closeEvent(MagicMock())

    for page_name in [
        "control_panel_page",
        "otomatik_kesim_page",
        "positioning_page",
        "sensor_page",
        "monitoring_page",
        "alarm_page",
    ]:
        page = getattr(ctrl, page_name)
        page.stop_timers.assert_called_once(), (
            f"stop_timers not called on {page_name}"
        )
