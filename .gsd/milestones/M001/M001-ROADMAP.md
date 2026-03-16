# M001: Migration

**Vision:** Kamera tabanli yapay zeka ile serit testere dis kirigi, catlak ve asinma tespiti; v1.0-v1.6 veritabani, performans ve dokunmatik ekran iyilestirmeleri uzerine v2.0 Camera Vision & AI Detection.

## Success Criteria


## Slices

- [x] **S01: Ml Schema Update** `risk:medium` `depends:[]`
  > After this: Update ML predictions database schema to include torque and head height fields.
- [x] **S02: Anomaly Schema Update** `risk:medium` `depends:[S01]`
  > After this: Add kafa_yuksekligi (head height) field to anomaly_events table schema.
- [x] **S03: Data Population** `risk:medium` `depends:[S02]`
  > After this: Update ML prediction logging to include serit_motor_tork and kafa_yuksekligi values.
- [x] **S04: Modbus Timeout** `risk:medium` `depends:[S03]`
  > After this: Add connection cooldown and operation timeouts to AsyncModbusService to prevent application freezing when PLC is unreachable.
- [x] **S05: Ml Speed Restoration** `risk:medium` `depends:[S04]`
  > After this: Implement save/restore of cutting speeds around ML cuts.
- [x] **S06: Dynamic Chart Axis Labels** `risk:medium` `depends:[S05]`
  > After this: Add dynamic axis title labels to the cutting graph that update based on selected X/Y axis buttons.
- [x] **S07: Mqtt Lock Free Queue** `risk:medium` `depends:[S06]`
  > After this: MQTT telemetry uses lock-free asyncio.Queue instead of deque for O(1) batching.
- [x] **S08: Vibration Dbscan To Iqr** `risk:medium` `depends:[S07]`
  > After this: Replace DBSCAN with IQR for vibration anomaly detectors (TitresimX, TitresimY, TitresimZ).
- [x] **S09: Anomaly Manager Lock Consolidation** `risk:medium` `depends:[S08]`
  > After this: Consolidate 9 separate lock acquisitions into single lock acquisition in AnomalyManager.
- [x] **S10: Ai Mode Switch Fix** `risk:medium` `depends:[S09]`
  > After this: Fix cross-thread asyncio scheduling in GUI mode switch operations.
- [x] **S11: Initial Delay Logic** `risk:medium` `depends:[S10]`
  > After this: Make initial_delay logic mode-aware: only apply to ML mode, skip for manual mode.
- [x] **S12: Ml Prediction Parity** `risk:medium` `depends:[S11]`
  > After this: Fix ML prediction parity by aligning speed calculation logic with old codebase.
- [x] **S13: Unit Labels Naming** `risk:medium` `depends:[S12]`
  > After this: Add units (mm/dk, m/dk, A, %) to numerical labels and rename "İnme Hızı" → "İlerleme Hızı" across all GUI pages.
- [x] **S14: Chart Axis Sapma Gauge** `risk:medium` `depends:[S13]`
  > After this: Add axis title labels to band deviation graph and fix Y-axis labels to always show a range that includes zero.
- [x] **S15: Touch Long Press Fix** `risk:medium` `depends:[S14]`
  > After this: TouchButton widget enables hold-to-jog on touchscreen HMI with emergency stop overlay.
- [x] **S16: ML DB None Values Investigation** `risk:medium` `depends:[S15]`
  > After this: ML predictions table populates all 11 columns including yeni_kesme_hizi, yeni_inme_hizi, katsayi.
- [x] **S17: ML DB Schema Update** `risk:medium` `depends:[S16]`
  > After this: ml_predictions table includes kesim_id, makine_id, serit_id, malzeme_cinsi traceability columns.
- [x] **S18: Anomaly DB Schema Update** `risk:medium` `depends:[S17]`
  > After this: anomaly_events table includes makine_id, serit_id, malzeme_cinsi traceability columns.
- [x] **S19: Foundation** `risk:medium` `depends:[S18]`
  > After this: numpy cap removed, camera config schema defined, camera.db schema in schemas.py, zero-import guard active.
- [x] **S20: Camera Capture** `risk:medium` `depends:[S19]`
  > After this: OpenCV capture thread runs in background, JPEG frames written to recordings directory.
- [x] **S21: AI Detection Pipeline** `risk:medium` `depends:[S20]`
  > After this: RT-DETR broken/crack detection and LDC wear calculation run in dedicated threads with results in CameraResultsStore.
- [x] **S22: Lifecycle & DB Integration** `risk:medium` `depends:[S21]`
  > After this: Camera services start/stop in lifecycle, detection results written to camera.db via SQLiteService queue.
- [x] **S23: IoT Integration** `risk:medium` `depends:[S22]`
  > After this: Camera telemetry fields included in ThingsBoard payload when camera.enabled=true.
- [x] **S24: Camera GUI** `risk:medium` `depends:[S23]`
  > After this: Camera page with live feed, detection stats, wear %, health score, thumbnails, and sidebar nav button.
