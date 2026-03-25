# Requirements: Smart Saw v2.0

**Defined:** 2026-03-16
**Core Value:** Endustriyel testere operasyonlarinin guvenilir kontrolu ve serit testere sagliginin yapay zeka ile surekli izlenmesi

## v2.0 Requirements

Requirements for Camera Vision & AI Detection milestone. Each maps to roadmap phases.

### Camera Infrastructure

- [x] **CAM-01**: Sistem config dosyasinda camera.enabled flagi ile kamera modulunun acilip kapatilabilmesi
- [x] **CAM-02**: camera.enabled=false oldugunda hicbir kamera kodu yuklenmemesi (sifir import, sifir thread)
- [x] **CAM-03**: OpenCV ile kameradan frame capture yapilabilmesi (cozunurluk ve FPS config'den ayarlanabilir)
- [x] **CAM-04**: Capture edilen frame'lerin JPEG formatinda diske kaydedilmesi (multi-thread encoder)
- [x] **CAM-05**: Kayit klasor yapisi (recordings/YYYYMMDD-HHMMSS/) ile organize edilmesi

### AI Detection

- [x] **DET-01**: RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt)
- [x] **DET-02**: RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt)
- [ ] **DET-03**: LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi
- [ ] **DET-04**: Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30)
- [x] **DET-05**: Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tukecilere sunulmasi
- [x] **DET-06**: AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan)

### Data Integration

- [ ] **DATA-01**: Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db)
- [ ] **DATA-02**: Tespit sonuclarinin ThingsBoard IoT platformuna gonderilmesi (mevcut telemetri batch'ine eklenerek)
- [x] **DATA-03**: Kamera veritabani semasinin lifecycle'da config-driven olusturulmasi

### GUI

- [ ] **GUI-01**: Kamera sayfasinda canli kamera goruntusu goruntulenmesi (QTimer ile periyodik guncelleme)
- [ ] **GUI-02**: Kirik dis tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)
- [ ] **GUI-03**: Catlak tespit sonuclarinin kamera sayfasinda goruntulenmesi (sayi, zaman damgasi)
- [ ] **GUI-04**: Asinma yuzdesinin kamera sayfasinda goruntulenmesi
- [ ] **GUI-05**: Testere saglik durumunun kamera sayfasinda goruntulenmesi (yuzde + durum metni + renk kodu)
- [ ] **GUI-06**: Sidebar'a 5. navigasyon butonu olarak kamera butonu eklenmesi (sadece camera.enabled=true iken)
- [ ] **GUI-07**: Son kaydedilen frame'lerden 4 adet thumbnail goruntulenmesi (sequential images panel)
- [ ] **GUI-08**: Tespit durumu icin OK/alert ikonlari goruntulenmesi
- [ ] **GUI-09**: Asinma olcum gorsellestirmesinin (wear visualization overlay) goruntulenmesi

## v2.x Requirements

Deferred to future release. Tracked but not in current roadmap.

### Recording Management

- **REC-01**: Eski kayitlarin otomatik silinmesi (disk alani yonetimi)
- **REC-02**: Kayit bazli gecmis paneli (per-recording history UI)

### Detection Tuning

- **TUNE-01**: Confidence threshold'un GUI uzerinden ayarlanabilmesi
- **TUNE-02**: Detection interval'in GUI uzerinden ayarlanabilmesi

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time AI inference during recording | CPU, RT-DETR'yi frame rate'inde calistiramaz; record-then-detect pattern dogru yaklasim |
| Surekli video kaydi (MP4/AVI) | Disk alani: ~54GB/30dk; JPEG sekans yeterli |
| Multi-camera destegi | Tek kamera yeterli; genisleme noktasi dokumante edilir ama implement edilmez |
| opencv-python (full) kullanimi | Qt5/Qt6 symbol catismasi — opencv-python-headless kullanilmali |
| Model egitimi / fine-tuning | Mevcut modeller (best.pt, catlak-best.pt) kullanilacak |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CAM-01 | Phase 19 | Complete |
| CAM-02 | Phase 19 | Complete |
| CAM-03 | Phase 20 | Complete |
| CAM-04 | Phase 20 | Complete |
| CAM-05 | Phase 20 | Complete |
| DET-01 | Phase 21 | Complete |
| DET-02 | Phase 21 | Complete |
| DET-03 | Phase 21 | Pending |
| DET-04 | Phase 21 | Pending |
| DET-05 | Phase 21 | Complete |
| DET-06 | Phase 21 | Complete |
| DATA-01 | Phase 22 | Pending |
| DATA-02 | Phase 23 | Pending |
| DATA-03 | Phase 19 | Complete |
| GUI-01 | Phase 24 | Pending |
| GUI-02 | Phase 24 | Pending |
| GUI-03 | Phase 24 | Pending |
| GUI-04 | Phase 24 | Pending |
| GUI-05 | Phase 24 | Pending |
| GUI-06 | Phase 24 | Pending |
| GUI-07 | Phase 24 | Pending |
| GUI-08 | Phase 24 | Pending |
| GUI-09 | Phase 24 | Pending |

**Coverage:**
- v2.0 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-16*
*Last updated: 2026-03-16 — traceability mapped to Phases 19-24*
