# -*- coding: utf-8 -*-
"""
ThingsBoard cihaz API'si için HTTP tabanlı gönderim istemcisi (sağlamlaştırılmış sürüm).
- Telemetry ve attributes gönderimi
- Toplu (batch) gönderim desteği
- Retry + exponential backoff
- İnce ayarlı timeout (connect/read/write/pool)
- Zaman damgası normalizasyonu (s, ms, ISO)
- Alan adı eşleme (field_map) ve güvenli veri temizleme (sanitize)
- Context manager (with ... as ...) desteği

NOT: Varsayılan base_url, senin kullandığın uzak TB:
      http://185.87.252.58:8081
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Union

import httpx


Number = Union[int, float]
JSONObj = Dict[str, Any]

# YALNIZCA "tamamen sayısal" metinleri sayıya çeviren regex.
# Böylece "0123" gibi ID'leri yanlışlıkla float'a çevirmeyiz.
_NUMERIC_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


class ThingsBoardSender:
    """
    Basit kullanım:
        tb = ThingsBoardSender(
            base_url="http://185.87.252.58:8081",
            access_token="CIHAZ_TOKENIN",
        )
        tb.send_telemetry({"serit_motor_akim_a": 12.3, "serit_gerginligi_bar": 9.6})
        tb.close()

    Context manager:
        with ThingsBoardSender("http://185.87.252.58:8081", "CIHAZ_TOKENIN") as tb:
            tb.send_attributes({"makine_adi": "SmartSaw-01"})
    """

    # Dashboard ve veri boru hattına uygun bilinen alanlar.
    EXPECTED_FIELDS: Tuple[str, ...] = (
        "id", "timestamp", "makine_id", "serit_id", "serit_dis_mm", "serit_tip",
        "serit_marka", "serit_malz", "malzeme_cinsi", "malzeme_sertlik",
        "kesit_yapisi", "a_mm", "b_mm", "c_mm", "d_mm", "kafa_yuksekligi_mm",
        "kesilen_parca_adeti", "serit_motor_akim_a", "serit_motor_tork_percentage",
        "inme_motor_akim_a", "inme_motor_tork_percentage", "mengene_basinc_bar",
        "serit_gerginligi_bar",          # ← Doğru isim
        "serit_sapmasi", "ortam_sicakligi_c", "ortam_nem_percentage",
        "sogutma_sivi_sicakligi_c", "hidrolik_yag_sicakligi_c", "serit_sicakligi_c",
        "ivme_olcer_x", "ivme_olcer_y", "ivme_olcer_z",
        "ivme_olcer_x_hz", "ivme_olcer_y_hz", "ivme_olcer_z_hz", "max_titresim_hz",
        "testere_durumu", "alarm_status", "alarm_bilgisi",
        "serit_kesme_hizi", "serit_inme_hizi", "fuzzy_output",
        "kesme_hizi_degisim", "modbus_connected", "modbus_ip",
        "kesim_turu", "kesim_id",
    )

    def __init__(
        self,
        base_url: str,
        access_token: str,
        *,
        timeout: Optional[httpx.Timeout] = None,
        verify: Union[bool, str] = True,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        default_headers: Optional[Mapping[str, str]] = None,
        logger: Optional[Any] = None,
    ) -> None:
        """
        Parametreler:
          - base_url: TB temel adresi (örn. http://185.87.252.58:8081)
          - access_token: cihaz access token'ı
          - timeout: httpx.Timeout; None ise makul varsayılanlar atanır
          - verify: HTTPS doğrulama (http kullanıyorsan etkisiz)
          - max_retries: başarısız POST denemesi tekrar sayısı
          - backoff_factor: denemeler arası bekleme (exponential backoff)
          - default_headers: HTTP isteğine varsayılan başlıklar
          - logger: uyarı/log basmak için opsiyonel logger
        """
        if not base_url:
            raise ValueError("base_url must be provided")
        if not access_token:
            raise ValueError("access_token must be provided")

        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.verify = verify
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logger

        if timeout is None:
            # Bağlantı, okuma, yazma ve havuz zaman aşımları ayrı ayrı.
            timeout = httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)

        self._client = httpx.Client(timeout=timeout, verify=verify, headers=dict(default_headers or {}))

    # ---------- Context manager ----------
    def __enter__(self) -> "ThingsBoardSender":
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    # ---------- Public API ----------
    def send_telemetry(self, data: Mapping[str, Any]) -> bool:
        """Zaman damgasız tek telemetry sözlüğü gönderir."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping of key to value")
        url = self._build_url("/telemetry")
        return self._post_json(url, dict(data))

    def send_attributes(self, attributes: Mapping[str, Any]) -> bool:
        """İstemci tarafı attributes gönderir."""
        if not isinstance(attributes, Mapping):
            raise TypeError("attributes must be a mapping of key to value")
        url = self._build_url("/attributes")
        return self._post_json(url, dict(attributes))

    def send_events(self, events: Iterable[Mapping[str, Any]]) -> bool:
        """
        Toplu zaman serisi (batch) gönderimi.
        Örnek payload:
            [
              {"ts": 1712323232000, "values": {"serit_motor_akim_a": 12.3}},
              {"ts": 1712323233000, "values": {"serit_motor_akim_a": 12.7}}
            ]
        """
        url = self._build_url("/telemetry")
        payload = [dict(e) for e in events]
        return self._post_json(url, payload)

    def send_machine_telemetry(
        self,
        machine_values: Mapping[str, Any],
        *,
        prefix: Optional[str] = None,
        extra_fields: Optional[Mapping[str, Any]] = None,
        timestamp: Optional[Union[int, float, str, datetime]] = None,
        timestamp_unit: str = "auto",  # "auto" | "s" | "ms"
        field_map: Optional[Mapping[str, str]] = None,
    ) -> bool:
        """
        Makine sözlüğünü ThingsBoard formatına getirip gönderir.
          - prefix: anahtarların başına önek (örn. "saw_")
          - extra_fields: telemetriye eklenecek ek alanlar
          - timestamp: verilirse TB'nin "ts/values" şeması kullanılır
          - timestamp_unit: 'auto' (>=1e12 → ms), 's', 'ms'
          - field_map: isim dönüştürme (örn. {'serit_gerginligi':'serit_gerginligi_bar'})
        """
        values = self._sanitize_machine_data(machine_values, prefix=prefix, extra=extra_fields, field_map=field_map)
        url = self._build_url("/telemetry")

        if timestamp is not None:
            ts_ms = self._normalize_ts(timestamp, unit=timestamp_unit)
            body: JSONObj = {"ts": ts_ms, "values": values}
        else:
            body = values

        return self._post_json(url, body)

    def send_processed_row(
        self,
        row: Mapping[str, Any],
        *,
        field_map: Optional[Mapping[str, str]] = None,
        timestamp_unit: str = "auto",
    ) -> bool:
        """
        İşlenmiş (tek satır) veriyi ThingsBoard'a gönder.
        - 'timestamp' varsa epoch ms'e çevrilir
        - EXPECTED_FIELDS + ekstra alanlar toplanır
        - field_map ile adlar normalize edilir
        """
        if not isinstance(row, Mapping):
            raise TypeError("row must be a mapping")

        # timestamp → epoch ms
        ts_ms: Optional[int] = None
        raw_ts = row.get("timestamp")
        if raw_ts is not None:
            try:
                ts_ms = self._normalize_ts(raw_ts, unit=timestamp_unit)
            except Exception:
                ts_ms = None

        # Bilinen alanları önceliklendir, ekstra alanları da ekle
        values: Dict[str, Any] = {}
        for key in self.EXPECTED_FIELDS:
            if key in row:
                values[key] = row.get(key)
        for key, value in dict(row).items():
            if key not in values:
                values[key] = value

        cleaned = self._sanitize_machine_data(values, field_map=field_map)

        url = self._build_url("/telemetry")
        body: JSONObj = {"ts": ts_ms, "values": cleaned} if ts_ms is not None else cleaned
        return self._post_json(url, body)

    def close(self) -> None:
        """HTTP istemcisini kapat (kaynak serbest bırak)."""
        try:
            self._client.close()
        except Exception:
            pass

    # ---------- Internal helpers ----------
    def _build_url(self, path: str) -> str:
        """Cihaz token'ı gömülü endpoint oluşturur."""
        return f"{self.base_url}/api/v1/{self.access_token}{path}"

    def _post_json(self, url: str, payload: Any) -> bool:
        """Retry + exponential backoff ile JSON POST yap."""
        tries = max(1, int(self.max_retries))
        delay = max(0.0, float(self.backoff_factor))

        for attempt in range(tries):
            try:
                r = self._client.post(url, json=payload)
                if r.status_code in (200, 204):
                    return True
                # 5xx: sunucu hatası → retry mantıklı; 4xx genelde yanlış token/endpoint
                if 500 <= r.status_code < 600:
                    self._log(f"[TB] {r.status_code} server error, retrying...")
                else:
                    self._log(f"[TB] HTTP {r.status_code}: {r.text[:200]}")
                    return False
            except Exception as e:
                self._log(f"[TB] POST error: {e!r}")

            if attempt < tries - 1 and delay > 0:
                time.sleep(delay * (2 ** attempt))

        return False

    def _log(self, msg: str) -> None:
        """Logger varsa uyarı bas; yoksa sessiz kal (istersen print aç)."""
        if self.logger is not None:
            try:
                self.logger.warning(msg)
            except Exception:
                pass
        else:
            # Geliştirme aşamasında görmek istersen aşağıyı aç:
            # print(msg)
            pass

    @staticmethod
    def _normalize_ts(value: Union[int, float, str, datetime], *, unit: str = "auto") -> int:
        """
        Timestamp'i epoch milliseconds'e çevir.
          - unit="ms": değer doğrudan ms kabul edilir
          - unit="s" : saniye → ms
          - unit="auto": heuristik (>=1e12 ise ms, değilse s)
          - ISO string (örn. '2025-08-31T14:30:00') → ms
        """
        if isinstance(value, datetime):
            return int(value.timestamp() * 1000)
        if isinstance(value, str):
            # ISO tarih ise parse et, değilse sayıya çevirmeyi dene
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp() * 1000)
            except Exception:
                value = float(value)

        if unit == "ms":
            return int(float(value))
        if unit == "s":
            return int(float(value) * 1000.0)

        v = float(value)
        return int(v if v >= 1e12 else v * 1000.0)

    @staticmethod
    def _sanitize_machine_data(
        values: Mapping[str, Any],
        *,
        prefix: Optional[str] = None,
        extra: Optional[Mapping[str, Any]] = None,
        field_map: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Güvenli veri temizleme:
          - None olanları at
          - Sadece TAM sayısal stringleri number'a çevir (regex ile)
          - prefix uygula (örn. 'saw_')
          - field_map ile anahtar adlarını normalize et
          - extra alanları ekle
        """
        out: Dict[str, Any] = {}

        def map_key(k: str) -> str:
            if field_map and k in field_map:
                return field_map[k]
            return k

        for key, value in dict(values).items():
            if value is None:
                continue
            base_key = map_key(str(key))               # önce eşleme
            new_key  = f"{prefix}{base_key}" if prefix else base_key  # sonra prefix

            if isinstance(value, (int, float, bool)):
                out[new_key] = value
            elif isinstance(value, str):
                s = value.strip()
                if _NUMERIC_RE.match(s):
                    # "12" → 12 (int), "12.5" → 12.5 (float)
                    try:
                        out[new_key] = float(s) if ("." in s or "e" in s.lower()) else int(s)
                    except Exception:
                        out[new_key] = s
                else:
                    out[new_key] = s
            else:
                # Liste/sözlük gibi tipleri de ham haliyle koyuyoruz; TB JSON kabul eder.
                out[new_key] = value

        if extra:
            for key, value in dict(extra).items():
                if value is None:
                    continue
                base_key = map_key(str(key))
                out[ f"{prefix}{base_key}" if prefix else base_key ] = value

        return out


# --------- Ortam değişkenlerinden kurulum (fabrika) ---------
def create_sender_from_env(prefix: str = "TB_", default_url: str = "http://185.87.252.58:8081") -> ThingsBoardSender:
    """
    Ortam değişkenleri ile kolay kurulum:
      - TB_URL:    örn. http://185.87.252.58:8081   (varsayılan bu)
      - TB_TOKEN:  cihaz access token
      - TB_TIMEOUT: tek sayı verirsen tüm timeout'lara uygulanır (s)
      - TB_VERIFY:  "false"/"0"/"no" → False (HTTPS için)
      - TB_RETRIES: int, varsayılan 3
      - TB_BACKOFF: float, varsayılan 0.5
    """
    base_url = os.getenv(f"{prefix}URL", default_url).strip()
    token = os.getenv(f"{prefix}TOKEN", "").strip()

    # Basit (tek değer) timeout → tüm alanlara uygula; ince ayar gerekiyorsa ctor'da override et
    timeout_str = (os.getenv(f"{prefix}TIMEOUT", "") or "").strip()
    if timeout_str:
        try:
            to_val = float(timeout_str)
            timeout = httpx.Timeout(connect=to_val, read=to_val, write=to_val, pool=to_val)
        except Exception:
            timeout = httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
    else:
        timeout = httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)

    verify_env = (os.getenv(f"{prefix}VERIFY", "true") or "true").strip().lower()
    verify: Union[bool, str]
    if verify_env in ("false", "0", "no"):
        verify = False
    else:
        verify = True

    retries = int((os.getenv(f"{prefix}RETRIES", "3") or "3").strip())
    backoff = float((os.getenv(f"{prefix}BACKOFF", "0.5") or "0.5").strip())

    return ThingsBoardSender(
        base_url=base_url,
        access_token=token,
        timeout=timeout,
        verify=verify,
        max_retries=retries,
        backoff_factor=backoff,
    )
