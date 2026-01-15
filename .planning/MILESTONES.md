# Project Milestones: Smart Saw Database Field Additions

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
