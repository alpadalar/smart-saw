"""
AlarmController - Machine alarm monitoring page.

Monitors Modbus registers 1031 (fault status) and 1032 (alarm bitmask).
Persists alarms to SQLite, survives app restarts.
Auto-navigates to this page when a new alarm fires.

Page size: 1528x1080 (content area)
Framework: PySide6
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QFrame, QPushButton, QLabel, QTableWidget,
        QTableWidgetItem, QHeaderView, QAbstractItemView,
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QFont
except ImportError:
    logging.warning("PySide6 not installed")
    QWidget = object

logger = logging.getLogger(__name__)

# Alarm code bitmask → description (register 1032)
ALARM_CODES = {
    0x0001: "Acil Buton Basılı",
    0x0002: "Kesme Motor Arıza",
    0x0004: "Hidrolik Motor Arıza",
    0x0008: "Soğutma Motor Arıza",
    0x0010: "Konveyor Motor Arıza",
    0x0020: "Fırça Motor Arıza",
    0x0040: "Kasnak Kapak Açık",
    0x0080: "Şerit Kopma Arıza",
    0x0100: "Servo Motor Aşırı Yük",
    0x0200: "Servo Motor Yüksek Sıcaklık",
    0x0400: "Şerit Motor Arıza",
    0x0800: "Ölçü Hesap Hatası",
    0x1000: "Ön Mengene Hatası",
    0x2000: "Servo Hata Direnç",
}

DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "databases" / "current" / "alarm.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS alarm_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    code INTEGER NOT NULL,
    description TEXT NOT NULL,
    resolved_at TEXT
);
CREATE TABLE IF NOT EXISTS alarm_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class AlarmController(QWidget):
    """Machine alarm page with persistent alarm history."""

    def __init__(self, data_pipeline=None, parent=None, switch_page_callback=None):
        super().__init__(parent)
        self.data_pipeline = data_pipeline
        self._switch_page = switch_page_callback

        # Alarm tracking state
        self._prev_alarm_bits: int = 0
        self._active_alarm_ids: dict[int, int] = {}  # code → db row id

        # DB
        self._db = self._init_db()

        # UI
        self._setup_ui()
        self._setup_timers()
        self._reload_table()

        logger.info("AlarmController initialized")

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    @staticmethod
    def _init_db() -> sqlite3.Connection:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)
        conn.commit()
        return conn

    def _get_reset_timestamp(self) -> Optional[str]:
        row = self._db.execute(
            "SELECT value FROM alarm_config WHERE key='reset_timestamp'"
        ).fetchone()
        return row[0] if row else None

    def _set_reset_timestamp(self, ts: str):
        self._db.execute(
            "INSERT OR REPLACE INTO alarm_config (key, value) VALUES ('reset_timestamp', ?)",
            (ts,),
        )
        self._db.commit()

    def _insert_alarm(self, code: int, description: str) -> int:
        ts = datetime.now().isoformat(timespec="seconds")
        # Resolve any previous active alarms with the same code
        self._db.execute(
            "UPDATE alarm_events SET resolved_at=? WHERE code=? AND resolved_at IS NULL",
            (ts, code),
        )
        cur = self._db.execute(
            "INSERT INTO alarm_events (timestamp, code, description) VALUES (?, ?, ?)",
            (ts, code, description),
        )
        self._db.commit()
        return cur.lastrowid

    def _resolve_alarm(self, row_id: int):
        ts = datetime.now().isoformat(timespec="seconds")
        self._db.execute(
            "UPDATE alarm_events SET resolved_at=? WHERE id=?", (ts, row_id)
        )
        self._db.commit()

    def _fetch_visible_alarms(self) -> list[tuple]:
        reset_ts = self._get_reset_timestamp()
        if reset_ts:
            return self._db.execute(
                "SELECT id, timestamp, code, description, resolved_at "
                "FROM alarm_events WHERE timestamp >= ? ORDER BY id DESC",
                (reset_ts,),
            ).fetchall()
        return self._db.execute(
            "SELECT id, timestamp, code, description, resolved_at "
            "FROM alarm_events ORDER BY id DESC"
        ).fetchall()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.setMinimumSize(1528, 1080)
        self.setStyleSheet("background-color: transparent;")

        frame_style = """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                border-radius: 20px;
            }
        """
        title_style = (
            "background: transparent; color: #F4F6FC;"
            " font: bold 24px 'Plus Jakarta Sans';"
        )

        # Title frame
        self.titleFrame = QFrame(self)
        self.titleFrame.setGeometry(30, 127, 1468, 60)
        self.titleFrame.setStyleSheet(frame_style)

        self.labelTitle = QLabel("Makine Alarmları", self.titleFrame)
        self.labelTitle.setGeometry(20, 13, 400, 34)
        self.labelTitle.setStyleSheet(title_style)

        # Active alarm count
        self.labelActiveCount = QLabel("", self.titleFrame)
        self.labelActiveCount.setGeometry(900, 13, 540, 34)
        self.labelActiveCount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.labelActiveCount.setStyleSheet(
            "background: transparent; color: #DC2626;"
            " font: bold 20px 'Plus Jakarta Sans';"
        )

        # Alarm table
        self.tableAlarms = QTableWidget(self)
        self.tableAlarms.setGeometry(30, 200, 1468, 780)
        self.tableAlarms.setColumnCount(4)
        self.tableAlarms.setHorizontalHeaderLabels(
            ["Zaman", "Alarm Kodu", "Açıklama", "Durum"]
        )
        self.tableAlarms.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableAlarms.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableAlarms.verticalHeader().setVisible(False)

        header = self.tableAlarms.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.tableAlarms.setColumnWidth(0, 200)
        self.tableAlarms.setColumnWidth(1, 160)
        self.tableAlarms.setColumnWidth(3, 180)

        table_style = """
            QTableWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-size: 18px;
                border: none;
                border-radius: 20px;
                gridline-color: rgba(244, 246, 252, 30);
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 11, 38, 240),
                    stop:1 rgba(26, 31, 55, 0)
                );
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 18px;
                border: none;
                padding: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(26, 31, 55, 100);
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #950952;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        self.tableAlarms.setStyleSheet(table_style)

        # Reset button
        self.btnReset = QPushButton("Alarmları Sıfırla", self)
        self.btnReset.setGeometry(30, 995, 300, 60)
        self.btnReset.setCursor(Qt.PointingHandCursor)
        self.btnReset.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000000, stop:0.38 rgba(26, 31, 55, 200)
                );
                color: #F4F6FC;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 20px;
                border-radius: 20px;
                border: 2px solid #F4F6FC;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.btnReset.clicked.connect(self._on_reset_clicked)

    # ------------------------------------------------------------------
    # Timers
    # ------------------------------------------------------------------

    def _setup_timers(self):
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(500)  # 2 Hz
        self._poll_timer.timeout.connect(self._poll_alarms)
        self._poll_timer.start()

    def stop_timers(self):
        try:
            if hasattr(self, "_poll_timer") and self._poll_timer:
                self._poll_timer.stop()
        except Exception as e:
            logger.error(f"Error stopping alarm timers: {e}")

    # ------------------------------------------------------------------
    # Alarm polling
    # ------------------------------------------------------------------

    def _poll_alarms(self):
        try:
            if not self.data_pipeline or not hasattr(self.data_pipeline, "get_latest_data"):
                return
            data = self.data_pipeline.get_latest_data()
            if not data:
                return

            alarm_status = int(data.get("alarm_status", 0))
            alarm_raw = data.get("alarm_bilgisi", "0x0000")
            if isinstance(alarm_raw, str):
                alarm_bits = int(alarm_raw, 16)
            else:
                alarm_bits = int(alarm_raw)

            if alarm_status == 0:
                # No fault — resolve any active alarms
                if self._active_alarm_ids:
                    for code, row_id in list(self._active_alarm_ids.items()):
                        self._resolve_alarm(row_id)
                    self._active_alarm_ids.clear()
                    self._reload_table()
                self._prev_alarm_bits = 0
                return

            # Fault active — check for new alarm bits
            new_bits = alarm_bits & ~self._prev_alarm_bits
            if new_bits:
                for mask, desc in ALARM_CODES.items():
                    if new_bits & mask:
                        row_id = self._insert_alarm(mask, desc)
                        self._active_alarm_ids[mask] = row_id

                self._reload_table()

                # Auto-navigate to alarm page
                if self._switch_page:
                    from ..page_index import PageIndex
                    self._switch_page(PageIndex.ALARM)

            # Check for cleared bits (resolved while fault still active)
            cleared_bits = self._prev_alarm_bits & ~alarm_bits
            if cleared_bits:
                for mask in list(self._active_alarm_ids.keys()):
                    if cleared_bits & mask:
                        self._resolve_alarm(self._active_alarm_ids.pop(mask))
                self._reload_table()

            self._prev_alarm_bits = alarm_bits

        except Exception as e:
            logger.error(f"Alarm poll error: {e}")

    # ------------------------------------------------------------------
    # Table display
    # ------------------------------------------------------------------

    def _reload_table(self):
        try:
            rows = self._fetch_visible_alarms()
            self.tableAlarms.setRowCount(len(rows))

            active_count = 0
            font_normal = QFont("Plus Jakarta Sans", 16)
            font_bold = QFont("Plus Jakarta Sans", 16, QFont.Bold)

            for i, (row_id, ts, code, desc, resolved_at) in enumerate(rows):
                is_active = resolved_at is None
                if is_active:
                    active_count += 1

                color = QColor("#DC2626") if is_active else QColor("#F4F6FC")
                font = font_bold if is_active else font_normal
                status_text = "AKTİF" if is_active else "Çözüldü"

                ts_display = ts.replace("T", " ") if ts else ""
                code_hex = f"0x{code:04X}"

                for col, text in enumerate([ts_display, code_hex, desc, status_text]):
                    item = QTableWidgetItem(text)
                    item.setForeground(color)
                    item.setFont(font)
                    self.tableAlarms.setItem(i, col, item)

                self.tableAlarms.setRowHeight(i, 48)

            if active_count > 0:
                self.labelActiveCount.setText(f"{active_count} aktif alarm")
            else:
                self.labelActiveCount.setText("")

        except Exception as e:
            logger.error(f"Alarm table reload error: {e}")

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def _on_reset_clicked(self):
        ts = datetime.now().isoformat(timespec="seconds")
        self._set_reset_timestamp(ts)

        # Resolve all currently active alarms in DB
        for code, row_id in list(self._active_alarm_ids.items()):
            self._resolve_alarm(row_id)

        # Reset tracking so polling re-detects current alarms as new
        self._active_alarm_ids.clear()
        self._prev_alarm_bits = 0

        # Force immediate re-poll to pick up still-active alarms
        self._poll_alarms()

        self._reload_table()
        logger.info(f"Alarm display reset at {ts}")
