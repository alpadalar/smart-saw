# Requirements

## Active

### CAM-01 — Sistem config dosyasinda camera.enabled flagi ile kamera modulunun acilip kapatilabilmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S22

Sistem config dosyasinda camera.enabled flagi ile kamera modulunun acilip kapatilabilmesi. S22 wired _init_camera() to create/start camera services only when camera.enabled=true in config.

### CAM-02 — camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S22

camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread). S22 proved zero-import guard: camera __init__.py is inert, all imports lazy inside config guard in lifecycle.

camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread)

### CAM-03 — OpenCV ile kameradan frame capture yapilabilmesi (cozunurluk ve FPS config'den ayarlanabilir)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S20

OpenCV ile kameradan frame capture yapilabilmesi (cozunurluk ve FPS config'den ayarlanabilir). S20 built CameraService with config-driven capture — needs S22 lifecycle wiring for end-to-end validation.

### CAM-04 — Capture edilen frame'lerin JPEG formatinda diske kaydedilmesi (multi-thread encoder)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S20

Capture edilen frame'lerin JPEG formatinda diske kaydedilmesi (multi-thread encoder). S20 built save worker pool with put_nowait drop-on-full — needs real camera for end-to-end validation.

### CAM-05 — Kayit klasor yapisi (recordings/YYYYMMDD-HHMMSS/) ile organize edilmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S20

Kayit klasor yapisi (recordings/YYYYMMDD-HHMMSS/) ile organize edilmesi. S20 implements timestamped directory creation in start_recording().

### DET-01 — RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S21

RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt). S21 built DetectionWorker with dual RT-DETR inference — contract proven (import, instantiation), needs real model files and S22 lifecycle wiring for runtime validation.

### DET-02 — RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S21

RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt). S21 built DetectionWorker with crack model path — contract proven, needs real model files and S22 lifecycle wiring.

### DET-03 — LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S21

LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi. S21 built LDCWorker with LDC model + contour-based wear calculation — contract proven, needs real checkpoint and S22 lifecycle wiring.

### DET-04 — Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S21

Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30). S21 built HealthCalculator with verified math — calculate_saw_health, get_health_status, get_health_color all pass boundary tests.

### DET-05 — Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tukecilere sunulmasi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S20

Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tukecilere sunulmasi. S20 built CameraResultsStore with Lock-guarded dict and copy-on-snapshot. S21 workers publish detection results via update_batch().

### DET-06 — AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S21

AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan). S21 built both workers as daemon threads with models loading inside run() — zero-import guard verified.

### DATA-01 — Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S22

Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db). S22 wired DetectionWorker and LDCWorker to write to detection_events and wear_history via SQLiteService.write_async(). INSERT SQL verified against schema. Needs runtime validation with real camera.

### DATA-02 — Tespit sonuclarinin ThingsBoard IoT platformuna gonderilmesi (mevcut telemetri batch'ine eklenerek)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Tespit sonuclarinin ThingsBoard IoT platformuna gonderilmesi (mevcut telemetri batch'ine eklenerek)

### DATA-03 — Kamera veritabani semasinin lifecycle'da config-driven olusturulmasi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: S22

Kamera veritabani semasinin lifecycle'da config-driven olusturulmasi. S22 lifecycle _init_camera() creates camera.db via SQLiteService with SCHEMA_CAMERA_DB when camera.enabled=true.

### GUI-01 — Kamera sayfasinda canli kamera goruntusu goruntulenmesi (QTimer ile periyodik guncelleme)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Kamera sayfasinda canli kamera goruntusu goruntulenmesi (QTimer ile periyodik guncelleme)

### GUI-02 — Kirik dis tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Kirik dis tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)

### GUI-03 — Catlak tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Catlak tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)

### GUI-04 — Asinma yuzdesinin kamera sayfasinda goruntulenmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Asinma yuzdesinin kamera sayfasinda goruntulenmesi

### GUI-05 — Testere saglik durumunun kamera sayfasinda goruntulenmesi (yuzde + durum metni + renk kodu)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Testere saglik durumunun kamera sayfasinda goruntulenmesi (yuzde + durum metni + renk kodu)

### GUI-06 — Sidebar'a 5. navigasyon butonu olarak kamera butonu eklenmesi (sadece camera.enabled=true iken)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Sidebar'a 5. navigasyon butonu olarak kamera butonu eklenmesi (sadece camera.enabled=true iken)

### GUI-07 — Son kaydedilen frame'lerden 4 adet thumbnail goruntulenmesi (sequential images panel)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Son kaydedilen frame'lerden 4 adet thumbnail goruntulenmesi (sequential images panel)

### GUI-08 — Tespit durumu icin OK/alert ikonlari goruntulenmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Tespit durumu icin OK/alert ikonlari goruntulenmesi

### GUI-09 — Asinma olcum gorsellestirmesinin (wear visualization overlay) goruntulenmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Asinma olcum gorsellestirmesinin (wear visualization overlay) goruntulenmesi

## Validated

## Deferred

## Out of Scope
