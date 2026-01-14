# Smart Saw - Database Field Additions

## What This Is

Smart Saw endüstriyel testere kontrol sistemi için database şema güncellemesi. ML ve anomali veritabanlarına ek alanlar eklenerek veri kaydı zenginleştirilecek.

## Core Value

ML ve anomali kayıtlarında tork ve kafa yüksekliği verilerinin saklanması — geçmişe dönük analiz için kritik verinin eksik kalmaması.

## Requirements

### Validated

- ✓ Modbus TCP ile PLC haberleşmesi — existing
- ✓ 10 Hz veri okuma ve işleme — existing
- ✓ Manuel ve ML kontrol modları — existing
- ✓ 9 anomali dedektörü — existing
- ✓ SQLite veritabanları (raw, total, log, ml, anomaly) — existing
- ✓ PySide6 desktop GUI — existing
- ✓ ThingsBoard IoT telemetri — existing
- ✓ PostgreSQL uzak veritabanı desteği — existing

### Active

- [ ] ML database'ine tork (serit_motor_tork) alanı eklenmesi
- [ ] ML database'ine kafa yüksekliği (kafa_yuksekligi) alanı eklenmesi
- [ ] Anomali database'ine kafa yüksekliği (kafa_yuksekligi) alanı eklenmesi

### Out of Scope

- ML modeli değişikliği — bu alanlar sadece kayıt amaçlı, model inputu değil
- Yeni anomali dedektörü — kafa yüksekliği sadece kayıt için, tespit için değil
- GUI değişiklikleri — backend schema değişikliği yeterli

## Context

**Mevcut Durum:**
- ML predictions tablosu: `akim_input`, `sapma_input`, `kesme_hizi_input`, `inme_hizi_input`, `yeni_kesme_hizi`, `yeni_inme_hizi`, `katsayi`, `ml_output`
- Anomaly events tablosu: `timestamp`, `sensor_name`, `sensor_value`, `detection_method`, `kesim_id`

**Eklenecek Veriler:**
- Tork ve kafa yüksekliği verileri zaten `RawSensorData` ve `ProcessedData` modellerinde mevcut
- Bu veriler sadece ML ve anomali tablolarına ek olarak kaydedilecek

## Constraints

- **Geriye Uyumluluk**: Mevcut veritabanı dosyaları korunmalı, ALTER TABLE ile ekleme yapılmalı
- **Veri Kaynağı**: Veriler mevcut `RawSensorData`/`ProcessedData` modellerinden alınacak

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Sadece kayıt amaçlı ekleme | ML model inputu değişmeyecek, geriye dönük analiz için | — Pending |
| ALTER TABLE kullanımı | Mevcut veri kaybı önlenmeli | — Pending |

---
*Last updated: 2026-01-15 after initialization*
