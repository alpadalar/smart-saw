# Smart Saw

## What This Is

Smart Saw endustriyel testere kontrol ve goruntu isleme sistemi. PLC uzerinden Modbus TCP ile 10 Hz veri okuma, ML tabanli kesim kontrolu, 9 anomali dedektoru, dokunmatik ekran destegi ve IoT telemetri ozelliklerinin yaninda, kamera tabanli yapay zeka ile serit testere dis kirigi, catlak ve asinma tespiti yaparak testere saglik durumunu izler.

## Core Value

Endustriyel testere operasyonlarinin guvenilir kontrolu ve serit testere sagliginin yapay zeka ile surekli izlenmesi — kesim kalitesi ve operator guvenligi icin kritik.

## Current State

**M001 Migration complete** — all 24 slices shipped, all 28 requirements validated. System at v2.0.

## Requirements

### Validated (M001)

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
- ✓ Config-driven kamera modulu (camera.enabled ile acilip kapatilabilir) — v2.0 CAM-01
- ✓ Zero-import guard (camera.enabled=false → sifir kamera kodu yuklenir) — v2.0 CAM-02
- ✓ OpenCV frame capture ve JPEG recording sistemi — v2.0 CAM-03/04/05
- ✓ RT-DETR kirik dis tespiti (best.pt model) — v2.0 DET-01
- ✓ RT-DETR catlak tespiti (catlak-best.pt model) — v2.0 DET-02
- ✓ LDC edge detection + asinma hesaplama pipeline — v2.0 DET-03
- ✓ Testere saglik hesaplayicisi (kirik %70 + asinma %30) — v2.0 DET-04
- ✓ Thread-safe CameraResultsStore integration boundary — v2.0 DET-05
- ✓ AI modelleri kendi thread'lerinde yuklenir — v2.0 DET-06
- ✓ Tespit sonuclari SQLite'a kaydedilir (camera.db) — v2.0 DATA-01
- ✓ Tespit sonuclari ThingsBoard IoT'a gonderilir — v2.0 DATA-02
- ✓ Kamera DB lifecycle'da config-driven olusturulur — v2.0 DATA-03
- ✓ Kamera sayfasi canli goruntu (QTimer + QImage) — v2.0 GUI-01
- ✓ Kirik dis tespit paneli (sayi, zaman damgasi) — v2.0 GUI-02
- ✓ Catlak tespit paneli (sayi, zaman damgasi) — v2.0 GUI-03
- ✓ Asinma yuzdesi goruntulenmesi — v2.0 GUI-04
- ✓ Saglik durumu (yuzde + durum + renk) — v2.0 GUI-05
- ✓ Sidebar 5. kamera butonu (sadece enabled iken) — v2.0 GUI-06
- ✓ 4 thumbnail sequential images paneli — v2.0 GUI-07
- ✓ OK/alert tespit ikonlari — v2.0 GUI-08
- ✓ Asinma olcum gorsellestirmesi — v2.0 GUI-09

### Out of Scope

- ML modeli degisikligi — bu alanlar sadece kayit amacli, model inputu degil
- Yeni anomali dedektoru — kafa yuksekligi sadece kayit icin, tespit icin degil
- Mobile app — web-first approach, industrial panel PC yeterli
- Multi-touch gestures — simple hold action yeterli
- Database migration framework (Alembic) — SQLite ALTER TABLE yeterli
- Real-time traceability dashboards — veri toplama once, gorsellestirme sonra

## Context

**Architecture:**
- ML predictions tablosu: 15 columns (akim_input, sapma_input, kesme_hizi_input, inme_hizi_input, serit_motor_tork, kafa_yuksekligi, yeni_kesme_hizi, yeni_inme_hizi, katsayi, ml_output, kesim_id, makine_id, serit_id, malzeme_cinsi + timestamp)
- Anomaly events tablosu: 9 columns (timestamp, sensor_name, sensor_value, detection_method, kesim_id, kafa_yuksekligi, makine_id, serit_id, malzeme_cinsi)
- Camera DB: detection_events + wear_history tables in camera.db
- Camera pipeline: config → lifecycle → CameraService (capture) → DetectionWorker (RT-DETR) + LDCWorker (LDC+contour) → CameraResultsStore → DB/IoT/GUI
- IoT: 6 camera fields flat in ThingsBoard payload alongside sensor data
- GUI: 5 pages (Control Panel, Sensor, Monitoring, Positioning, Camera) with conditional 5th button
- TouchButton widget for industrial touchscreen HMI with emergency stop overlay
- AsyncModbusService with connection cooldown and operation timeouts
- MLController with speed save/restore, averaged buffer speeds, deferred logging
- MQTTClient with lock-free asyncio.Queue batching
- AnomalyManager with single-lock consolidation, IQR for vibration detectors
- GUI→async via run_coroutine_threadsafe() with event loop propagation

**Tech Stack:**
- Python, PySide6, asyncio, SQLite, Modbus TCP
- OpenCV (headless), PyTorch, ultralytics (RT-DETR), vendored LDC model
- ThingsBoard IoT, MQTT

**Known Issues:**
- Pre-existing missing `src.services.iot.http_client` module blocks LifecycleManager runtime import
- All camera verification is contract-level — runtime validation requires camera hardware and model checkpoint files

## Constraints

- **Geriye Uyumluluk**: Mevcut veritabani dosyalari korunmali, ALTER TABLE ile ekleme yapilmali
- **Veri Kaynagi**: Veriler mevcut `RawSensorData`/`ProcessedData` modellerinden alinacak

## Key Decisions

See `.gsd/DECISIONS.md` for full decision register.
