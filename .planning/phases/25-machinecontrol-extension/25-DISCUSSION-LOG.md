# Phase 25: MachineControl Extension - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 25-machinecontrol-extension
**Areas discussed:** Bit 20.4 cakismasi, Start latch davranisi, Double Word API tasarimi, Sinif organizasyonu

---

## Bit 20.4 Cakismasi

| Option | Description | Selected |
|--------|-------------|----------|
| Tek sabit paylas (Tavsiye) | CUTTING_STOP_BIT = 4 korunur, cancel_auto_cutting() ayni sabiti kullanir | ✓ |
| Ayri alias sabiti | AUTO_CUTTING_CANCEL_BIT = CUTTING_STOP_BIT alias'i tanimla | |
| Semantik bolumleme | CUTTING_STOP_BIT'i AUTO_CUTTING_CANCEL_BIT olarak yeniden adlandir | |

**User's choice:** Tek sabit paylas (Tavsiye)
**Notes:** PLC tarafinda tek stop biti var, kodda da tek sabit olmali

---

## Start Latch Davranisi

| Option | Description | Selected |
|--------|-------------|----------|
| Set ve birak (Tavsiye) | Bit'i set et, PLC temizlesin. Timer/delay yok | ✓ |
| Set-delay-clear (pulse) | Set, 50ms bekle, clear. Edge-trigger icin | |
| Claude karar versin | Mevcut start_cutting() pattern'ine bakip tutarli davransin | |

**User's choice:** Set ve birak (Tavsiye)
**Notes:** Mevcut start_cutting() ile tutarli. PLC acknowledge edip kendisi temizler.

---

## Double Word API Tasarimi

| Option | Description | Selected |
|--------|-------------|----------|
| Genel amacli (Tavsiye) | _write_double_word(register, value) herhangi bir register icin | ✓ |
| D2064'e ozel | write_target_uzunluk icinde inline, ekstra soyutlama yok | |

**User's choice:** Genel amacli (Tavsiye)
**Notes:** Su an tek kullanim var ama gelecek icin genel amacli tercih edildi

---

## Sinif Organizasyonu

| Option | Description | Selected |
|--------|-------------|----------|
| Ayri bolum (Tavsiye) | # Auto Cutting Control (Otomatik Kesim) basligi altinda | ✓ |
| Mevcut ile birlestir | Cutting Control bolumune ekle | |
| Claude karar versin | Convention'a bakarak belirlesin | |

**User's choice:** Ayri bolum (Tavsiye)
**Notes:** Register sabitleri, bit pozisyonlari ve tum auto-cutting metodlari ayri bolumde

## Claude's Discretion

- Error handling ve loglama detaylari mevcut pattern ile tutarli olacak sekilde Claude belirler
- _write_double_word icindeki _ensure_connected ve error handling Claude'un takdirinde

## Deferred Ideas

None — discussion stayed within phase scope
