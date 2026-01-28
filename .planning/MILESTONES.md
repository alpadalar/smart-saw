# Project Milestones: Smart Saw Database Field Additions

## v1.5 ML Parity & UX Polish (Shipped: 2026-01-28)

**Delivered:** ML tahmin hesaplamalarında eski kod ile tam eşitlik sağlandı ve GUI etiketlerinde birim/terminoloji düzeltmeleri yapıldı.

**Phases completed:** 12-14 (3 plans total)

**Key accomplishments:**

- ML speed calculations aligned with old codebase (averaged buffer values instead of raw current values)
- Torque-to-current conversion without clamping (matches old code polynomial behavior)
- GUI labels with units (mm/dk, m/dk, A, %) across control panel and monitoring pages
- Consistent "İlerleme" terminology replacing "İnme" throughout the interface
- Band deviation graph axis title labels (Sapma (mm), Zaman (s))
- Y-axis range always includes zero reference point for deviation gauge

**Stats:**

- 4 source files modified (preprocessor.py, ml_controller.py, control_panel_controller.py, monitoring_controller.py)
- ~14,432 lines Python (existing codebase)
- 3 phases, 3 plans, 9 tasks
- Same-day completion (2026-01-28)

**Git range:** `feat(12-01)` → `feat(14-01)`

**What's next:** Production validation of ML predictions matching old system behavior

---

## v1.4 Control Mode Fixes (Shipped: 2026-01-28)

**Delivered:** AI mode switch hatası ve manuel mod initial delay düzeltmeleri ile kontrol modu geçişleri güvenilir hale getirildi.

**Phases completed:** 10-11 (2 plans total)

**Key accomplishments:**

- Thread-safe asyncio scheduling via asyncio.run_coroutine_threadsafe() for GUI→main thread mode switching
- Event loop propagation through GUI initialization chain (lifecycle → app → controllers)
- Mode-aware initial delay logic — ML mode retains delay, manual mode gets immediate response
- Cross-thread async infrastructure established for future GUI→async needs

**Stats:**

- 5 source files modified (lifecycle.py, app.py, main_controller.py, control_panel_controller.py, manager.py)
- ~14,400 lines Python (existing codebase)
- 2 phases, 2 plans, 5 tasks
- Same-day completion (2026-01-15)

**Git range:** `feat(10-01)` → `docs(11-01)`

**What's next:** Production validation of mode switching behavior

---

## v1.3 Processing Performance (Shipped: 2026-01-15)

**Delivered:** Lock contention ve algoritma optimizasyonları ile 10 Hz data processing loop performansı iyileştirildi.

**Phases completed:** 7-9 (3 plans total)

**Key accomplishments:**

- Lock-free asyncio.Queue for MQTT telemetry batching — queue_telemetry() never blocks (O(1) with put_nowait)
- Vibration detectors migrated from DBSCAN to IQR — O(n²) → O(n) complexity for TitresimX/Y/Z
- AnomalyManager lock acquisitions consolidated — 9 separate locks → 1 atomic update per process_data() cycle
- All processing loop hot paths now lock-free or minimally locked

**Stats:**

- 3 files modified (mqtt_client.py, detectors.py, manager.py)
- ~14,000 lines Python (existing codebase)
- 3 phases, 3 plans, 6 tasks
- Same-day completion (2026-01-15)

**Git range:** `feat(07-01)` → `docs(09-01)`

**What's next:** Production monitoring of processing cycle times

---

## v1.2 ML Speed Memory & Chart UX (Shipped: 2026-01-15)

**Delivered:** ML kesim sonrası otomatik hız restorasyonu ve grafik eksenlerinde dinamik etiketler ile kullanıcı deneyimi iyileştirildi.

**Phases completed:** 5-6 (2 plans total)

**Key accomplishments:**

- Automatic save/restore of operator-set speeds around ML cutting sessions
- ModbusWriter integration via dependency injection for async speed writes
- Dynamic Y-axis title labels showing current metric name and unit (Kesme Hizi, Ilerleme Hizi, etc.)
- Dynamic X-axis title labels (Zaman, Yukseklik) with Turkish character support
- Auto schema mismatch detection and database recreation with backup

**Stats:**

- 5 files modified (ml_controller.py, manager.py, config.yaml, sensor_controller.py, sqlite_service.py)
- ~14,000 lines Python (existing codebase)
- 2 phases, 2 plans, 5 tasks
- Same-day completion (2026-01-15)

**Git range:** `feat(05-01)` → `feat(06-01)`

**What's next:** Monitor speed restoration behavior in production

---

## v1.1 Modbus Connection Resilience (Shipped: 2026-01-15)

**Delivered:** AsyncModbusService'e connection cooldown ve operation timeout eklenerek PLC erişilemez olduğunda uygulama donması önlendi.

**Phases completed:** 4 (1 plan total)

**Key accomplishments:**

- Connection cooldown mechanism prevents repeated 5-second blocking calls when PLC is offline
- Explicit asyncio.wait_for wrappers ensure operations never exceed timeout bounds
- Configurable connect_cooldown parameter (10s default) allows tuning based on PLC characteristics

**Stats:**

- 2 files modified (client.py, config.yaml)
- ~14,000 lines Python (existing codebase)
- 1 phase, 1 plan, 2 tasks
- Same-day completion (2026-01-15)

**Git range:** `feat(04-01)` → `docs(04-01)`

**What's next:** Monitor Modbus resilience in production

---

## v1.0 Database Field Additions (Shipped: 2026-01-15)

**Delivered:** ML ve anomali veritabanlarına tork ve kafa yüksekliği alanları eklenerek geçmişe dönük analiz için veri zenginleştirildi.

**Phases completed:** 1-3 (4 plans total)

**Key accomplishments:**

- Added serit_motor_tork and kafa_yuksekligi columns to ML predictions table for historical torque and head height analysis
- Added kafa_yuksekligi column to anomaly events table for recording head position during anomaly detection
- Updated ML controller to log torque and head height values with each prediction
- Updated anomaly tracker to record head height at the time of anomaly detection

**Stats:**

- 4 source files modified (schemas.py, ml_controller.py, anomaly_tracker.py, data_processor.py)
- ~14,000 lines Python (existing codebase with additions)
- 3 phases, 4 plans, 7 tasks
- Same-day completion (2026-01-15)

**Git range:** `feat(01-01)` → `feat(03-02)`

**What's next:** Data collection and validation with new fields in production

---
