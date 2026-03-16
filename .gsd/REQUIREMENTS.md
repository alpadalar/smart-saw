# Requirements

## Active

## Validated

### CAM-01 — Sistem config dosyasinda camera.enabled flagi ile kamera modulunun acilip kapatilabilmesi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S22

Sistem config dosyasinda camera.enabled flagi ile kamera modulunun acilip kapatilabilmesi. S22 wired _init_camera() to create/start camera services only when camera.enabled=true in config. M001 milestone verification: config guard verified, _init_camera() creates services only when enabled=true, py_compile passes.

### CAM-02 — camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S22

camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread). S22 proved zero-import guard: camera __init__.py is inert, all imports lazy inside config guard in lifecycle. S24 extended guard to GUI layer: CameraController lazy-imported inside MainController config guard, not in controllers/__init__.py. M001 verification: `import src.services.camera` does not trigger cv2/torch.

### CAM-03 — OpenCV ile kameradan frame capture yapilabilmesi (cozunurluk ve FPS config'den ayarlanabilir)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S20

OpenCV ile kameradan frame capture yapilabilmesi (cozunurluk ve FPS config'den ayarlanabilir). S20 built CameraService with config-driven capture. S22 wired into lifecycle. M001 verification: CameraService instantiation with config dict verified, lifecycle wiring confirmed.

### CAM-04 — Capture edilen frame'lerin JPEG formatinda diske kaydedilmesi (multi-thread encoder)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S20

Capture edilen frame'lerin JPEG formatinda diske kaydedilmesi (multi-thread encoder). S20 built save worker pool with put_nowait drop-on-full. M001 verification: contract proven via instantiation and code inspection.

### CAM-05 — Kayit klasor yapisi (recordings/YYYYMMDD-HHMMSS/) ile organize edilmesi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S20

Kayit klasor yapisi (recordings/YYYYMMDD-HHMMSS/) ile organize edilmesi. S20 implements timestamped directory creation in start_recording(). M001 verification: code confirmed.

### DET-01 — RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S21

RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt). S21 built DetectionWorker with dual RT-DETR inference. M001 verification: import + instantiation verified, model_load_failed property available.

### DET-02 — RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S21

RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt). S21 built DetectionWorker with crack model path. M001 verification: import + instantiation verified.

### DET-03 — LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S21

LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi. S21 built LDCWorker with LDC model + contour-based wear calculation. M001 verification: import + instantiation verified.

### DET-04 — Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S21

Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30). S21 built HealthCalculator. M001 verification: math verified — 100.0 at perfect health, 35.0 at bad, 'Sağlıklı' at 85, 'Tehlikeli' at 15, '#FF0000' at critical.

### DET-05 — Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tukecilere sunulmasi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S20

Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tukecilere sunulmasi. S20 built CameraResultsStore with Lock-guarded dict and copy-on-snapshot. M001 verification: functionally tested — update/get/snapshot cycle passes, snapshot returns independent copy.

### DET-06 — AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S21

AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan). S21 built both workers as daemon threads with models loading inside run(). M001 verification: zero-import guard verified.

### DATA-01 — Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S22

Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db). S22 wired DetectionWorker and LDCWorker to write to detection_events and wear_history via SQLiteService.write_async(). M001 verification: INSERT SQL verified against SCHEMA_CAMERA_DB (9 columns each).

### DATA-02 — Tespit sonuclarinin ThingsBoard IoT platformuna gonderilmesi (mevcut telemetri batch'ine eklenerek)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S23

Tespit sonuclarinin ThingsBoard IoT platformuna gonderilmesi (mevcut telemetri batch'ine eklenerek). S23 wired CameraResultsStore.snapshot() through DataProcessingPipeline → MQTTService → ThingsBoardFormatter. M001 verification: format_telemetry accepts vision_data, 6 camera fields appear in output; telemetry_fields whitelist confirmed in config.

### DATA-03 — Kamera veritabani semasinin lifecycle'da config-driven olusturulmasi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S22

Kamera veritabani semasinin lifecycle'da config-driven olusturulmasi. S22 lifecycle _init_camera() creates camera.db via SQLiteService with SCHEMA_CAMERA_DB when camera.enabled=true. M001 verification: lifecycle source confirmed.

### GUI-01 — Kamera sayfasinda canli kamera goruntusu goruntulenmesi (QTimer ile periyodik guncelleme)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: CameraController has 500ms frame update timer reading latest_frame from CameraResultsStore, using QImage.loadFromData() for JPEG decoding.

### GUI-02 — Kirik dis tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: Broken tooth detection panel with lbl_broken_count and lbl_broken_time labels populated from store snapshot.

### GUI-03 — Catlak tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: Crack detection panel with lbl_crack_count and lbl_crack_time labels populated from store snapshot.

### GUI-04 — Asinma yuzdesinin kamera sayfasinda goruntulenmesi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: lbl_wear_percentage label populated from store snapshot wear_percentage field.

### GUI-05 — Testere saglik durumunun kamera sayfasinda goruntulenmesi (yuzde + durum metni + renk kodu)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: lbl_health_score with percentage, lbl_health_status with dynamic setStyleSheet from health_color hex value.

### GUI-06 — Sidebar'a 5. navigasyon butonu olarak kamera butonu eklenmesi (sadece camera.enabled=true iken)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: btnCamera created at y=649 only when camera_results_store is not None, wired to _switch_page(4). Not created when camera disabled.

### GUI-07 — Son kaydedilen frame'lerden 4 adet thumbnail goruntulenmesi (sequential images panel)

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: deque(maxlen=4) thumbnail history, 4 QLabel thumbnails updated from frame JPEG bytes.

### GUI-08 — Tespit durumu icin OK/alert ikonlari goruntulenmesi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: _set_ok_style (green ✓ OK) / _set_alert_style (red ✗ UYARI) applied based on detection counts.

### GUI-09 — Asinma olcum gorsellestirmesinin (wear visualization overlay) goruntulenmesi

- Status: validated
- Class: core-capability
- Source: inferred
- Primary Slice: S24

S24 contract proof: AsinmaYuzdesiFrame with wear percentage display label reading from CameraResultsStore.

## Deferred

## Out of Scope
