# Phase 21: AI Detection Pipeline - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

RT-DETR ve LDC modellerinin kendi daemon thread'lerinde calisarak kirik dis, catlak ve asinma tespit sonuclarini CameraResultsStore'a yazmasi. DetectionWorker (broken + crack RT-DETR), LDCWorker (edge detection + wear %), SawHealthCalculator ve modelB4 (LDC NN mimarisi) mevcut eski proje kodlarinin audit/refactor edilmesiyle uretilecek.

</domain>

<decisions>
## Implementation Decisions

### Mevcut Kod Stratejisi
- **D-01:** Eski projeden gelen `detection_worker.py`, `ldc_worker.py`, `health_calculator.py` ve `modelB4.py` kodlari audit edilerek convention'lara uygun hale getirilecek. Algoritmik mantik (LDC inference pipeline, contour analizi, wear hesaplamasi, RT-DETR class mapping) korunacak, sadece stil/convention uyumu saglanacak (docstring formati, logging style, naming conventions, type hints).
- **D-02:** `modelB4.py` (LDC NN mimarisi) harici bir model dosyasi oldugu icin minimal degisiklikle korunacak — sadece gerekli lint/import duzeltmeleri.

### DB Yazma Kapsami
- **D-03:** Worker'lardaki DB yazma kodu (`db_service.write_async()` cagrilari) Phase 21'de korunacak. detection_events ve wear_history tablolarina yazma mevcut kodda zaten var. Phase 22'de sadece lifecycle baglantisi yapilacak (db_service instance'ini worker'lara inject etme).
- **D-04:** Phase 21'de worker'lar `db_service=None` varsayilani ile calisir — DB yazma kodu hazir ama aktif degil (lifecycle inject etmedigi surece).

### Annotated Frame Kaydetme
- **D-05:** `_save_annotated_frame()` metodu Phase 21 kapsaminda korunacak. Tespit edilen kirik dislere kirmizi, saglam dislere yesil, catlaklara mavi bounding box cizilip `recording_path/detected/` klasorune kaydedilir. Sadece aktif kayit varsa yazar, yoksa skip eder.

### Wear ROI Parametreleri
- **D-06:** LDC worker'daki hardcoded ROI sabitleri (`TOP_LINE_Y=170`, `BOTTOM_LINE_Y=236`, `_ROI_X_CENTER_N`, `_ROI_Y_CENTER_N`, `_ROI_WIDTH_N`, `_ROI_HEIGHT_N`) ve BGR mean degerleri `config.yaml` `camera.wear` altina tasinacak. Varsayilan degerler mevcut sabitlerle ayni kalacak. Farkli kamera kurulumlarinda degistirilebilir olacak.

### Claude's Discretion
- Convention audit sirasinda yapilacak spesifik degisikliklerin kapsami (hangi docstringler guncellenmeli, hangi logging pattern'leri duzeltilmeli)
- Test stratejisi — mock-based unit testlerin yapisi ve kapsami
- imgsz parametresinin (960) config'e tasinip tasinmamasi

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Mevcut Referans Kod (audit/refactor edilecek)
- `src/services/camera/detection_worker.py` — RT-DETR broken+crack detection worker (311 satir, mevcut)
- `src/services/camera/ldc_worker.py` — LDC edge detection + wear measurement worker (312 satir, mevcut)
- `src/services/camera/health_calculator.py` — Saw health calculator (96 satir, mevcut)
- `src/services/camera/modelB4.py` — LDC neural network architecture (harici model, minimal degisiklik)
- `src/services/camera/results_store.py` — CameraResultsStore (Phase 20'de yazildi, API kontrati)

### Model Dosyalari
- `data/models/best.pt` — RT-DETR broken tooth model (66MB)
- `data/models/catlak-best.pt` — RT-DETR crack model (66MB)
- `data/models/ldc/16_model.pth` — LDC checkpoint (2.7MB)

### Proje Convention'lari
- `.planning/codebase/CONVENTIONS.md` — Naming, docstring, error handling pattern'leri
- `.planning/codebase/ARCHITECTURE.md` — Concurrency model (asyncio + threading hybrid), service patterns

### Config ve Schema
- `config/config.yaml` §camera — Camera config section (detection, wear, health sub-keys)
- `src/services/database/schemas.py` — SCHEMA_CAMERA_DB (detection_events + wear_history tablolari)

### Onceki Phase Context'leri
- `.planning/phases/19-foundation/19-CONTEXT.md` — Foundation kararlari (numpy uncap, config schema, camera.db schema, zero-import guard)
- `.planning/phases/20-camera-capture/20-CONTEXT.md` — Camera capture kararlari (CameraService API, auto-discovery, recording pattern)

### Requirements
- `.planning/REQUIREMENTS.md` §AI Detection — DET-01 (kirik dis), DET-02 (catlak), DET-03 (asinma), DET-04 (saglik skoru), DET-05 (CameraResultsStore), DET-06 (thread'de model yukleme)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CameraResultsStore` (results_store.py) — Thread-safe key-value store, Phase 20'de yazildi. `update_batch()`, `get()`, `snapshot()` API'si. Detection ve wear sonuclari bu store'a yazilacak.
- `CameraService.get_current_frame()` — Worker'lar bu method ile raw frame alacak
- `SQLiteService.write_async()` — Mevcut queue-based async DB yazma pattern'i (detection_events ve wear_history icin)

### Established Patterns
- Daemon thread pattern — `threading.Thread(daemon=True)` ile arka plan threadleri
- Lazy import inside run() — torch, ultralytics, cv2 import'lari thread run() icinde (DET-06 requirement)
- `threading.Event()` ile stop signaling
- Logger per module — `logger = logging.getLogger(__name__)`
- Type hints + Google-style docstrings

### Integration Points
- `CameraService.get_current_frame()` → DetectionWorker ve LDCWorker frame kaynagi
- `CameraResultsStore.update_batch()` → Worker sonuclarini store'a yazma
- `CameraResultsStore.get("recording_path")` → Annotated frame kaydetme yolu
- `CameraResultsStore.get("tooth_count"/"broken_count")` → LDCWorker health hesaplamasi icin detection sonuclarina erisim
- `db_service.write_async()` → camera.db'ye detection_events ve wear_history yazma (Phase 22'de aktif olacak)

</code_context>

<specifics>
## Specific Ideas

- Mevcut kodlar algoritmik olarak hassas — ozellikle LDC inference pipeline (BGR mean subtraction, sigmoid normalization, contour-based wear calculation). Bu mantik korunmali, sadece convention audit yapilmali.
- RT-DETR class mapping: Broken model class 0=tooth (saglam), class 1=broken. Crack model class 0=crack.
- Health formula: `health = 100 - ((broken_pct/100 * 0.70 + wear/100 * 0.30) * 100)`
- Health status Turkce: Saglikli (>=80), Iyi (>=60), Orta (>=40), Kritik (>=20), Tehlikeli (<20)
- Wear ROI parametreleri config'e tasinacak — farkli kamera kurulumlarinda esneklik

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 21-ai-detection-pipeline*
*Context gathered: 2026-03-26*
