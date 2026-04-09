# Phase 27: MainController Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 27-maincontroller-integration
**Areas discussed:** Sidebar sıralama & indeks shift, Buton ikonu ve etiketi, Koşullu vs sabit ekleme, closeEvent & timer cleanup

---

## Sidebar Sıralama & İndeks Shift

### Soru 1: Sidebar'da Otomatik Kesim butonu hangi sırada olsun?

| Option | Description | Selected |
|--------|-------------|----------|
| Index 1 (Roadmap planı) | Kontrol Paneli → Otomatik Kesim → Konumlandırma → Sensör → İzleme → Kamera | ✓ |
| Index 4 (sona ekle) | Mevcut sıralama korunur, Kamera'nın öncesine eklenir | |
| Son sıraya ekle | Kamera'nın altına eklenir | |

**User's choice:** Index 1 (Roadmap planı)
**Notes:** En sık kullanılan sayfalar üste yakın konumlandırılır.

### Soru 2: PageIndex sabitleri nasıl tanımlansın?

| Option | Description | Selected |
|--------|-------------|----------|
| IntEnum ayrı dosyada | src/gui/page_index.py dosyasında IntEnum | ✓ |
| MainController class sabitleri | MainController içinde class-level sabitler | |
| Sen karar ver | Claude en uygun yaklaşımı seçsin | |

**User's choice:** IntEnum ayrı dosyada
**Notes:** Tip güvenli, IDE autocomplete destekli, import edilerek tüm modüllerden erişilebilir.

---

## Buton İkonu ve Etiketi

### Soru 3: Otomatik Kesim butonu için hangi ikonu kullanalım?

| Option | Description | Selected |
|--------|-------------|----------|
| cutting-start-icon.svg | Mevcut 'kesim başlat' ikonu | ✓ |
| Yeni SVG oluştur | Otomatik/seri kesim konseptine özel yeni ikon | |
| Sen karar ver | Claude seçsin | |

**User's choice:** cutting-start-icon.svg
**Notes:** Mevcut ikon otomatik kesim konseptiyle örtüşüyor, yeni dosya gereksiz.

### Soru 4: Sidebar buton etiketi ne olsun?

| Option | Description | Selected |
|--------|-------------|----------|
| Otomatik Kesim | Roadmap ve requirements'taki resmi isim | ✓ |
| Seri Kesim | Daha kısa, operasyon amacını vurgular | |
| Oto. Kesim | Kısaltılmış versiyon | |

**User's choice:** Otomatik Kesim
**Notes:** Resmi isimlendirme ile tutarlılık sağlar.

---

## Koşullu vs Sabit Ekleme

### Soru 5: Otomatik Kesim sayfası her zaman mı görünecek yoksa bir koşula mı bağlı?

| Option | Description | Selected |
|--------|-------------|----------|
| Her zaman görünsün | Sayfa her zaman sidebar'da mevcut | ✓ |
| Config flag ile koşullu | auto_cutting.enabled config flag'i | |
| PLC bağlantısına bağlı | Sadece PLC aktifken görünür | |

**User's choice:** Her zaman görünsün
**Notes:** MachineControl zaten bağlantı yokken sessizce başarısız olur — koşul gereksiz.

---

## closeEvent & Timer Cleanup

### Soru 6: closeEvent'te Otomatik Kesim sayfası timer cleanup nasıl yapılsın?

| Option | Description | Selected |
|--------|-------------|----------|
| Sabit listeye ekle | Mevcut sabit listeye otomatik_kesim_page eklenir | ✓ |
| Dinamik iterasyon | stackedWidget'ın tüm sayfalarını iterate et | |
| Sen karar ver | Claude seçsin | |

**User's choice:** Sabit listeye ekle
**Notes:** Basit, açık, mevcut pattern ile tutarlı.

---

## Claude's Discretion

- OtomatikKesimController constructor parametreleri
- Import sıralaması ve dosya organizasyonu
- Qt property detayları (setCheckable vb.)

## Deferred Ideas

(None)
