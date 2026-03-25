# Phase 22: Lifecycle & DB Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 22-lifecycle-db-integration
**Areas discussed:** VisionService orchestration, DB yazma dogrulama, Hata izolasyonu, Shutdown sirasi

---

## VisionService Orchestration

### Q1: VisionService testere durumunu nereden okusun?

| Option | Description | Selected |
|--------|-------------|----------|
| CameraResultsStore | DataProcessingPipeline her dongude testere_durumu'nu CameraResultsStore'a yazsin, VisionService oradan okusun. Tum kamera servisleri tek store uzerinden haberlesirir. | ✓ |
| Callback/signal | DataProcessingPipeline testere_durumu degistiginde VisionService'e callback/event gondersin. Daha az polling ama yeni bir coupling pattern. | |

**User's choice:** CameraResultsStore (Recommended)
**Notes:** Tum kamera servisleri tek store uzerinden haberlesir — tutarli pattern.

### Q2: Recording hangi testere_durumu gecisinde tetiklensin?

| Option | Description | Selected |
|--------|-------------|----------|
| Kesim sonu gecisi | testere_durumu 3'den farkli bir degere gectiginde recording baslasin. Phase 20 D-03 ile uyumlu. | ✓ |
| Surekli recording | camera.enabled=true iken surekli kaydet. Basit ama disk kullanimi yuksek. | |
| Manuel API | VisionService sadece API sunsun, tetikleme disa birakilsin. | |

**User's choice:** Kesim sonu gecisi (Recommended)
**Notes:** Phase 20 D-03 ile uyumlu — testere yuzeyi gorunur oldugunda.

### Q3: VisionService kendi daemon thread'inde mi calissin, yoksa asyncio task olarak mi?

| Option | Description | Selected |
|--------|-------------|----------|
| Daemon thread | Diger kamera servisleri gibi daemon thread. Tutarli pattern, asyncio event loop'u bloklamaz. | ✓ |
| asyncio Task | Main event loop icinde asyncio.Task olarak calisir. Farkli pattern olur. | |

**User's choice:** Daemon thread (Recommended)
**Notes:** DetectionWorker, LDCWorker ile ayni pattern.

---

## DB Yazma Dogrulama

### Q4: Traceability alanlari nasil doldurulsun?

| Option | Description | Selected |
|--------|-------------|----------|
| VisionService inject etsin | VisionService CameraResultsStore uzerinden guncel traceability degerlerini store'a yazsin, worker'lar oradan okuyup DB'ye kaydetsin. | ✓ |
| NULL kalsin | Simdilik NULL birak, ileride doldurulsun. | |
| Worker constructor'a parametre | Worker'lara dogrudan parametre olarak gec (runtime'da degistigi icin uygun degil). | |

**User's choice:** VisionService inject etsin (Recommended)
**Notes:** DataProcessingPipeline zaten bu degerleri uretiyor.

### Q5: image_path ve edge_pixel_count alanlari da Phase 22'de doldurulsun mu?

| Option | Description | Selected |
|--------|-------------|----------|
| Evet, hepsini doldur | Worker'lar zaten annotated frame kaydediyor ve edge pixel hesapliyor — bu degerleri DB'ye de yazsinlar. | ✓ |
| Sadece edge_pixel_count | image_path recording'e bagli, her zaman mevcut degil. | |
| NULL kalsin | Simdilik ek is yapma. | |

**User's choice:** Evet, hepsini doldur (Recommended)
**Notes:** Tam veri butunlugu saglanir.

---

## Hata Izolasyonu

### Q6: VisionService polling/recording hatasinda ne olsun?

| Option | Description | Selected |
|--------|-------------|----------|
| Logla ve devam et | Hata loglanir, sonraki cycle'da tekrar dener. Thread olmez, ana dongu etkilenmez. | ✓ |
| N hata sonrasi devre disi | Ardisik N hatadan sonra VisionService kendini durdursun. | |
| Claude karar versin | Mevcut worker pattern'lerine bakarak Claude belirlesin. | |

**User's choice:** Logla ve devam et (Recommended)
**Notes:** Mevcut worker pattern'i ile tutarli.

---

## Shutdown Sirasi

### Q7: VisionService shutdown sirasinda nerede durdurulsun?

| Option | Description | Selected |
|--------|-------------|----------|
| Once VisionService, sonra worker'lar | VisionService once durdurulur, sonra worker'lar, sonra CameraService. Ustten asagiya. | ✓ |
| Worker'larla ayni anda | Paralel durdurma. Daha hizli ama siralama garantisi yok. | |
| Claude karar versin | Mevcut pattern'e en uygun sirayi Claude belirlesin. | |

**User's choice:** Once VisionService, sonra worker'lar (Recommended)
**Notes:** Orchestrator ustten asagiya kapanir.

### Q8: Worker'lar durdurulurken DB flush yapilsin mi?

| Option | Description | Selected |
|--------|-------------|----------|
| Evet, flush sonra dur | Mevcut cycle tamamlanir ve son DB write'lar yapilir. | ✓ |
| Hayir, hemen dur | stop_event set edilir, kuyrukta bekleyen veri kaybolabilir. | |

**User's choice:** Evet, flush sonra dur (Recommended)
**Notes:** SQLiteService kendi shutdown'unda da flush yapiyor — cift katmanli koruma.

---

## Claude's Discretion

- VisionService polling intervali
- CameraResultsStore'a testere_durumu yazma yeri
- Recording durdurma zamanlama mantigi

## Deferred Ideas

None — discussion stayed within phase scope
