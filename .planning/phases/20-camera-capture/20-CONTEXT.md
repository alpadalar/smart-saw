# Phase 20: Camera Capture - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Kameradan frame alimi ve JPEG kaydi — asyncio event loop'u hic bloklamadan arka plan thread'lerinde calisir. CameraResultsStore ve CameraService sifirdan yazilacak (mevcut eski proje kodu referans olarak kullanilacak).

</domain>

<decisions>
## Implementation Decisions

### Mevcut Kod Stratejisi
- **D-01:** Eski projeden gelen `camera_service.py` ve `results_store.py` kodlari referans olarak kullanilacak ama sifirdan yazilacak. Yeni mimarinin convention'larina (docstring formati, error handling pattern'leri, logging style, naming conventions) tam uyumlu olacak.
- **D-02:** Diger camera modulu dosyalari (`detection_worker.py`, `ldc_worker.py`, `health_calculator.py`, `modelB4.py`) Phase 21'e ait — Phase 20'de dokunulmayacak.

### Kayit Baslatma Davranisi
- **D-03:** Kayit sadece testere durumu "yukari cikiyor" oldugunda aktif olacak. Kesim bittikten sonra testere geri cekilirken frame'ler kaydedilir (testere yüzeyi gorunur hale geldiginde).
- **D-04:** Phase 20'de CameraService sadece `start_recording()` / `stop_recording()` API'sini sunacak. Tetikleme mantigi Phase 22'de (VisionService orchestration) `testere_durumu` degerine gore yapilacak.

### Kamera Erisilelemezligi
- **D-05:** Baslangiçta config'deki `device_id` yerine sistemdeki tum kamera device'lerini tarayip ilk bulunani kullanacak (auto-discovery). Config'deki `device_id` sadece hint olarak kalir.
- **D-06:** Capture sirasinda kamera baglantisi koparsa: 30 saniye boyunca retry, basarisiz olursa capture thread'i durdur ve log yaz. Ana uygulama dongusu etkilenmez.

### Claude's Discretion
- fps_actual takibinin capture loop'ta nasil implement edilecegi (moving average, window size vb.)
- Frame queue boyutu ve overflow stratejisi
- Save worker thread sayisi (mevcut kodda min(4, cpu_count) — uygun gorulen deger kullanilabilir)
- Auto-discovery sirasinda taranan device ID araligi

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Mevcut Referans Kod (eski projeden — sifirdan yazilacak ama referans)
- `src/services/camera/camera_service.py` — Mevcut capture thread + save worker implementasyonu (referans olarak okunmali)
- `src/services/camera/results_store.py` — Mevcut thread-safe store implementasyonu (referans olarak okunmali)

### Proje Convention'lari
- `.planning/codebase/CONVENTIONS.md` — Naming, docstring, error handling pattern'leri
- `.planning/codebase/ARCHITECTURE.md` — Concurrency model (asyncio + threading hybrid), service patterns

### Config ve Schema
- `config/config.yaml` §camera — Camera config section (device_id, resolution, fps, jpeg_quality, recordings_path)
- `src/services/database/schemas.py` — SCHEMA_CAMERA_DB (detection_events + wear_history tablolari)

### Phase 19 Foundation
- `.planning/phases/19-foundation/19-CONTEXT.md` — Foundation kararlari (numpy uncap, config schema, camera.db schema, zero-import guard)

### Requirements
- `.planning/REQUIREMENTS.md` §Camera Infrastructure — CAM-03 (frame capture), CAM-04 (JPEG recording), CAM-05 (directory structure)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CameraResultsStore` pattern (results_store.py) — Thread-safe key-value store with update/snapshot. Sifirdan yazilacak ama ayni API kontrati korunacak (update, update_batch, get, snapshot).
- `CameraService` capture pattern (camera_service.py) — Platform-aware VideoCapture, daemon capture thread, multi-thread save worker pool. Referans mimari.
- `SQLiteService` queue pattern — Database yazma icin mevcut queue-based async pattern (services/database/)
- Config access pattern — `config.get()` ile config degerlerine erisim (tum servisler bu pattern'i kullaniyor)

### Established Patterns
- Daemon thread pattern — `threading.Thread(daemon=True)` ile arka plan threadleri (mevcut: health monitor, SQLite writer)
- async start()/stop() lifecycle — Tum servisler bu pattern'i kullaniyor
- Logger per module — `logger = logging.getLogger(__name__)`
- Type hints + Google-style docstrings

### Integration Points
- `CameraResultsStore` — Phase 21 (detection), Phase 22 (lifecycle), Phase 23 (IoT), Phase 24 (GUI) tarafindan tuketilecek
- `CameraService.get_current_frame()` — Phase 21 DetectionWorker bu method ile raw frame alacak
- `start_recording()` / `stop_recording()` — Phase 22 VisionService testere_durumu'na gore tetikleyecek

</code_context>

<specifics>
## Specific Ideas

- Kayit sadece "yukari cikiyor" durumunda — testere yüzeyi gorunur oldugunda. Bu, tespit icin en anlamli framelerin yakalanmasini saglar.
- Auto-discovery: sistemdeki tum kamera devicelerini tara, ilk bulunani kullan. Endustriyel ortamda USB kamera device ID'leri degisebilir.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 20-camera-capture*
*Context gathered: 2026-03-25*
