# Phase 24: Camera GUI - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

PySide6 kamera sayfasinin tamamlanmasi — canli annotated frame goruntusu, kirik/catlak/asinma tespit sonuclari, progress bar ile gorsel asinma/saglik gostergesi, thumbnail paneli, OK/alert ikonlari ve sidebar navigasyon butonu. Tum veriler CameraResultsStore.snapshot() uzerinden okunur.

</domain>

<decisions>
## Implementation Decisions

### Annotated Frame Gosterimi
- **D-01:** Canli feed alani (`camera_label`) raw frame yerine annotated frame gosterecek. DetectionWorker'in urettigi kirik dis (kirmizi) ve catlak (mavi) bounding box'li frame dogrudan canli goruntuye yansiyacak. Operator tespit sonuclarini anlik gorecek.
- **D-02:** CameraResultsStore'a `annotated_frame` key ile annotated JPEG bytes yazilacak. CameraController `latest_frame` yerine `annotated_frame` varsa onu, yoksa `latest_frame`'i gosterecek (fallback).
- **D-03:** LDC edge detection overlay'i (wear ROI cizgileri) gosterilmeyecek — sadece kirik/catlak bounding box'lari gorunecek.

### Progress Bar Tasarimi
- **D-04:** Asinma yuzdesi icin renk gecisli horizontal progress bar: yesil (dusuk asinma = iyi) → sari → kirmizi (yuksek asinma = kotu). Mevcut 300x120 frame icine QFrame-based bar + yuzde yazisi.
- **D-05:** Testere sagligi icin renk gecisli horizontal progress bar: kirmizi (dusuk skor = kotu) → sari → yesil (yuksek skor = iyi). Ters renk yonu — yuksek saglik skoru iyidir.
- **D-06:** Mevcut sayi gosterimi (lbl_wear_value, lbl_health_score) korunacak, progress bar ek gorsel olarak eklenecek.

### Kod Dogrulama
- **D-07:** Mevcut CameraController kodu tam convention audit'ten gecirilecek: CameraResultsStore key uyumlulugu, edge case handling (kamera yok, veri yok, store bos), docstring formati, logging pattern, type hints.
- **D-08:** MainController'daki kamera entegrasyonu (conditional import, sidebar buton, stacked widget) da audit kapsaminda.

### Test Stratejisi
- **D-09:** CameraController icin unit test yazilmayacak. GUI kodu gorsel dogrulama ile test edilecek. Diger phase'lerdeki 45 mock-based test kamera backend'ini kapsiyor.

### Claude's Discretion
- Progress bar QFrame genisligi ve animasyon detaylari
- Annotated frame fallback mantigi (annotated yokken latest_frame gosterme zamanlama detaylari)
- Convention audit sirasinda yapilacak spesifik duzeltmelerin kapsami

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Mevcut CameraController (audit edilecek)
- `src/gui/controllers/camera_controller.py` — Mevcut CameraController implementasyonu (480 satir, auto-commit)
- `src/gui/controllers/main_controller.py` — MainController: conditional camera button (satir 212-220), camera page (satir 297-303), closeEvent timer stop (satir 416-417)

### Camera Pipeline (veri kaynagi)
- `src/services/camera/results_store.py` — CameraResultsStore: snapshot() API, key-value store
- `src/services/camera/detection_worker.py` — DetectionWorker: annotated frame uretimi, _save_annotated_frame()
- `src/services/camera/health_calculator.py` — HealthCalculator: CSS renk kodlari, Turkce durum metinleri

### GUI Patterns (tutarlilik)
- `src/gui/controllers/control_panel_controller.py` — Control panel pattern (QTimer, thread-safe update, style constants)
- `src/gui/controllers/sensor_controller.py` — Sensor page pattern (CuttingGraphWidget, QPainter custom widget)
- `src/gui/numpad.py` — NumpadDialog (close button, pre-fill — Phase 19.1)

### Proje Convention'lari
- `.planning/codebase/CONVENTIONS.md` — Naming, docstring, error handling pattern'leri
- `.planning/codebase/ARCHITECTURE.md` — Concurrency model, service patterns

### Onceki Phase Context'leri
- `.planning/phases/20-camera-capture/20-CONTEXT.md` — CameraService API, recording pattern
- `.planning/phases/21-ai-detection-pipeline/21-CONTEXT.md` — DetectionWorker annotated frame, health formula, Turkce status
- `.planning/phases/22-lifecycle-db-integration/22-CONTEXT.md` — VisionService, CameraResultsStore integration

### Requirements
- `.planning/REQUIREMENTS.md` §GUI — GUI-01 ~ GUI-09

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CameraController` (camera_controller.py) — Mevcut 480 satirlik implementasyon: canli feed, kirik/catlak panelleri, thumbnail deque, asinma/saglik frameleri, OK/alert ikonlari, 3 QTimer (500/1000/2000 ms). Audit + genisletme yapilacak.
- `_FRAME_STYLE`, `_TITLE_STYLE`, `_VALUE_STYLE`, `_SUBTITLE_STYLE`, `_INFO_STYLE` — Shared style constants (camera_controller.py). Diger sayfalarla tutarli gorsel dil.
- `HealthCalculator.get_css_color()` — Saglik durumuna gore CSS hex renk kodu (health_calculator.py). Progress bar renklendirmesi icin kullanilabilir.
- MainController conditional camera integration — `camera_results_store is not None` guard pattern (main_controller.py:212, 297).

### Established Patterns
- QTimer polling pattern — Periyodik snapshot okuma (mevcut: 500/1000/2000 ms)
- `_set_ok_style()` / `_set_alert_style()` — Static method ile durum stili degistirme
- QFrame + QLabel layout — Programmatic layout, .ui dosyasi yok
- `Plus Jakarta Sans` font family — Tum GUI'de tutarli
- Gradient background — `rgba(6, 11, 38, 240)` → `rgba(26, 31, 55, 0)` frame stili

### Integration Points
- `CameraResultsStore.snapshot()` → Tum GUI verisi buradan okunuyor (latest_frame, broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status, health_color, is_recording, frame_count, last_detection_ts)
- `annotated_frame` key → Yeni: DetectionWorker annotated JPEG bytes'i store'a yazacak, CameraController okuyacak
- Sidebar nav_buttons[] → Camera butonu index 4 olarak ekleniyor (main_controller.py:220)
- QStackedWidget → Camera page index 4 (main_controller.py:303)

</code_context>

<specifics>
## Specific Ideas

- Annotated frame: Kirik dislere kirmizi, saglam dislere yesil, catlaklara mavi bounding box cizilmis frame dogrudan canli feed'de gosterilecek. Raw frame ile annotated frame arasinda otomatik fallback.
- Progress bar renk yonu: Asinma dusuk=yesil (iyi), yuksek=kirmizi (kotu). Saglik dusuk=kirmizi (kotu), yuksek=yesil (iyi). Ters mantik.
- Mevcut CameraController style constant'lari (_FRAME_STYLE vs.) diger sayfalardaki pattern'lerle tutarli — korunacak.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 24-camera-gui*
*Context gathered: 2026-03-26*
