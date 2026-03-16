# Smart Saw

## What This Is

Smart Saw endustriyel testere kontrol ve goruntu isleme sistemi. PLC uzerinden Modbus TCP ile 10 Hz veri okuma, ML tabanli kesim kontrolu, 9 anomali dedektoru, dokunmatik ekran destegi ve IoT telemetri ozelliklerinin yaninda, kamera tabanli yapay zeka ile serit testere dis kirigi, catlak ve asinma tespiti yaparak testere saglik durumunu izler.

## Core Value

Endustriyel testere operasyonlarinin guvenilir kontrolu ve serit testere sagliginin yapay zeka ile surekli izlenmesi — kesim kalitesi ve operator guvenligi icin kritik.

## Current Milestone: v2.0 Camera Vision & AI Detection

**Goal:** Eski projedeki kamera/AI vision sistemini moduler ve config-driven olarak entegre ederek serit testere dis kirigi, catlak ve asinma tespiti yetenegi kazandirmak.

**Target features:**
- Kamera modulu (OpenCV frame capture + JPEG recording)
- Kirik dis tespiti (RT-DETR model)
- Catlak tespiti (RT-DETR model)
- Asinma tespiti (LDC edge detection + wear calculation)
- Testere saglik hesaplayicisi (kirik + asinma bazli)
- Kamera GUI sayfasi (canli goruntu, tespit sonuclari, asinma %, saglik durumu)
- Config-driven modulerlik (camera.enabled=false → sifir kamera kodu yuklenir)
- DB entegrasyonu (tespit sonuclari SQLite'a kaydedilir)
- IoT entegrasyonu (tespit sonuclari ThingsBoard'a gonderilir)

## Requirements

### Validated

- ✓ Modbus TCP ile PLC haberlesmesi — existing
- ✓ 10 Hz veri okuma ve isleme — existing
- ✓ Manuel ve ML kontrol modlari — existing
- ✓ 9 anomali dedektoru — existing
- ✓ SQLite veritabanlari (raw, total, log, ml, anomaly) — existing
- ✓ PySide6 desktop GUI — existing
- ✓ ThingsBoard IoT telemetri — existing
- ✓ PostgreSQL uzak veritabani destegi — existing
- ✓ ML database'ine tork (serit_motor_tork) alani eklenmesi — v1.0
- ✓ ML database'ine kafa yuksekligi (kafa_yuksekligi) alani eklenmesi — v1.0
- ✓ Anomali database'ine kafa yuksekligi (kafa_yuksekligi) alani eklenmesi — v1.0
- ✓ Modbus connection cooldown mekanizmasi — v1.1
- ✓ Modbus operation timeout wrappers — v1.1
- ✓ ML kesim sonrasi otomatik hiz restorasyonu — v1.2
- ✓ Dinamik grafik eksen etiketleri (Y-axis, X-axis) — v1.2
- ✓ Lock-free asyncio.Queue for MQTT batching — v1.3
- ✓ Vibration DBSCAN to IQR algorithm optimization — v1.3
- ✓ AnomalyManager lock consolidation (9 → 1 per cycle) — v1.3
- ✓ Thread-safe GUI→main thread asyncio scheduling — v1.4
- ✓ Mode-aware initial delay (ML-only) — v1.4
- ✓ ML prediction parity with old codebase (averaged buffer values) — v1.5
- ✓ Torque-to-current without clamping (old code polynomial behavior) — v1.5
- ✓ GUI labels with units (mm/dk, m/dk, A, %) — v1.5
- ✓ Consistent "Ilerleme" terminology (replacing "Inme") — v1.5
- ✓ Band deviation graph axis title labels — v1.5
- ✓ Y-axis range always includes zero reference — v1.5
- ✓ Dokunmatik ekran long press fix — konumlandirma butonlarinda touch event handling — v1.6
- ✓ ML DB None degerleri duzeltme — yeni hiz/katsayi alanlari doldurma — v1.6
- ✓ ML DB kesim_id, makine_id, serit_id, malzeme_cinsi eklenmesi — v1.6
- ✓ Anomaly DB makine_id, serit_id, malzeme_cinsi eklenmesi — v1.6

### Active

- [x] Config-driven kamera modulu (camera.enabled ile acilip kapatilabilir) — S22
- [x] OpenCV frame capture ve JPEG recording sistemi — S20
- [x] RT-DETR kirik dis tespiti (best.pt model) — S21
- [x] RT-DETR catlak tespiti (catlak-best.pt model) — S21
- [x] LDC edge detection + asinma hesaplama pipeline — S21
- [x] Testere saglik hesaplayicisi (kirik %70 + asinma %30) — S21
- [x] PySide6 kamera sayfasi (canli goruntu, tespit sonuclari, asinma, saglik) — S24
- [x] GUI sidebar'a kamera navigasyon butonu eklenmesi — S24
- [x] Tespit sonuclarinin SQLite'a kaydedilmesi — S22
- [x] Tespit sonuclarinin ThingsBoard IoT'a gonderilmesi — S23
- [x] Lifecycle'da kamera servislerinin config-driven baslatilmasi — S22

### Out of Scope

- ML modeli degisikligi — bu alanlar sadece kayit amacli, model inputu degil
- Yeni anomali dedektoru — kafa yuksekligi sadece kayit icin, tespit icin degil
- Mobile app — web-first approach, industrial panel PC yeterli
- Multi-touch gestures — simple hold action yeterli
- Database migration framework (Alembic) — SQLite ALTER TABLE yeterli
- Real-time traceability dashboards — veri toplama once, gorsellestirme sonra

## Context

**Current State (v2.0 M001 complete — all 24 slices shipped):**
- ML predictions tablosu: `akim_input`, `sapma_input`, `kesme_hizi_input`, `inme_hizi_input`, `serit_motor_tork`, `kafa_yuksekligi`, `yeni_kesme_hizi`, `yeni_inme_hizi`, `katsayi`, `ml_output`, `kesim_id`, `makine_id`, `serit_id`, `malzeme_cinsi`
- Anomaly events tablosu: `timestamp`, `sensor_name`, `sensor_value`, `detection_method`, `kesim_id`, `kafa_yuksekligi`, `makine_id`, `serit_id`, `malzeme_cinsi`
- TouchButton widget: Qt touch events, instant activation, strict bounds, first-touch-wins, emergency stop overlay
- AsyncModbusService: Connection cooldown (10s default), operation timeouts via asyncio.wait_for
- MLController: Automatic speed save/restore around ML cuts; uses averaged buffer speeds; deferred logging pattern
- CuttingGraphWidget: Dynamic axis title labels with Turkish character support
- BandDeviationGraphWidget: Axis title labels (Sapma/Zaman), Y-axis always includes zero
- SQLiteService: Automatic schema mismatch detection and database recreation with backup
- MQTTClient: Lock-free asyncio.Queue for telemetry batching (O(1) queue_telemetry)
- AnomalyDetectors: IQR method for all vibration sensors (TitresimX/Y/Z)
- AnomalyManager: Single atomic lock acquisition per process_data() cycle
- GUI→Async: Event loop propagation through GUI init chain, run_coroutine_threadsafe() for mode switching
- ControlManager: Mode-aware initial delay (ML-only, manual mode bypasses)
- GUI Labels: Units (mm/dk, m/dk, A, %) on all numerical values; "Ilerleme" terminology
- PositioningController: TouchButton for 4 positioning buttons with emergency stop overlay
- CameraResultsStore: Thread-safe Lock-guarded key-value store for camera pipeline state
- CameraService: Config-driven capture engine with daemon threads, JPEG encoding, recording to disk
- Camera foundation: config.yaml camera section, SCHEMA_CAMERA_DB, lifecycle stub, zero-import guard
- DetectionWorker: Daemon thread with dual RT-DETR inference (broken tooth + crack), results to CameraResultsStore
- LDCWorker: Daemon thread with LDC edge detection + contour-based wear calculation + health scoring
- HealthCalculator: Standalone class (no torch dep) with 70/30 weighted health formula, Turkish status labels, hex colors
- modelB4.py: Vendored LDC network architecture (pure PyTorch)
- Lifecycle camera integration: _init_camera() creates CameraResultsStore → CameraService → DetectionWorker → LDCWorker with lazy imports; stop() tears down camera before SQLite flush
- Camera DB persistence: DetectionWorker writes broken_tooth/crack events to detection_events; LDCWorker writes wear measurements to wear_history; both via SQLiteService.write_async()
- IoT camera telemetry: CameraResultsStore.snapshot() → DataProcessingPipeline → MQTTService → ThingsBoardFormatter; 6 scalar fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) in flat ThingsBoard payload; vision_data=None for backward compat

- CameraController: QWidget with 3 QTimers (500ms frame, 1000ms stats, 2000ms health), reads exclusively from CameraResultsStore.snapshot(), QImage.loadFromData() for JPEG decoding, deque-based thumbnail history, OK/alert detection indicators, dynamic health color

**Tech Stack:**
- ~15,641 LOC Python
- v1.0-v1.5: schemas.py, ml_controller.py, anomaly_tracker.py, data_processor.py, client.py, config.yaml, manager.py, sensor_controller.py, sqlite_service.py, mqtt_client.py, detectors.py, lifecycle.py, app.py, main_controller.py, control_panel_controller.py, monitoring_controller.py, preprocessor.py
- v1.6: touch_button.py, positioning_controller.py, ml_controller.py, schemas.py, anomaly_tracker.py, data_processor.py

## Constraints

- **Geriye Uyumluluk**: Mevcut veritabani dosyalari korunmali, ALTER TABLE ile ekleme yapilmali
- **Veri Kaynagi**: Veriler mevcut `RawSensorData`/`ProcessedData` modellerinden alinacak

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Sadece kayit amacli ekleme | ML model inputu degismeyecek, geriye donuk analiz icin | ✓ Good |
| ALTER TABLE kullanimi | Mevcut veri kaybi onlenmeli | ✓ Good |
| Place ML columns in input features group | Logical ordering: input features together, output fields together | ✓ Good |
| Place kafa_yuksekligi after kesim_id | kesim_id is a reference while kafa_yuksekligi is measurement data | ✓ Good |
| Use instantaneous torque value | Direct raw_data.serit_motor_tork_percentage rather than buffer average | ✓ Good |
| Pass kafa_yuksekligi from raw_data directly | Value already available in scope at anomaly recording location | ✓ Good |
| 10 second default cooldown | Matches typical PLC recovery time | ✓ Good |
| Reuse existing timeout config | No new config complexity | ✓ Good |
| ModbusWriter dependency injection | MLController receives writer from ControlManager | ✓ Good |
| Async speed restoration | _reset_cutting_state is async to support await on Modbus writes | ✓ Good |
| Horizontal axis title labels | Qt text rotation is complex, horizontal text simpler | ✓ Good |
| Auto schema mismatch recovery | Backup old DB, recreate with new schema | ✓ Good |
| asyncio.Queue for MQTT batching | Native asyncio, O(1) put_nowait | ✓ Good |
| IQR for vibration detectors | O(n) vs DBSCAN O(n²) | ✓ Good |
| dict.update() for atomic state update | Simpler, equally thread-safe | ✓ Good |
| asyncio.run_coroutine_threadsafe() for GUI→main | Proper cross-thread async scheduling | ✓ Good |
| Event loop as optional parameter | Backward compatibility for standalone testing | ✓ Good |
| Initial delay inside ML branch only | Cleaner separation — manual mode never needs delay | ✓ Good |
| Use averaged buffer speeds for ML calculations | Matches old code behavior | ✓ Good |
| Remove torque clamping in torque_to_current | Old code polynomial behavior preserved | ✓ Good |
| Only change visible label text, keep variable names | Minimal code churn | ✓ Good |
| New get_axis_max/get_axis_min methods | Preserve existing get_max_value/get_min_value behavior | ✓ Good |
| Touch instant activation (0ms delay) | Industrial users expect immediate response | ✓ Good |
| Strict touch bounds, no tolerance zone | Prevents accidental adjacent button activation | ✓ Good |
| First button wins multi-touch | Prevents conflicting jog commands | ✓ Good |
| Emergency stop always responsive | Safety feature must be accessible | ✓ Good |
| Stop jog on focusOutEvent | Safety mechanism for backgrounded app | ✓ Good |
| Log calculated speeds, not threshold-dependent targets | Captures all ML decisions | ✓ Good |
| Deferred logging pattern | Log after calculation, not before | ✓ Good |
| NULL defaults for traceability columns | Preserves existing records without migration | ✓ Good |
| Falsy-to-None conversion at call site | Store NULL when source is 0 or empty string | ✓ Good |
| Index only on kesim_id | Low cardinality on makine_id/serit_id/malzeme_cinsi | ✓ Good |

---
*Last updated: 2026-03-16 after S24 Camera GUI complete — M001 milestone finished*
