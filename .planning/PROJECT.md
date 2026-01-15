# Smart Saw - Database Field Additions

## What This Is

Smart Saw endüstriyel testere kontrol sistemi için database şema güncellemesi. ML predictions tablosuna serit_motor_tork ve kafa_yuksekligi, anomaly events tablosuna kafa_yuksekligi alanları eklenerek geçmişe dönük analiz için veri kaydı zenginleştirildi.

## Core Value

ML ve anomali kayıtlarında tork ve kafa yüksekliği verilerinin saklanması — geçmişe dönük analiz için kritik verinin eksik kalmaması.

## Requirements

### Validated

- ✓ Modbus TCP ile PLC haberleşmesi — existing
- ✓ 10 Hz veri okuma ve işleme — existing
- ✓ Manuel ve ML kontrol modları — existing
- ✓ 9 anomali dedektörü — existing
- ✓ SQLite veritabanları (raw, total, log, ml, anomaly) — existing
- ✓ PySide6 desktop GUI — existing
- ✓ ThingsBoard IoT telemetri — existing
- ✓ PostgreSQL uzak veritabanı desteği — existing
- ✓ ML database'ine tork (serit_motor_tork) alanı eklenmesi — v1.0
- ✓ ML database'ine kafa yüksekliği (kafa_yuksekligi) alanı eklenmesi — v1.0
- ✓ Anomali database'ine kafa yüksekliği (kafa_yuksekligi) alanı eklenmesi — v1.0
- ✓ Modbus connection cooldown mekanizması — v1.1
- ✓ Modbus operation timeout wrappers — v1.1
- ✓ ML kesim sonrası otomatik hız restorasyonu — v1.2
- ✓ Dinamik grafik eksen etiketleri (Y-axis, X-axis) — v1.2
- ✓ Lock-free asyncio.Queue for MQTT batching — v1.3
- ✓ Vibration DBSCAN to IQR algorithm optimization — v1.3
- ✓ AnomalyManager lock consolidation (9 → 1 per cycle) — v1.3

### Active

(None — v1.3 milestone complete)

### Out of Scope

- ML modeli değişikliği — bu alanlar sadece kayıt amaçlı, model inputu değil
- Yeni anomali dedektörü — kafa yüksekliği sadece kayıt için, tespit için değil
- GUI değişiklikleri — backend schema değişikliği yeterli

## Context

**Current State (v1.3 shipped):**
- ML predictions tablosu: `akim_input`, `sapma_input`, `kesme_hizi_input`, `inme_hizi_input`, `serit_motor_tork`, `kafa_yuksekligi`, `yeni_kesme_hizi`, `yeni_inme_hizi`, `katsayi`, `ml_output`
- Anomaly events tablosu: `timestamp`, `sensor_name`, `sensor_value`, `detection_method`, `kesim_id`, `kafa_yuksekligi`
- AsyncModbusService: Connection cooldown (10s default), operation timeouts via asyncio.wait_for
- MLController: Automatic speed save/restore around ML cuts via ModbusWriter injection
- CuttingGraphWidget: Dynamic axis title labels with Turkish character support
- SQLiteService: Automatic schema mismatch detection and database recreation with backup
- MQTTClient: Lock-free asyncio.Queue for telemetry batching (O(1) queue_telemetry)
- AnomalyDetectors: IQR method for all vibration sensors (TitresimX/Y/Z)
- AnomalyManager: Single atomic lock acquisition per process_data() cycle

**Tech Stack:**
- ~14,000 LOC Python
- v1.0: schemas.py, ml_controller.py, anomaly_tracker.py, data_processor.py
- v1.1: client.py, config.yaml
- v1.2: ml_controller.py, manager.py, sensor_controller.py, sqlite_service.py
- v1.3: mqtt_client.py, detectors.py, manager.py

## Constraints

- **Geriye Uyumluluk**: Mevcut veritabanı dosyaları korunmalı, ALTER TABLE ile ekleme yapılmalı
- **Veri Kaynağı**: Veriler mevcut `RawSensorData`/`ProcessedData` modellerinden alınacak

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Sadece kayıt amaçlı ekleme | ML model inputu değişmeyecek, geriye dönük analiz için | ✓ Good |
| ALTER TABLE kullanımı | Mevcut veri kaybı önlenmeli | ✓ Good |
| Place ML columns in input features group | Logical ordering: input features together, output fields together | ✓ Good |
| Place kafa_yuksekligi after kesim_id | kesim_id is a reference while kafa_yuksekligi is measurement data | ✓ Good |
| Use instantaneous torque value | Direct raw_data.serit_motor_tork_percentage rather than buffer average | ✓ Good |
| Pass kafa_yuksekligi from raw_data directly | Value already available in scope at anomaly recording location | ✓ Good |
| 10 second default cooldown | Matches typical PLC recovery time, good balance between responsiveness and blocking prevention | ✓ Good |
| Reuse existing timeout config | No new config complexity, existing timeout value (5.0s) sufficient for operation wrappers | ✓ Good |
| ModbusWriter dependency injection | MLController receives writer from ControlManager, allows optional speed restoration | ✓ Good |
| Async speed restoration | _reset_cutting_state is async to support await on Modbus writes | ✓ Good |
| Horizontal axis title labels | Qt text rotation is complex, horizontal text simpler and readable | ✓ Good |
| Auto schema mismatch recovery | Backup old DB with timestamp, recreate with new schema, continue without restart | ✓ Good |
| asyncio.Queue for MQTT batching | Native asyncio, no GIL concerns, O(1) put_nowait | ✓ Good |
| IQR for vibration detectors | O(n) vs DBSCAN O(n²), consistent with other detectors | ✓ Good |
| dict.update() for atomic state update | Simpler than individual key assignments, equally thread-safe | ✓ Good |

---
*Last updated: 2026-01-15 after v1.3 milestone*
