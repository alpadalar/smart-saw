# Smart Saw

## What This Is

Smart Saw endustriyel testere kontrol ve goruntu isleme sistemi. PLC uzerinden Modbus TCP ile 10 Hz veri okuma, ML tabanli kesim kontrolu, 9 anomali dedektoru, dokunmatik ekran destegi ve IoT telemetri ozelliklerinin yaninda, kamera tabanli yapay zeka ile serit testere dis kirigi, catlak ve asinma tespiti yaparak testere saglik durumunu izler.

## Core Value

Endustriyel testere operasyonlarinin guvenilir kontrolu ve serit testere sagliginin yapay zeka ile surekli izlenmesi — kesim kalitesi ve operator guvenligi icin kritik.

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
- ✓ Config-driven kamera modulu (camera.enabled ile acilip kapatilabilir) — v2.0
- ✓ OpenCV frame capture ve JPEG recording sistemi — v2.0
- ✓ RT-DETR kirik dis ve catlak tespiti — v2.0
- ✓ LDC edge detection + asinma hesaplama pipeline — v2.0
- ✓ Testere saglik hesaplayicisi (kirik %70 + asinma %30) — v2.0
- ✓ VisionService lifecycle orchestration — v2.0
- ✓ PySide6 kamera sayfasi (canli goruntu, tespit sonuclari, asinma, saglik) — v2.0
- ✓ GUI sidebar'a kamera navigasyon butonu eklenmesi — v2.0
- ✓ Tespit sonuclarinin SQLite'a kaydedilmesi (camera.db) — v2.0
- ✓ Tespit sonuclarinin ThingsBoard IoT'a gonderilmesi — v2.0

### Active

(Next milestone requirements to be defined via `/gsd-new-milestone`)

### Out of Scope

- ML modeli degisikligi — bu alanlar sadece kayit amacli, model inputu degil
- Yeni anomali dedektoru — kafa yuksekligi sadece kayit icin, tespit icin degil
- Mobile app — web-first approach, industrial panel PC yeterli
- Multi-touch gestures — simple hold action yeterli
- Database migration framework (Alembic) — SQLite ALTER TABLE yeterli
- Real-time traceability dashboards — veri toplama once, gorsellestirme sonra
- Real-time AI inference during recording — CPU, RT-DETR'yi frame rate'inde calistiramaz
- Surekli video kaydi (MP4/AVI) — disk alani: ~54GB/30dk; JPEG sekans yeterli
- Multi-camera destegi — tek kamera yeterli
- opencv-python (full) kullanimi — Qt5/Qt6 symbol catismasi
- Model egitimi / fine-tuning — mevcut modeller kullanilacak

## Context

**Current State (v2.0 shipped 2026-04-08):**
- Camera vision pipeline: CameraService → DetectionWorker/LDCWorker → CameraResultsStore → GUI/IoT
- VisionService: Daemon thread polling at 0.5s, CUTTING transition triggers recording (10s duration)
- 50 unit tests for camera module (results_store, camera_service, detection_worker, ldc_worker, health_calculator, vision_service)
- HealthCalculator: Config-driven weights (broken_weight=0.7, wear_weight=0.3 from config.yaml)
- IoT: 6 camera fields in ThingsBoard telemetry (broken_count, crack_count, wear_percentage, health_score, etc.)
- All 23 v2.0 requirements verified through VERIFICATION.md reports

**Tech Stack:**
- ~15,641 LOC Python
- PySide6 desktop GUI with touch support
- AsyncModbusService (Modbus TCP, 10 Hz)
- SQLite databases: raw, total, log, ml, anomaly, camera
- ThingsBoard IoT telemetry via MQTT
- OpenCV + RT-DETR + LDC for camera vision
- Config-driven modular architecture (camera.enabled flag)

## Constraints

- **Geriye Uyumluluk**: Mevcut veritabani dosyalari korunmali, ALTER TABLE ile ekleme yapilmali
- **Veri Kaynagi**: Veriler mevcut `RawSensorData`/`ProcessedData` modellerinden alinacak
- **Qt Symbol Catismasi**: opencv-python-headless kullanilmali (full surum Qt ile catisir)
- **CPU Siniri**: RT-DETR real-time inference yapilamaz; record-then-detect pattern

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Sadece kayit amacli ekleme | ML model inputu degismeyecek, geriye donuk analiz icin | ✓ Good |
| ALTER TABLE kullanimi | Mevcut veri kaybi onlenmeli | ✓ Good |
| 10 second default cooldown | Matches typical PLC recovery time | ✓ Good |
| asyncio.Queue for MQTT batching | Native asyncio, O(1) put_nowait | ✓ Good |
| IQR for vibration detectors | O(n) vs DBSCAN O(n²) | ✓ Good |
| Touch instant activation (0ms delay) | Industrial users expect immediate response | ✓ Good |
| Falsy-to-None conversion at call site | Store NULL when source is 0 or empty string | ✓ Good |
| opencv-python-headless | Qt5/Qt6 symbol conflict on Linux | ✓ Good |
| CameraResultsStore as sole integration boundary | GUI and IoT only touch the store | ✓ Good |
| Camera threads are daemon threads | Never touch asyncio event loop | ✓ Good |
| Models loaded inside worker thread run() | Lifecycle startup unblocked | ✓ Good |
| Lazy imports behind camera.enabled guard | No ImportError when opencv not installed | ✓ Good |
| Auto-discovery scans 4 device IDs | Industrial robustness for USB ID shifts | ✓ Good |
| 30-second retry on capture loss | Transient USB disconnect recovery | ✓ Good |
| VisionService polls at 0.5s (2 Hz) | Configurable via vision.polling_interval | ✓ Good |
| Config-driven HealthCalculator weights | broken_weight/wear_weight from config.yaml | ✓ Good |
| annotated_frame unconditional store write | Bounding boxes always visible in live feed | ✓ Good |

---
*Last updated: 2026-04-08 after v2.0 Camera Vision & AI Detection milestone complete*
