# Phase 22: Lifecycle & DB Integration - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Kamera servislerinin uygulama lifecycle'ina baglanmasi ve tespit sonuclarinin SQLite'a yazilmasi. VisionService orchestrator'u testere durumuna gore recording tetikler, worker'lar tespit sonuclarini camera.db'ye yazar, tum kamera bilesenlerinin lifecycle'a temiz entegrasyonu saglanir.

</domain>

<decisions>
## Implementation Decisions

### VisionService Orchestration
- **D-01:** VisionService daemon thread olarak calisir (DetectionWorker, LDCWorker ile ayni pattern). asyncio event loop'u bloklamaz.
- **D-02:** VisionService testere durumunu CameraResultsStore uzerinden okur. DataProcessingPipeline her dongude testere_durumu'nu CameraResultsStore'a yazar, VisionService oradan periyodik polling yapar.
- **D-03:** Recording tetikleme: testere_durumu 3'den (CUTTING) farkli bir degere gectiginde (kesim sonu) start_recording() cagrilir. Testere yuzeyi gorunur hale geldiginde kayit baslar (Phase 20 D-03 ile uyumlu).

### DB Yazma
- **D-04:** Worker'lardaki mevcut write_async() cagrilari schema ile tam uyumlu — detection_events ve wear_history tablolarinin tum sutunlari dogru eslestirilmis.
- **D-05:** Traceability alanlari (kesim_id, makine_id, serit_id, malzeme_cinsi) VisionService tarafindan CameraResultsStore'a yazilir, worker'lar oradan okuyup DB'ye kaydeder. DataProcessingPipeline zaten bu degerleri uretiyor.
- **D-06:** image_path ve edge_pixel_count alanlari da Phase 22'de doldurulacak — worker'lar zaten annotated frame kaydediyor ve edge pixel hesapliyor, bu degerleri DB'ye de yazacaklar. Tam veri butunlugu saglanir.

### Hata Izolasyonu
- **D-07:** VisionService polling/recording hatalarinda: logla ve devam et. Hata loglanir, bir sonraki polling cycle'da tekrar dener. VisionService thread'i olmez, ana dongu etkilenmez. Mevcut worker pattern'i ile tutarli.
- **D-08:** Mevcut izolasyon yeterli: _init_camera() try/except ile sarili (baslama hatasi ana uygulamayi durdurmaz), worker DB hatalari loglanip atlaniyor, DataProcessingPipeline kamera koduyla dogrudan temas etmiyor.

### Shutdown Sirasi
- **D-09:** Shutdown sirasi: VisionService once durdurulur (recording tetiklemesi kesilir), sonra DetectionWorker ve LDCWorker (son cycle tamamlanir), sonra CameraService. Orchestrator ustten asagiya kapanir.
- **D-10:** Worker'lar durdurulurken mevcut cycle tamamlanir ve son DB write'lar yapilir (flush sonra dur). SQLiteService kendi shutdown'unda da flush yapiyor — cift katmanli veri koruma.

### Claude's Discretion
- VisionService polling intervali (testere_durumu kontrol sikligi)
- CameraResultsStore'a testere_durumu yazma yeri (DataProcessingPipeline'in hangi noktasinda)
- Recording durdurma zamanlama mantigi (kesim sonu gecisinden kac saniye sonra stop)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Lifecycle & Integration
- `src/core/lifecycle.py` — _init_camera() (satir 383+) ve shutdown sequence (satir 150+). Mevcut lazy import pattern, camera services baslama/durdurma sirasi.
- `src/services/processing/data_processor.py` — DataProcessingPipeline, testere_durumu islemesi, 10 Hz dongu

### Camera Services
- `src/services/camera/camera_service.py` — CameraService: start_recording()/stop_recording() API (Phase 22 VisionService tetikleyecek)
- `src/services/camera/results_store.py` — CameraResultsStore: thread-safe key-value store API
- `src/services/camera/detection_worker.py` — DetectionWorker: DB write_async cagrilari (satir 210-233)
- `src/services/camera/ldc_worker.py` — LDCWorker: DB write_async cagrilari (satir 158-168)

### Config ve Schema
- `config/config.yaml` §camera — Camera config section (detection, wear, health sub-keys)
- `src/services/database/schemas.py` — SCHEMA_CAMERA_DB (detection_events + wear_history tablolari, satir 263-312)

### Domain
- `src/domain/models.py` — TesereDurumu enum, testere_durumu alani (satir 57)
- `src/services/processing/cutting_tracker.py` — Cutting state gecis mantigi

### Onceki Phase Context'leri
- `.planning/phases/19-foundation/19-CONTEXT.md` — Foundation kararlari (camera.db olusturma, zero-import guard)
- `.planning/phases/20-camera-capture/20-CONTEXT.md` — Camera capture kararlari (start/stop recording API, tetikleme Phase 22'ye birakildi)
- `.planning/phases/21-ai-detection-pipeline/21-CONTEXT.md` — AI pipeline kararlari (worker DB yazma kodu hazir ama db_service=None, Phase 22'de inject)

### Requirements
- `.planning/REQUIREMENTS.md` §Data Integration — DATA-01 (SQLite'a kayit)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_init_camera()` (lifecycle.py:383) — Zaten CameraResultsStore, CameraService, DetectionWorker, LDCWorker baslatiyor ve camera_db_service inject ediyor. VisionService eklenmeli.
- `CameraResultsStore` (results_store.py) — Thread-safe store, update_batch/get/snapshot API. VisionService testere_durumu ve traceability alanlarini buraya yazacak.
- `CameraService.start_recording()` / `stop_recording()` — Phase 20'de implement edildi, VisionService tarafindan tetiklenecek.
- `SQLiteService.write_async()` — Queue-based async DB yazma pattern (worker'lar zaten kullaniyor).

### Established Patterns
- Daemon thread pattern — `threading.Thread(daemon=True)` (DetectionWorker, LDCWorker)
- `threading.Event()` ile stop signaling — Worker stop pattern
- Lazy import inside _init_camera() — camera modulleri sadece burada import edilir
- try/except ile izole baslama — _init_camera() hatasi ana uygulamayi durdurmaz

### Integration Points
- `DataProcessingPipeline` → `CameraResultsStore`: testere_durumu ve traceability alanlarini store'a yazmali (yeni)
- `VisionService` → `CameraResultsStore`: testere_durumu polling (yeni)
- `VisionService` → `CameraService`: start/stop recording tetikleme (yeni)
- Worker'lar → `CameraResultsStore`: traceability alanlarini okuyup DB'ye yazma (guncelleme)

</code_context>

<specifics>
## Specific Ideas

- VisionService, diger kamera worker'lariyla ayni daemon thread pattern'ini kullanmali — tutarlilik onemli
- Traceability alanlari DataProcessingPipeline'dan CameraResultsStore'a, oradan worker'lara akar. Dogrudan coupling yok.
- Kesim sonu gecisi (testere_durumu 3 → baska deger) recording'i tetikler — testere yuzeyi gorunur olunca kayit baslar
- Shutdown sirasi: VisionService → DetectionWorker → LDCWorker → CameraService (ustten asagiya)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 22-lifecycle-db-integration*
*Context gathered: 2026-03-26*
