# Requirements

## Active

### CAM-01 — Sistem config dosyasinda camera.enabled flagi ile kamera modulunun acilip kapatilabilmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Sistem config dosyasinda camera.enabled flagi ile kamera modulunun acilip kapatilabilmesi

### CAM-02 — camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread)

### CAM-03 — OpenCV ile kameradan frame capture yapilabilmesi (cozunurluk ve FPS config'den ayarlanabilir)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

OpenCV ile kameradan frame capture yapilabilmesi (cozunurluk ve FPS config'den ayarlanabilir)

### CAM-04 — Capture edilen frame'lerin JPEG formatinda diske kaydedilmesi (multi-thread encoder)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Capture edilen frame'lerin JPEG formatinda diske kaydedilmesi (multi-thread encoder)

### CAM-05 — Kayit klasor yapisi (recordings/YYYYMMDD-HHMMSS/) ile organize edilmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Kayit klasor yapisi (recordings/YYYYMMDD-HHMMSS/) ile organize edilmesi

### DET-01 — RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt)

### DET-02 — RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt)

### DET-03 — LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi

### DET-04 — Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30)

### DET-05 — Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tukecilere sunulmasi

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tukecilere sunulmasi

### DET-06 — AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan)

### DATA-01 — Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db)

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db)

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
- Primary Slice: none yet

Kamera veritabani semasinin lifecycle'da config-driven olusturulmasi

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
