"""
Camera page controller for Smart Band Saw.

Displays live camera feed, broken/crack detection panels, sequential
thumbnails, wear percentage, health score, and status — all driven
by three QTimers reading from CameraResultsStore.snapshot().

Page size: 1528×1080 (content area)
Framework: PySide6
"""

import logging
from collections import deque

from PySide6.QtWidgets import QWidget, QFrame, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap, QFont, QColor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared style constants
# ---------------------------------------------------------------------------

_FRAME_STYLE = """
    QFrame {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(6, 11, 38, 240),
            stop:1 rgba(26, 31, 55, 0)
        );
        border-radius: 15px;
    }
"""

_TITLE_STYLE = """
    QLabel {
        color: #F4F6FC;
        font-family: 'Plus Jakarta Sans';
        font-weight: bold;
        font-size: 22px;
        background-color: transparent;
    }
"""

_VALUE_STYLE = """
    QLabel {
        color: #F4F6FC;
        font-family: 'Plus Jakarta Sans';
        font-weight: bold;
        font-size: 32px;
        background-color: transparent;
    }
"""

_SUBTITLE_STYLE = """
    QLabel {
        color: rgba(244, 246, 252, 151);
        font-family: 'Plus Jakarta Sans';
        font-weight: medium;
        font-size: 16px;
        background-color: transparent;
    }
"""

_INFO_STYLE = """
    QLabel {
        color: rgba(244, 246, 252, 120);
        font-family: 'Plus Jakarta Sans';
        font-size: 14px;
        background-color: transparent;
    }
"""


class CameraController(QWidget):
    """Camera page widget — lives inside MainController's QStackedWidget.

    Reads exclusively from *results_store* via three QTimers:
      - 500 ms  — frame + thumbnails
      - 1000 ms — detection stats
      - 2000 ms — health / wear
    """

    # Max thumbnails displayed in the sequential strip
    _MAX_THUMBNAILS = 4
    _THUMB_W = 220
    _THUMB_H = 140

    def __init__(self, results_store, parent=None):
        super().__init__(parent)
        self.results_store = results_store

        # Thumbnail history (most-recent on the right)
        self._thumb_pixmaps: deque[QPixmap] = deque(maxlen=self._MAX_THUMBNAILS)

        self._setup_ui()
        self._setup_timers()

        logger.info("CameraController initialized")

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        """Build the entire camera page — programmatic layout, no .ui file."""

        self.setMinimumSize(1528, 1080)
        self.setStyleSheet("background-color: #0A0E1A;")

        # ── Camera feed frame ────────────────────────────────────────
        self.kamera_frame = QFrame(self)
        self.kamera_frame.setGeometry(20, 20, 934, 525)
        self.kamera_frame.setStyleSheet(_FRAME_STYLE)

        lbl_kamera_title = QLabel("Kamera Görüntüsü", self.kamera_frame)
        lbl_kamera_title.setGeometry(20, 12, 300, 30)
        lbl_kamera_title.setStyleSheet(_TITLE_STYLE)

        self.camera_label = QLabel(self.kamera_frame)
        self.camera_label.setGeometry(10, 48, 914, 467)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet(
            "QLabel { background-color: #1A1F37; border-radius: 10px; "
            "color: rgba(244,246,252,80); font-size: 16px; }"
        )
        self.camera_label.setText("Kamera bekleniyor…")

        # ── Sequential thumbnails frame ──────────────────────────────
        self.sirali_frame = QFrame(self)
        self.sirali_frame.setGeometry(20, 555, 934, 170)
        self.sirali_frame.setStyleSheet(_FRAME_STYLE)

        lbl_sirali_title = QLabel("Sıralı Görüntüler", self.sirali_frame)
        lbl_sirali_title.setGeometry(20, 10, 300, 26)
        lbl_sirali_title.setStyleSheet(_TITLE_STYLE)

        self.thumbnail_labels: list[QLabel] = []
        thumb_y = 40
        thumb_spacing = 10
        thumb_x_start = 20
        for i in range(self._MAX_THUMBNAILS):
            lbl = QLabel(self.sirali_frame)
            x = thumb_x_start + i * (self._THUMB_W + thumb_spacing)
            lbl.setGeometry(x, thumb_y, self._THUMB_W, self._THUMB_H)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                "QLabel { background-color: #1A1F37; border-radius: 8px; "
                "color: rgba(244,246,252,60); font-size: 12px; }"
            )
            lbl.setText(f"{i + 1}")
            self.thumbnail_labels.append(lbl)

        # ── Broken-tooth detection frame ─────────────────────────────
        self.kirik_frame = QFrame(self)
        self.kirik_frame.setGeometry(970, 20, 538, 350)
        self.kirik_frame.setStyleSheet(_FRAME_STYLE)

        lbl_kirik_title = QLabel("Kırık Diş Tespiti", self.kirik_frame)
        lbl_kirik_title.setGeometry(20, 15, 300, 30)
        lbl_kirik_title.setStyleSheet(_TITLE_STYLE)

        # Broken count
        lbl_broken_name = QLabel("Kırık Diş Sayısı", self.kirik_frame)
        lbl_broken_name.setGeometry(20, 60, 200, 22)
        lbl_broken_name.setStyleSheet(_SUBTITLE_STYLE)

        self.lbl_broken_count = QLabel("0", self.kirik_frame)
        self.lbl_broken_count.setGeometry(20, 85, 200, 45)
        self.lbl_broken_count.setStyleSheet(_VALUE_STYLE)

        # Tooth count
        lbl_tooth_name = QLabel("Toplam Diş Sayısı", self.kirik_frame)
        lbl_tooth_name.setGeometry(20, 140, 200, 22)
        lbl_tooth_name.setStyleSheet(_SUBTITLE_STYLE)

        self.lbl_tooth_count = QLabel("—", self.kirik_frame)
        self.lbl_tooth_count.setGeometry(20, 165, 200, 45)
        self.lbl_tooth_count.setStyleSheet(_VALUE_STYLE)

        # Last detection timestamp
        lbl_kirik_ts_name = QLabel("Son Tespit", self.kirik_frame)
        lbl_kirik_ts_name.setGeometry(20, 225, 200, 22)
        lbl_kirik_ts_name.setStyleSheet(_SUBTITLE_STYLE)

        self.lbl_kirik_ts = QLabel("—", self.kirik_frame)
        self.lbl_kirik_ts.setGeometry(20, 250, 300, 30)
        self.lbl_kirik_ts.setStyleSheet(_INFO_STYLE)

        # OK / alert indicator
        self.lbl_kirik_status = QLabel("✓ OK", self.kirik_frame)
        self.lbl_kirik_status.setGeometry(20, 290, 200, 40)
        self.lbl_kirik_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._set_ok_style(self.lbl_kirik_status)

        # ── Crack detection frame ────────────────────────────────────
        self.catlak_frame = QFrame(self)
        self.catlak_frame.setGeometry(970, 385, 538, 350)
        self.catlak_frame.setStyleSheet(_FRAME_STYLE)

        lbl_catlak_title = QLabel("Çatlak Tespiti", self.catlak_frame)
        lbl_catlak_title.setGeometry(20, 15, 300, 30)
        lbl_catlak_title.setStyleSheet(_TITLE_STYLE)

        # Crack count
        lbl_crack_name = QLabel("Çatlak Sayısı", self.catlak_frame)
        lbl_crack_name.setGeometry(20, 60, 200, 22)
        lbl_crack_name.setStyleSheet(_SUBTITLE_STYLE)

        self.lbl_crack_count = QLabel("0", self.catlak_frame)
        self.lbl_crack_count.setGeometry(20, 85, 200, 45)
        self.lbl_crack_count.setStyleSheet(_VALUE_STYLE)

        # Last detection timestamp
        lbl_catlak_ts_name = QLabel("Son Tespit", self.catlak_frame)
        lbl_catlak_ts_name.setGeometry(20, 145, 200, 22)
        lbl_catlak_ts_name.setStyleSheet(_SUBTITLE_STYLE)

        self.lbl_catlak_ts = QLabel("—", self.catlak_frame)
        self.lbl_catlak_ts.setGeometry(20, 170, 300, 30)
        self.lbl_catlak_ts.setStyleSheet(_INFO_STYLE)

        # OK / alert indicator
        self.lbl_catlak_status = QLabel("✓ OK", self.catlak_frame)
        self.lbl_catlak_status.setGeometry(20, 220, 200, 40)
        self.lbl_catlak_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._set_ok_style(self.lbl_catlak_status)

        # ── Wear percentage frame ────────────────────────────────────
        self.asinma_frame = QFrame(self)
        self.asinma_frame.setGeometry(20, 740, 300, 120)
        self.asinma_frame.setStyleSheet(_FRAME_STYLE)

        lbl_asinma_title = QLabel("Aşınma Yüzdesi", self.asinma_frame)
        lbl_asinma_title.setGeometry(15, 10, 270, 26)
        lbl_asinma_title.setStyleSheet(_TITLE_STYLE)

        self.lbl_wear_value = QLabel("—", self.asinma_frame)
        self.lbl_wear_value.setGeometry(15, 45, 270, 55)
        self.lbl_wear_value.setStyleSheet(_VALUE_STYLE)
        self.lbl_wear_value.setAlignment(Qt.AlignCenter)

        # ── Health score frame ───────────────────────────────────────
        self.saglik_frame = QFrame(self)
        self.saglik_frame.setGeometry(340, 740, 300, 120)
        self.saglik_frame.setStyleSheet(_FRAME_STYLE)

        lbl_saglik_title = QLabel("Testere Sağlığı", self.saglik_frame)
        lbl_saglik_title.setGeometry(15, 10, 270, 26)
        lbl_saglik_title.setStyleSheet(_TITLE_STYLE)

        self.lbl_health_score = QLabel("—", self.saglik_frame)
        self.lbl_health_score.setGeometry(15, 45, 270, 55)
        self.lbl_health_score.setStyleSheet(_VALUE_STYLE)
        self.lbl_health_score.setAlignment(Qt.AlignCenter)

        # ── Health status frame ──────────────────────────────────────
        self.durum_frame = QFrame(self)
        self.durum_frame.setGeometry(660, 740, 300, 120)
        self.durum_frame.setStyleSheet(_FRAME_STYLE)

        lbl_durum_title = QLabel("Testere Durumu", self.durum_frame)
        lbl_durum_title.setGeometry(15, 10, 270, 26)
        lbl_durum_title.setStyleSheet(_TITLE_STYLE)

        self.lbl_health_status = QLabel("—", self.durum_frame)
        self.lbl_health_status.setGeometry(15, 45, 270, 55)
        self.lbl_health_status.setStyleSheet(_VALUE_STYLE)
        self.lbl_health_status.setAlignment(Qt.AlignCenter)

        # ── Recording / FPS info (bottom-right) ──────────────────────
        self.lbl_frame_count = QLabel("Kare: 0", self)
        self.lbl_frame_count.setGeometry(1300, 1040, 200, 20)
        self.lbl_frame_count.setStyleSheet(_INFO_STYLE)
        self.lbl_frame_count.setAlignment(Qt.AlignRight)

        self.lbl_recording = QLabel("Kayıt: —", self)
        self.lbl_recording.setGeometry(1300, 1060, 200, 20)
        self.lbl_recording.setStyleSheet(_INFO_STYLE)
        self.lbl_recording.setAlignment(Qt.AlignRight)

    # ------------------------------------------------------------------
    # Timers
    # ------------------------------------------------------------------

    def _setup_timers(self):
        """Create and start the three polling timers."""

        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(500)
        self._frame_timer.timeout.connect(self._update_frame)

        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(1000)
        self._stats_timer.timeout.connect(self._update_stats)

        self._health_timer = QTimer(self)
        self._health_timer.setInterval(2000)
        self._health_timer.timeout.connect(self._update_health)

        self._frame_timer.start()
        self._stats_timer.start()
        self._health_timer.start()

        logger.debug("CameraController timers started (500/1000/2000 ms)")

    def stop_timers(self):
        """Stop all QTimers — call from the GUI thread before window closes."""
        try:
            if hasattr(self, "_frame_timer") and self._frame_timer:
                self._frame_timer.stop()
            if hasattr(self, "_stats_timer") and self._stats_timer:
                self._stats_timer.stop()
            if hasattr(self, "_health_timer") and self._health_timer:
                self._health_timer.stop()
            logger.info("CameraController timers stopped")
        except Exception as e:
            logger.error(f"Error stopping CameraController timers: {e}")

    # ------------------------------------------------------------------
    # Timer callbacks
    # ------------------------------------------------------------------

    def _update_frame(self):
        """Poll latest frame from the store, update camera label + thumbnails."""
        try:
            snapshot = self.results_store.snapshot()
            jpeg_bytes = snapshot.get("latest_frame")
            if not jpeg_bytes:
                return

            qimage = QImage()
            if not qimage.loadFromData(jpeg_bytes):
                logger.error("Failed to decode JPEG frame")
                return

            pixmap = QPixmap.fromImage(qimage)

            # Scale to camera label size, preserving aspect ratio
            scaled = pixmap.scaled(
                self.camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.camera_label.setPixmap(scaled)

            # Update thumbnail strip — add current frame, keep max 4
            thumb = pixmap.scaled(
                self._THUMB_W,
                self._THUMB_H,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self._thumb_pixmaps.append(thumb)
            self._refresh_thumbnails()

        except Exception:
            logger.error("Error in _update_frame", exc_info=True)

    def _update_stats(self):
        """Poll detection stats and recording info."""
        try:
            snapshot = self.results_store.snapshot()

            broken = snapshot.get("broken_count", 0)
            tooth = snapshot.get("tooth_count", "—")
            crack = snapshot.get("crack_count", 0)
            last_ts = snapshot.get("last_detection_ts", "—")
            frame_count = snapshot.get("frame_count", 0)
            is_recording = snapshot.get("is_recording", False)

            # Broken tooth panel
            self.lbl_broken_count.setText(str(broken))
            self.lbl_tooth_count.setText(str(tooth))
            self.lbl_kirik_ts.setText(str(last_ts) if last_ts else "—")

            if broken and int(broken) > 0:
                self.lbl_kirik_status.setText("✗ UYARI")
                self._set_alert_style(self.lbl_kirik_status)
            else:
                self.lbl_kirik_status.setText("✓ OK")
                self._set_ok_style(self.lbl_kirik_status)

            # Crack panel
            self.lbl_crack_count.setText(str(crack))
            self.lbl_catlak_ts.setText(str(last_ts) if last_ts else "—")

            if crack and int(crack) > 0:
                self.lbl_catlak_status.setText("✗ UYARI")
                self._set_alert_style(self.lbl_catlak_status)
            else:
                self.lbl_catlak_status.setText("✓ OK")
                self._set_ok_style(self.lbl_catlak_status)

            # Recording info
            self.lbl_frame_count.setText(f"Kare: {frame_count}")
            self.lbl_recording.setText(
                "Kayıt: Aktif" if is_recording else "Kayıt: —"
            )

        except Exception:
            logger.error("Error in _update_stats", exc_info=True)

    def _update_health(self):
        """Poll wear / health data."""
        try:
            snapshot = self.results_store.snapshot()

            wear = snapshot.get("wear_percentage")
            score = snapshot.get("health_score")
            status = snapshot.get("health_status", "—")
            color_hex = snapshot.get("health_color", "#F4F6FC")

            # Wear percentage
            if wear is not None:
                self.lbl_wear_value.setText(f"{float(wear):.1f}%")
            else:
                self.lbl_wear_value.setText("—")

            # Health score
            if score is not None:
                self.lbl_health_score.setText(f"{float(score):.1f}%")
            else:
                self.lbl_health_score.setText("—")

            # Health status text with dynamic color
            self.lbl_health_status.setText(str(status))
            self.lbl_health_status.setStyleSheet(f"""
                QLabel {{
                    color: {color_hex};
                    font-family: 'Plus Jakarta Sans';
                    font-weight: bold;
                    font-size: 32px;
                    background-color: transparent;
                }}
            """)

        except Exception:
            logger.error("Error in _update_health", exc_info=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_thumbnails(self):
        """Redraw the thumbnail strip from the deque."""
        for i, lbl in enumerate(self.thumbnail_labels):
            if i < len(self._thumb_pixmaps):
                lbl.setPixmap(self._thumb_pixmaps[i])
            else:
                lbl.clear()
                lbl.setText(f"{i + 1}")

    @staticmethod
    def _set_ok_style(label: QLabel):
        """Apply green OK style to a status indicator label."""
        label.setStyleSheet("""
            QLabel {
                color: #22C55E;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 28px;
                background-color: transparent;
            }
        """)

    @staticmethod
    def _set_alert_style(label: QLabel):
        """Apply red ALERT style to a status indicator label."""
        label.setStyleSheet("""
            QLabel {
                color: #EF4444;
                font-family: 'Plus Jakarta Sans';
                font-weight: bold;
                font-size: 28px;
                background-color: transparent;
            }
        """)
