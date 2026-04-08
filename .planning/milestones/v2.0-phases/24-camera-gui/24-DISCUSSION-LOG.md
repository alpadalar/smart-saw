# Phase 24: Camera GUI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 24-camera-gui
**Areas discussed:** Aşınma overlay (GUI-09), Mevcut kod doğrulaması, Test stratejisi

---

## Aşınma Overlay (GUI-09)

| Option | Description | Selected |
|--------|-------------|----------|
| Annotated frame göster | LDCWorker annotated frame'i ayrı panelde göster | |
| Canlı feed üzerine çiz | QPainter ile ROI dikdörtgenleri overlay | |
| Progress bar ile göster | Aşınma yüzdesini görsel bar ile göster | |
| (Kullanıcı kombinasyonu) | Annotated kırık/çatlak frame canlı feed olarak + progress bar'lar, LDC overlay yok | ✓ |

**User's choice:** Hem annotated çatlak kırık görüntüsü hem de aşınma ve diğer progress bar'lar olsun ama LDC görüntüsü olmasın
**Notes:** Kullanıcı üç seçeneğin kombinasyonunu istedi: annotated frame canlı feed'in kendisi olacak + progress bar'lar eklenecek. LDC edge detection overlay istenmiyor.

## Annotated Frame Konumu

| Option | Description | Selected |
|--------|-------------|----------|
| Canlı feed'in kendisi olsun | latest_frame yerine annotated frame göster | ✓ |
| Ayrı panel olsun | Raw + annotated yan yana | |
| Geçişli göster | Varsayılan raw, tespit olunca annotated'a geç | |

**User's choice:** Canlı feed'in kendisi olsun
**Notes:** Tek görüntü alanı yeterli, operatör doğrudan tespit sonuçlarını görecek.

## Progress Bar Tasarımı

| Option | Description | Selected |
|--------|-------------|----------|
| Renk geçişli bar (Tavsiye) | Horizontal bar, yeşilden kırmızıya renk geçişi | ✓ |
| Dairesel gauge | QPainter çember gauge | |
| Sen karar ver | Claude seçsin | |

**User's choice:** Renk geçişli bar (Tavsiye)
**Notes:** Mevcut 300x120 frame'lerin içine horizontal bar + yüzde yazısı.

## Mevcut Kod Doğrulaması

| Option | Description | Selected |
|--------|-------------|----------|
| Tam audit (Tavsiye) | Key uyumluluğu + edge case + convention | ✓ |
| Sadece key uyumluluğu | Minimal kontrol | |
| Sen karar ver | Claude kapsam belirlesin | |

**User's choice:** Tam audit (Tavsiye)
**Notes:** CameraResultsStore key uyumluluğu, edge case handling, docstring, logging, type hints.

## Test Stratejisi

| Option | Description | Selected |
|--------|-------------|----------|
| Unit test (Tavsiye) | QTimer mock, snapshot sim, OK/alert geçişleri | |
| Minimal test | Sadece init + stop_timers | |
| Test yok | GUI görsel doğrulama ile | ✓ |

**User's choice:** Test yok
**Notes:** GUI kodu görsel doğrulama gerektirir, mevcut 45 test kamera backend'ini kapsıyor.

## Claude's Discretion

- Progress bar QFrame genişliği ve animasyon detayları
- Annotated frame fallback zamanlaması
- Convention audit kapsamı detayları

## Deferred Ideas

None — discussion stayed within phase scope
