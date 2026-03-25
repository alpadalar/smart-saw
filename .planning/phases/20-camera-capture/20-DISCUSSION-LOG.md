# Phase 20: Camera Capture - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 20-camera-capture
**Areas discussed:** Mevcut kod stratejisi, Kayit baslatma davranisi, Kamera erisilemezligi

---

## Mevcut Kod Stratejisi

| Option | Description | Selected |
|--------|-------------|----------|
| Mevcut kodu kullan (Recommended) | Eski projeden gelen kodu oldugu gibi kabul et, eksikleri tamamla, yeni mimariye uyumu dogrula. Minimum is, sinanmis kod. | |
| Refactor et | Mevcut kodu temel al ama yeni mimarinin convention'larina uyarla (docstring formati, error handling pattern'leri, logging style). Orta seviye is. | |
| Sifirdan yaz | Mevcut kodu referans olarak kullan ama tumunu yeni mimariye uygun sifirdan implement et. En cok is, en tutarli sonuc. | ✓ |

**User's choice:** Sifirdan yaz
**Notes:** Kullanici tutarlilik icin sifirdan yazmayi tercih etti. Mevcut kod referans olarak kullanilacak.

---

## Kayit Baslatma Davranisi

| Option | Description | Selected |
|--------|-------------|----------|
| Otomatik (kamera acilinca) (Recommended) | CameraService.start() cagrildiginda hem capture hem recording otomatik baslar. Basit, her zaman veri toplar. | |
| Kesim tetiklemeli | Sadece testere kesim modundayken (testere_durumu == 3) recording baslar. Disk tasarrufu, cross-service tetikleme gerekir. | |
| Manuel API | start_recording/stop_recording disaridan cagrilir. VisionService orchestration'i belirleyecek. | |

**User's choice:** Other — Testere durumu "yukari cikiyor" oldugunda kaydetsin
**Notes:** Kesim bittikten sonra testere yukari cikarken kayit yapilacak. Bu durumda testere yüzeyi gorunur oldugu icin tespit icin en anlamli frameler yakalanir. Phase 20'de sadece API hazir olacak, tetikleme Phase 22'de VisionService tarafindan yapilacak.

---

## Kamera Erisilemezligi — Baslangiç

| Option | Description | Selected |
|--------|-------------|----------|
| Sessiz basarisizlik (Recommended) | Log yaz, False don, uygulama kamera olmadan devam etsin. | |
| Periyodik yeniden deneme | Arka planda her 30 saniyede bir kamerayi tekrar acmayi dene. | |
| Operatore uyari | GUI'da uyari goster + log yaz. | |

**User's choice:** Other — Sistemdeki tum kamera devicelerini tarayip ilk bulugunu kullansın
**Notes:** Config'deki device_id yerine auto-discovery. Endustriyel ortamda USB kamera device ID'leri degisebilir, bu yaklasim daha robust.

## Kamera Erisilemezligi — Kopma

| Option | Description | Selected |
|--------|-------------|----------|
| Retry + timeout (Recommended) | Belirli sure (30sn) boyunca tekrar dene, basarisiz olursa capture thread'i durdur ve log yaz. | ✓ |
| Suresiz retry | Sonsuz dongude 10ms bekle + tekrar dene. | |
| Hemen durdur | cap.read() basarisiz olunca capture durdur, stop() cagir. | |

**User's choice:** Retry + timeout (Recommended)
**Notes:** 30 saniye retry window, sonra capture thread durdurulur. Ana uygulama dongusu etkilenmez.

---

## Claude's Discretion

- fps_actual takibi implementasyonu
- Frame queue boyutu ve overflow stratejisi
- Save worker thread sayisi
- Auto-discovery device ID tarama araligi

## Deferred Ideas

None — tartisma faz kapsaminda kaldi.
