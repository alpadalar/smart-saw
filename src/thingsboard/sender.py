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
- Thread-safe operasyonlar
- Metrik toplama ve monitoring

NOT: Varsayılan base_url, senin kullandığın uzak TB:
      http://185.87.252.58:8081
"""

from __future__ import annotations

import os
import re
import time
import threading
from collections import defaultdict
from datetime import datetime, timezone
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
        enable_metrics: bool = True,
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
          - enable_metrics: metrik toplama aktif/pasif
        """
        if not base_url:
            raise ValueError("base_url must be provided")
        if not access_token:
            raise ValueError("access_token must be provided")
        if not access_token.strip():
            raise ValueError("access_token cannot be empty or whitespace")

        self.base_url = base_url.rstrip("/")
        self.access_token = access_token.strip()
        self.verify = verify
        self.max_retries = max(1, int(max_retries))
        self.backoff_factor = max(0.0, float(backoff_factor))
        self.logger = logger
        self.enable_metrics = enable_metrics

        # Thread safety için lock
        self._lock = threading.RLock()
        
        # Metrik sayaçları
        self._metrics = defaultdict(int) if enable_metrics else None
        self._last_error = None
        self._last_error_time = None

        if timeout is None:
            # Timeout'ları artırdık: daha uzun network latency'si için
            timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=10.0)

        # Connection pooling aktif: limits parametresi ile kontrol edilir
        # max_keepalive_connections=20: aynı anda 20 bağlantı havuzda tutulur
        # max_connections=100: maksimum toplam bağlantı sayısı
        self._client = httpx.Client(
            timeout=timeout,
            verify=verify,
            headers=dict(default_headers or {}),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=False,  # HTTP/2 devre dışı (daha kararlı)
        )

    # ---------- Context manager ----------
    def __enter__(self) -> "ThingsBoardSender":
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    # ---------- Public API ----------
    def send_telemetry(self, data: Mapping[str, Any]) -> bool:
        """Zaman damgasız tek telemetry sözlüğü gönderir. Thread-safe."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping of key to value")
        with self._lock:
            url = self._build_url("/telemetry")
            return self._post_json(url, dict(data), operation="send_telemetry")

    def send_attributes(self, attributes: Mapping[str, Any]) -> bool:
        """İstemci tarafı attributes gönderir. Thread-safe."""
        if not isinstance(attributes, Mapping):
            raise TypeError("attributes must be a mapping of key to value")
        with self._lock:
            url = self._build_url("/attributes")
            return self._post_json(url, dict(attributes), operation="send_attributes")

    def send_events(self, events: Iterable[Mapping[str, Any]]) -> bool:
        """
        Toplu zaman serisi (batch) gönderimi. Thread-safe.
        Örnek payload:
            [
              {"ts": 1712323232000, "values": {"serit_motor_akim_a": 12.3}},
              {"ts": 1712323233000, "values": {"serit_motor_akim_a": 12.7}}
            ]
        """
        with self._lock:
            url = self._build_url("/telemetry")
            payload = [dict(e) for e in events]
            return self._post_json(url, payload, operation="send_events")

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
        Makine sözlüğünü ThingsBoard formatına getirip gönderir. Thread-safe.
          - prefix: anahtarların başına önek (örn. "saw_")
          - extra_fields: telemetriye eklenecek ek alanlar
          - timestamp: verilirse TB'nin "ts/values" şeması kullanılır
          - timestamp_unit: 'auto' (>=1e12 → ms), 's', 'ms'
          - field_map: isim dönüştürme (örn. {'serit_gerginligi':'serit_gerginligi_bar'})
        """
        with self._lock:
            values = self._sanitize_machine_data(machine_values, prefix=prefix, extra=extra_fields, field_map=field_map)
            url = self._build_url("/telemetry")

            if timestamp is not None:
                ts_ms = self._normalize_ts(timestamp, unit=timestamp_unit)
                body: JSONObj = {"ts": ts_ms, "values": values}
            else:
                body = values

            return self._post_json(url, body, operation="send_machine_telemetry")

    def send_processed_row(
        self,
        row: Mapping[str, Any],
        *,
        field_map: Optional[Mapping[str, str]] = None,
        timestamp_unit: str = "auto",
    ) -> bool:
        """
        İşlenmiş (tek satır) veriyi ThingsBoard'a gönder. Thread-safe.
        - 'timestamp' varsa epoch ms'e çevrilir
        - EXPECTED_FIELDS + ekstra alanlar toplanır
        - field_map ile adlar normalize edilir
        """
        if not isinstance(row, Mapping):
            raise TypeError("row must be a mapping")

        with self._lock:
            # timestamp → epoch ms
            ts_ms: Optional[int] = None
            raw_ts = row.get("timestamp")
            if raw_ts is not None:
                try:
                    ts_ms = self._normalize_ts(raw_ts, unit=timestamp_unit)
                except Exception as e:
                    self._log(f"[TB] Timestamp dönüştürme hatası: {e!r}, raw_ts={raw_ts}", level="warning")
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
            return self._post_json(url, body, operation="send_processed_row")

    def close(self) -> None:
        """HTTP istemcisini kapat (kaynak serbest bırak). Thread-safe."""
        with self._lock:
            try:
                self._client.close()
            except Exception:
                pass

    def get_metrics(self) -> Dict[str, Any]:
        """
        Metrik istatistiklerini döndürür. Thread-safe.
        Returns:
            {
                "total_requests": int,
                "successful_requests": int,
                "failed_requests": int,
                "last_error": str or None,
                "last_error_time": float or None,
                "success_rate": float (0.0-1.0),
            }
        """
        with self._lock:
            if not self.enable_metrics or self._metrics is None:
                return {}
            
            total = self._metrics.get("total_requests", 0)
            success = self._metrics.get("successful_requests", 0)
            failed = self._metrics.get("failed_requests", 0)
            success_rate = (success / total) if total > 0 else 0.0
            
            return {
                "total_requests": total,
                "successful_requests": success,
                "failed_requests": failed,
                "success_rate": success_rate,
                "last_error": self._last_error,
                "last_error_time": self._last_error_time,
                "by_operation": dict(self._metrics),
            }
    
    def reset_metrics(self) -> None:
        """Metrik sayaçlarını sıfırlar. Thread-safe."""
        with self._lock:
            if self.enable_metrics and self._metrics is not None:
                self._metrics.clear()
                self._last_error = None
                self._last_error_time = None

    # ---------- Internal helpers ----------
    def _build_url(self, path: str) -> str:
        """Cihaz token'ı gömülü endpoint oluşturur."""
        return f"{self.base_url}/api/v1/{self.access_token}{path}"

    def _post_json(self, url: str, payload: Any, operation: str = "unknown") -> bool:
        """
        Retry + exponential backoff ile JSON POST yap.
        Thread-safe olarak metrikleri günceller.
        """
        tries = self.max_retries
        delay = self.backoff_factor
        last_exception = None
        last_status_code = None

        for attempt in range(tries):
            try:
                r = self._client.post(url, json=payload)
                last_status_code = r.status_code
                
                if r.status_code in (200, 204):
                    # Başarılı
                    self._record_success(operation)
                    if attempt > 0:
                        self._log(f"[TB] {operation} başarılı (retry sonrası, attempt={attempt+1})", level="info")
                    return True
                
                # 5xx: sunucu hatası → retry mantıklı
                if 500 <= r.status_code < 600:
                    error_msg = f"[TB] {operation}: HTTP {r.status_code} server error"
                    if attempt < tries - 1:
                        self._log(f"{error_msg}, retrying... (attempt {attempt+1}/{tries})", level="warning")
                    else:
                        self._log(f"{error_msg}, max retries reached", level="error")
                        self._record_failure(operation, f"HTTP {r.status_code}")
                    last_exception = f"HTTP {r.status_code}: {r.text[:200]}"
                
                # 4xx: client hatası (token, yetki, vb.) → retry anlamsız
                elif 400 <= r.status_code < 500:
                    error_msg = f"[TB] {operation}: HTTP {r.status_code} client error: {r.text[:300]}"
                    self._log(error_msg, level="error")
                    self._record_failure(operation, f"HTTP {r.status_code}")
                    return False
                
                # Diğer durumlarda
                else:
                    error_msg = f"[TB] {operation}: Unexpected HTTP {r.status_code}: {r.text[:200]}"
                    self._log(error_msg, level="warning")
                    self._record_failure(operation, f"HTTP {r.status_code}")
                    return False
                    
            except httpx.TimeoutException as e:
                last_exception = str(e)
                if attempt < tries - 1:
                    self._log(f"[TB] {operation}: Timeout (attempt {attempt+1}/{tries}), retrying... {e!r}", level="warning")
                else:
                    self._log(f"[TB] {operation}: Timeout, max retries reached: {e!r}", level="error")
                    self._record_failure(operation, f"Timeout: {e}")
                    
            except httpx.ConnectError as e:
                last_exception = str(e)
                if attempt < tries - 1:
                    self._log(f"[TB] {operation}: Connection error (attempt {attempt+1}/{tries}), retrying... {e!r}", level="warning")
                else:
                    self._log(f"[TB] {operation}: Connection error, max retries reached: {e!r}", level="error")
                    self._record_failure(operation, f"Connection: {e}")
                    
            except httpx.HTTPError as e:
                last_exception = str(e)
                if attempt < tries - 1:
                    self._log(f"[TB] {operation}: HTTP error (attempt {attempt+1}/{tries}), retrying... {e!r}", level="warning")
                else:
                    self._log(f"[TB] {operation}: HTTP error, max retries reached: {e!r}", level="error")
                    self._record_failure(operation, f"HTTP error: {e}")
                    
            except Exception as e:
                last_exception = str(e)
                error_type = type(e).__name__
                if attempt < tries - 1:
                    self._log(f"[TB] {operation}: {error_type} (attempt {attempt+1}/{tries}), retrying... {e!r}", level="warning")
                else:
                    self._log(f"[TB] {operation}: {error_type}, max retries reached: {e!r}", level="error")
                    self._record_failure(operation, f"{error_type}: {e}")

            # Exponential backoff
            if attempt < tries - 1 and delay > 0:
                sleep_time = delay * (2 ** attempt)
                time.sleep(sleep_time)

        # Tüm retry'ler tükendi
        self._record_failure(operation, last_exception or f"HTTP {last_status_code}" if last_status_code else "Unknown")
        return False

    def _log(self, msg: str, level: str = "warning") -> None:
        """
        Logger varsa mesaj bas; yoksa print ile göster.
        Levels: "debug", "info", "warning", "error", "critical"
        """
        if self.logger is not None:
            try:
                log_method = getattr(self.logger, level.lower(), self.logger.warning)
                log_method(msg)
            except Exception:
                pass
        else:
            # Logger yoksa print ile göster (production'da görünür olsun)
            print(f"[{level.upper()}] {msg}")
    
    def _record_success(self, operation: str) -> None:
        """Başarılı işlem metriğini kaydet."""
        if self.enable_metrics and self._metrics is not None:
            self._metrics["total_requests"] += 1
            self._metrics["successful_requests"] += 1
            self._metrics[f"{operation}_success"] = self._metrics.get(f"{operation}_success", 0) + 1
    
    def _record_failure(self, operation: str, error: str) -> None:
        """Başarısız işlem metriğini kaydet."""
        if self.enable_metrics and self._metrics is not None:
            self._metrics["total_requests"] += 1
            self._metrics["failed_requests"] += 1
            self._metrics[f"{operation}_failed"] = self._metrics.get(f"{operation}_failed", 0) + 1
            self._last_error = error
            self._last_error_time = time.time()

    @staticmethod
    def _normalize_ts(value: Union[int, float, str, datetime], *, unit: str = "auto") -> int:
        """
        Timestamp'i epoch milliseconds'e çevir.
          - unit="ms": değer doğrudan ms kabul edilir
          - unit="s" : saniye → ms
          - unit="auto": heuristik (>=1e12 ise ms, değilse s)
          - ISO string (örn. '2025-08-31T14:30:00' veya '2025-08-31T14:30:00+03:00') → ms
        """
        if isinstance(value, datetime):
            return int(value.timestamp() * 1000)
        
        if isinstance(value, str):
            # Boş string kontrolü
            value_stripped = value.strip()
            if not value_stripped:
                raise ValueError("Empty timestamp string")
            
            # ISO tarih formatını parse et
            # Python 3.7+: fromisoformat kullan, timezone destekli
            try:
                # Önce ISO formatı dene
                # fromisoformat timezone'lu stringleri destekler (örn. +03:00)
                dt = datetime.fromisoformat(value_stripped)
                return int(dt.timestamp() * 1000)
            except ValueError:
                # ISO değilse, sayısal string olabilir
                pass
            
            # Sayısal string'e çevirmeyi dene
            try:
                value = float(value_stripped)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot parse timestamp: {value_stripped!r}") from e

        # Sayısal değerler için (int, float)
        try:
            if unit == "ms":
                return int(float(value))
            if unit == "s":
                return int(float(value) * 1000.0)

            # Auto: heuristic
            v = float(value)
            # 1e12 = 1 trilyon ms = ~2001 yılı (epoch'tan 31 yıl sonra)
            # Bu değerden büyükse zaten ms, küçükse saniye
            return int(v if v >= 1e12 else v * 1000.0)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid timestamp value: {value!r}") from e

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
def create_sender_from_env(
    prefix: str = "TB_",
    default_url: str = "http://185.87.252.58:8081",
    logger: Optional[Any] = None,
    enable_metrics: bool = True,
) -> ThingsBoardSender:
    """
    Ortam değişkenleri ile kolay kurulum:
      - TB_URL:    örn. http://185.87.252.58:8081   (varsayılan bu)
      - TB_TOKEN:  cihaz access token (ZORUNLU, boş olamaz)
      - TB_TIMEOUT: tek sayı verirsen tüm timeout'lara uygulanır (s)
      - TB_VERIFY:  "false"/"0"/"no" → False (HTTPS için)
      - TB_RETRIES: int, varsayılan 3
      - TB_BACKOFF: float, varsayılan 0.5
      - logger: Python logger instance (opsiyonel)
      - enable_metrics: metrik toplama aktif/pasif (varsayılan True)
    
    Raises:
        ValueError: token boş veya geçersizse
    """
    base_url = os.getenv(f"{prefix}URL", default_url).strip()
    token = os.getenv(f"{prefix}TOKEN", "").strip()
    
    # Token validation
    if not token:
        error_msg = f"Environment variable {prefix}TOKEN is required but not set or empty"
        if logger:
            logger.error(error_msg)
        raise ValueError(error_msg)

    # Basit (tek değer) timeout → tüm alanlara uygula; ince ayar gerekiyorsa ctor'da override et
    timeout_str = (os.getenv(f"{prefix}TIMEOUT", "") or "").strip()
    if timeout_str:
        try:
            to_val = float(timeout_str)
            # Minimum 1 saniye, maksimum 60 saniye
            to_val = max(1.0, min(60.0, to_val))
            timeout = httpx.Timeout(connect=to_val, read=to_val*1.5, write=to_val, pool=to_val)
            if logger:
                logger.info(f"ThingsBoard timeout set to {to_val}s from environment")
        except Exception as e:
            # Varsayılan timeout'lara dön
            timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=10.0)
            if logger:
                logger.warning(f"Invalid {prefix}TIMEOUT value: {timeout_str}, using defaults: {e}")
    else:
        # Varsayılan: daha uzun timeout'lar (production için)
        timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=10.0)

    verify_env = (os.getenv(f"{prefix}VERIFY", "true") or "true").strip().lower()
    verify: Union[bool, str]
    if verify_env in ("false", "0", "no"):
        verify = False
    else:
        verify = True

    try:
        retries = int((os.getenv(f"{prefix}RETRIES", "3") or "3").strip())
        retries = max(1, min(10, retries))  # 1-10 arası sınırla
    except ValueError:
        retries = 3
        if logger:
            logger.warning(f"Invalid {prefix}RETRIES value, using default: 3")
    
    try:
        backoff = float((os.getenv(f"{prefix}BACKOFF", "0.5") or "0.5").strip())
        backoff = max(0.1, min(5.0, backoff))  # 0.1-5.0 arası sınırla
    except ValueError:
        backoff = 0.5
        if logger:
            logger.warning(f"Invalid {prefix}BACKOFF value, using default: 0.5")

    sender = ThingsBoardSender(
        base_url=base_url,
        access_token=token,
        timeout=timeout,
        verify=verify,
        max_retries=retries,
        backoff_factor=backoff,
        logger=logger,
        enable_metrics=enable_metrics,
    )
    
    if logger:
        logger.info(f"ThingsBoard sender created: {base_url}, retries={retries}, backoff={backoff}")
    
    return sender
