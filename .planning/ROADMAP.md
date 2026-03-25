# Roadmap: Smart Saw

## Overview

Endustriyel testere kontrol sistemine kamera tabanli yapay zeka goruntusu entegrasyonu. v1.0'dan v1.6'ya uzanan veritabani, performans ve dokunmatik ekran milestonelari tamamlandi; v2.0 ile OpenCV frame capture, RT-DETR kirik/catlak tespiti, LDC asınma hesaplamasi ve PySide6 kamera GUI sayfasi `camera.enabled` config flagi arkasinda sifir etkiyle entegre edilecek.

## Milestones

- ✅ [v1.0 Database Field Additions](milestones/v1.0-ROADMAP.md) (Phases 1-3) — SHIPPED 2026-01-15
- ✅ [v1.1 Modbus Connection Resilience](milestones/v1.1-ROADMAP.md) (Phase 4) — SHIPPED 2026-01-15
- ✅ [v1.2 ML Speed Memory & Chart UX](milestones/v1.2-ROADMAP.md) (Phases 5-6) — SHIPPED 2026-01-15
- ✅ [v1.3 Processing Performance](milestones/v1.3-ROADMAP.md) (Phases 7-9) — SHIPPED 2026-01-15
- ✅ [v1.4 Control Mode Fixes](milestones/v1.4-ROADMAP.md) (Phases 10-11) — SHIPPED 2026-01-28
- ✅ [v1.5 ML Parity & UX Polish](milestones/v1.5-ROADMAP.md) (Phases 12-14) — SHIPPED 2026-01-28
- ✅ [v1.6 Touch UX & Data Traceability](milestones/v1.6-ROADMAP.md) (Phases 15-18) — SHIPPED 2026-03-16
- 🚧 **v2.0 Camera Vision & AI Detection** — Phases 19-24 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

<details>
<summary>✅ v1.0 Database Field Additions (Phases 1-3) — SHIPPED 2026-01-15</summary>

- [x] Phase 1: ML Schema Update (1/1 plans) — completed 2026-01-15
- [x] Phase 2: Anomaly Schema Update (1/1 plans) — completed 2026-01-15
- [x] Phase 3: Data Population (2/2 plans) — completed 2026-01-15

</details>

<details>
<summary>✅ v1.1 Modbus Connection Resilience (Phase 4) — SHIPPED 2026-01-15</summary>

- [x] Phase 4: Modbus Connection Timeout Handling (1/1 plans) — completed 2026-01-15

</details>

<details>
<summary>✅ v1.2 ML Speed Memory & Chart UX (Phases 5-6) — SHIPPED 2026-01-15</summary>

- [x] Phase 5: ML Speed Restoration (1/1 plans) — completed 2026-01-15
- [x] Phase 6: Dynamic Chart Axis Labels (1/1 plans) — completed 2026-01-15

</details>

<details>
<summary>✅ v1.3 Processing Performance (Phases 7-9) — SHIPPED 2026-01-15</summary>

- [x] Phase 7: MQTT Lock-Free Queue (1/1 plans) — completed 2026-01-15
- [x] Phase 8: Vibration DBSCAN to IQR (1/1 plans) — completed 2026-01-15
- [x] Phase 9: AnomalyManager Lock Consolidation (1/1 plans) — completed 2026-01-15

</details>

<details>
<summary>✅ v1.4 Control Mode Fixes (Phases 10-11) — SHIPPED 2026-01-28</summary>

- [x] Phase 10: AI Mode Switch Fix (1/1 plans) — completed 2026-01-15
- [x] Phase 11: Initial Delay Logic (1/1 plans) — completed 2026-01-15

</details>

<details>
<summary>✅ v1.5 ML Parity & UX Polish (Phases 12-14) — SHIPPED 2026-01-28</summary>

- [x] Phase 12: ML Prediction Parity Investigation & Fix (1/1 plans) — completed 2026-01-28
- [x] Phase 13: Unit Labels & Naming Fixes (1/1 plans) — completed 2026-01-28
- [x] Phase 14: Chart Axis Labels & Sapma Gauge Fix (1/1 plans) — completed 2026-01-28

</details>

<details>
<summary>✅ v1.6 Touch UX & Data Traceability (Phases 15-18) — SHIPPED 2026-03-16</summary>

- [x] Phase 15: Touch Long Press Fix (1/1 plans) — completed 2026-01-30
- [x] Phase 16: ML DB None Values Investigation (1/1 plans) — completed 2026-02-04
- [x] Phase 17: ML DB Schema Update (1/1 plans) — completed 2026-03-16
- [x] Phase 18: Anomaly DB Schema Update (1/1 plans) — completed 2026-03-16

</details>

### 🚧 v2.0 Camera Vision & AI Detection (In Progress)

**Milestone Goal:** Kamera tabanli yapay zeka ile serit testere dis kirigi, catlak ve asinma tespiti; camera.enabled=false oldugunda sifir kod yuklenir.

- [x] **Phase 19: Foundation** - numpy unblocker, camera config schema, camera.db schema, config-driven zero-import guard (completed 2026-03-16)
- [ ] **Phase 20: Camera Capture** - OpenCV frame capture thread, JPEG encoder, recordings directory structure
- [ ] **Phase 21: AI Detection Pipeline** - RT-DETR broken/crack detection, LDC wear, health calculator, CameraResultsStore
- [ ] **Phase 22: Lifecycle & DB Integration** - VisionService orchestration, lifecycle _init_camera(), detection results to SQLite
- [ ] **Phase 23: IoT Integration** - Detection results appended to existing ThingsBoard telemetry batch
- [ ] **Phase 24: Camera GUI** - Live feed, detection stats, wear %, health score, thumbnails, icons, sidebar button

## Phase Details

### Phase 19: Foundation
**Goal**: Kamera modulunun acilip kapatilabilmesi ve bagimlilik zincirinin kurulmasi — camera.enabled=false iken hicbir kamera kodu yuklenmez
**Depends on**: Phase 18 (v1.6 complete)
**Requirements**: CAM-01, CAM-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. `camera.enabled: false` (varsayilan) ile uygulama baslatildiginda cv2, torch, ultralytics import edilmez
  2. `camera.enabled: true` ile baslatildiginda camera config alanlari (device_id, fps, resolution, model paths) okunur
  3. Lifecycle'da camera.db dosyasi yalnizca camera.enabled=true iken olusturulur; false iken disk'e dokunulmaz
  4. requirements.txt'teki numpy<2.0 kapi kaldirilir; opencv-python-headless, ultralytics, torch (CPU), kornia bagimliliklar eklenir
**Plans**: 1 plan

Plans:
- [ ] 19-01: numpy uncap + np.ptp fix + camera config schema + SCHEMA_CAMERA_DB + lifecycle _init_camera() + camera module scaffold

### Phase 19.2: Graph axis labels (INSERTED)

**Goal:** Show currently selected X and Y axis variable names as static labels inside kesimGrafigiFrame, updating dynamically on axis button clicks
**Requirements**: none
**Depends on:** Phase 19
**Plans:** 1/1 plans complete

Plans:
- [ ] 19.2-01-PLAN.md — Reposition and resize y_axis_title and x_axis_title labels to user-specified coordinates with 20pt font

### Phase 19.1: UI Refinements (INSERTED) — COMPLETE 2026-03-25

**Goal:** Urgent touch UX improvements — NumpadDialog close button and speed pre-fill
**Requirements**: none
**Depends on:** Phase 19
**Plans:** 1/1 plans complete

Plans:
- [x] 19.1-01: NumpadDialog close button + initial_value pre-fill + first-keystroke replacement — completed 2026-03-25

### Phase 20: Camera Capture
**Goal**: Kameradan frame alimi ve JPEG kaydi — asyncio event loop'u hic bloklamadan arka plan thread'lerinde calisir
**Depends on**: Phase 19
**Requirements**: CAM-03, CAM-04, CAM-05
**Success Criteria** (what must be TRUE):
  1. CameraService baslatildiginda OpenCV capture thread'i arkaplanda doner; uygulama ana dongusu yavaslamamaz
  2. Kameradan alinan frame'ler `recordings/YYYYMMDD-HHMMSS/` klasorune JPEG olarak yazilir
  3. CameraResultsStore'daki `latest_frame` alani her yeni frame sonrasi guncellenir (thread-safe)
  4. Config'deki cozunurluk ve FPS degerleri gercekte VideoCapture'a uygulanir
**Plans**: TBD

Plans:
- [ ] 20-01: CameraResultsStore (results_store.py) + CameraService (camera_service.py) — capture thread + JPEG encoder

### Phase 21: AI Detection Pipeline
**Goal**: RT-DETR ve LDC modellerinin kendi thread'lerinde calisarak tespit sonuclarini CameraResultsStore'a yazmasi
**Depends on**: Phase 20
**Requirements**: DET-01, DET-02, DET-03, DET-04, DET-05, DET-06
**Success Criteria** (what must be TRUE):
  1. DetectionWorker kirik dis ve catlak sayisini RT-DETR ile tespit eder; sonuclar CameraResultsStore'a yazilir
  2. LDCWorker serit asinma yuzdesini hesaplar; sonuc CameraResultsStore'a yazilir
  3. SawHealthCalculator saglik skorunu (kirik %70 + asinma %30) hesaplar; CameraResultsStore'da gorunur
  4. Modeller kendi thread run() metodunda yuklenir — lifecycle startup'ini bloklamaz
  5. Broken ve crack modeli tek thread'de sirayla calisir — model nesneleri thread'ler arasinda paylasilmaz
**Plans**: TBD

Plans:
- [ ] 21-01: DetectionWorker (broken + crack RT-DETR) + CameraResultsStore detection fields
- [ ] 21-02: LDCWorker (edge detection + wear %) + SawHealthCalculator

### Phase 22: Lifecycle & DB Integration
**Goal**: Kamera servislerinin uygulama lifecyle'ina baglanmasi ve tespit sonuclarinin SQLite'a yazilmasi
**Depends on**: Phase 21
**Requirements**: DATA-01, DATA-03
**Success Criteria** (what must be TRUE):
  1. Uygulama baslatildiginda `_init_camera()` adimi kamera thread'lerini baslatir; kapanisda temiz durdurmaz
  2. Her tespit sonucu camera.db'ye (detection_events ve wear_history tablolari) SQLiteService queue pattern ile yazilir
  3. camera.db'ye yazma hatalari ana kontrol dongusunu etkilemez (exception izole edilir)
  4. camera.enabled=false iken lifecycle hicbir kamera nesnesi olusturmaz
**Plans**: TBD

Plans:
- [ ] 22-01: VisionService (scheduling orchestration) + lifecycle _init_camera() lazy import + camera.db writes

### Phase 23: IoT Integration
**Goal**: Tespit sonuclarinin mevcut ThingsBoard telemetri batch'ine eklenerek IoT'a iletilmesi
**Depends on**: Phase 22
**Requirements**: DATA-02
**Success Criteria** (what must be TRUE):
  1. 10 Hz veri dongusunda CameraResultsStore snapshot'i alinir; kamera alanlari ThingsBoard payload'una eklenir
  2. camera.enabled=false iken IoT payload degismez — hic kamera alani eklenmez
  3. Kamera alanlari mevcut telemetri batch'ine eklenirken hicbir mevcut alan kaybolmaz
**Plans**: TBD

Plans:
- [ ] 23-01: DataProcessingPipeline optional camera_results_store parameter + IoT snapshot integration

### Phase 24: Camera GUI
**Goal**: Operatorun kamera sayfasinda canli goruntu, tespit sonuclari, asinma ve saglik durumunu gorebilmesi
**Depends on**: Phase 22
**Requirements**: GUI-01, GUI-02, GUI-03, GUI-04, GUI-05, GUI-06, GUI-07, GUI-08, GUI-09
**Success Criteria** (what must be TRUE):
  1. Kamera sayfasinda canli kamera goruntusu 500 ms'de bir guncellenir; diger sayfalar etkilenmez
  2. Kirik dis ve catlak sayisi ile son tespit zaman damgasi sayfada goruntulenir
  3. Asinma yuzdesi ve testere saglik skoru (renk kodu + durum metni) sayfada goruntulenir
  4. Son 4 kaydedilen frame thumbnail olarak goruntulenir
  5. Sidebar'da 5. navigasyon butonu yalnizca camera.enabled=true iken gozukur; false iken sidebar degismez
  6. Her tespit kategorisi icin OK/alert ikonu ve asinma olcum overlay goruntulenir
**Plans**: TBD

Plans:
- [ ] 24-01: CameraController Qt widget (QTimers, live feed, stats display, health color coding)
- [ ] 24-02: Thumbnails panel + OK/alert icons + wear visualization overlay + sidebar nav button

## Progress

**Execution Order:**
Phases execute in numeric order: 19 → 20 → 21 → 22 → 23 → 24

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. ML Schema Update | v1.0 | 1/1 | Complete | 2026-01-15 |
| 2. Anomaly Schema Update | v1.0 | 1/1 | Complete | 2026-01-15 |
| 3. Data Population | v1.0 | 2/2 | Complete | 2026-01-15 |
| 4. Modbus Connection Timeout Handling | v1.1 | 1/1 | Complete | 2026-01-15 |
| 5. ML Speed Restoration | v1.2 | 1/1 | Complete | 2026-01-15 |
| 6. Dynamic Chart Axis Labels | v1.2 | 1/1 | Complete | 2026-01-15 |
| 7. MQTT Lock-Free Queue | v1.3 | 1/1 | Complete | 2026-01-15 |
| 8. Vibration DBSCAN to IQR | v1.3 | 1/1 | Complete | 2026-01-15 |
| 9. AnomalyManager Lock Consolidation | v1.3 | 1/1 | Complete | 2026-01-15 |
| 10. AI Mode Switch Fix | v1.4 | 1/1 | Complete | 2026-01-15 |
| 11. Initial Delay Logic | v1.4 | 1/1 | Complete | 2026-01-15 |
| 12. ML Prediction Parity Investigation & Fix | v1.5 | 1/1 | Complete | 2026-01-28 |
| 13. Unit Labels & Naming Fixes | v1.5 | 1/1 | Complete | 2026-01-28 |
| 14. Chart Axis Labels & Sapma Gauge Fix | v1.5 | 1/1 | Complete | 2026-01-28 |
| 15. Touch Long Press Fix | v1.6 | 1/1 | Complete | 2026-01-30 |
| 16. ML DB None Values Investigation | v1.6 | 1/1 | Complete | 2026-02-04 |
| 17. ML DB Schema Update | v1.6 | 1/1 | Complete | 2026-03-16 |
| 18. Anomaly DB Schema Update | v1.6 | 1/1 | Complete | 2026-03-16 |
| 19. Foundation | v2.0 | 1/1 | Complete | 2026-03-16 |
| 19.1. UI Refinements (INSERTED) | v2.0 | Complete    | 2026-03-25 | 2026-03-25 |
| 19.2. Graph Axis Labels (INSERTED) | 1/1 | Complete    | 2026-03-25 | - |
| 20. Camera Capture | v2.0 | 0/1 | Not started | - |
| 21. AI Detection Pipeline | v2.0 | 0/2 | Not started | - |
| 22. Lifecycle & DB Integration | v2.0 | 0/1 | Not started | - |
| 23. IoT Integration | v2.0 | 0/1 | Not started | - |
| 24. Camera GUI | v2.0 | 0/2 | Not started | - |
