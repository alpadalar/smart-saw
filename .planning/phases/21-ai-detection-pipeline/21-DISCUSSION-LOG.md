# Phase 21: AI Detection Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 21-ai-detection-pipeline
**Areas discussed:** Mevcut kod stratejisi, DB yazma kapsami, Annotated frame kaydetme, Wear ROI parametreleri

---

## Mevcut Kod Stratejisi

| Option | Description | Selected |
|--------|-------------|----------|
| Audit ve refactor (Tavsiye) | Mevcut kodu incele, convention'lara uygunlugunu denetle, gereken duzeltmeleri yap. Algoritmik mantik korunur. | ✓ |
| Sifirdan yaz (Phase 20 gibi) | Eski kodu referans olarak kullan, her seyi yeniden yaz. LDC wear hesaplamasi gibi hassas algoritmalar icin hata riski. | |
| Oldugu gibi kullan | Mevcut koda hic dokunma, sadece test yaz ve entegre et. Convention uyumsuzlugu kalabilir. | |

**User's choice:** Audit ve refactor (Tavsiye)
**Notes:** Mevcut kodlar algoritmik olarak hassas, sifirdan yazma riski yuksek. Convention audit yeterli.

---

## DB Yazma Kapsami

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 21'de tut (Tavsiye) | Worker'larin db_service parametresi ve write_async cagrilari mevcut kodda korunur. Phase 22'de sadece lifecycle baglantisi yapilir. | ✓ |
| Phase 22'ye birak | Phase 21'de db_service=None ile calisir, DB yazma kodu tamamen Phase 22'de eklenir. | |
| Hazir ama pasif | DB yazma kodu Phase 21'de kalir ama db_service=None varsayilani ile hicbir sey yazmaz. | |

**User's choice:** Phase 21'de tut (Tavsiye)
**Notes:** Mevcut kodda DB yazma zaten var, cikarma gereksiz. Phase 22'de lifecycle inject edecek.

---

## Annotated Frame Kaydetme

| Option | Description | Selected |
|--------|-------------|----------|
| Evet, kaps. dahil (Tavsiye) | Mevcut kodda zaten var, audit sirasinda korunur. Gorsel kanit olarak degerli. | ✓ |
| Hayir, cikar | Phase 21'den cikarilir, ileride ayri ozellik olarak eklenebilir. | |

**User's choice:** Evet, kapsam dahil (Tavsiye)
**Notes:** Sadece aktif kayit varsa yazar, yoksa skip eder. Operatorler icin gorsel kanit.

---

## Wear ROI Parametreleri

| Option | Description | Selected |
|--------|-------------|----------|
| Config'e tasi (Tavsiye) | TOP_LINE_Y, BOTTOM_LINE_Y ve ROI normalize koordinatlari config.yaml'a tasinir. Farkli kamera kurulumlarinda degistirilebilir. | ✓ |
| Sabit birak | Mevcut hardcoded degerler korunur. Tek kamera kurulumu icin yeterli. | |
| Sen karar ver | Claude degerlendirir. | |

**User's choice:** Config'e tasi (Tavsiye)
**Notes:** Farkli kamera kurulumlarinda esneklik saglanacak. Varsayilan degerler mevcut sabitlerle ayni.

---

## Claude's Discretion

- Convention audit spesifik kapsami
- Test stratejisi ve mock yapisi
- imgsz parametresinin config'e tasinip tasinmamasi

## Deferred Ideas

None — discussion stayed within phase scope
