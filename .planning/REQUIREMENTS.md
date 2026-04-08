# Requirements: Smart Saw

**Defined:** 2026-04-09
**Core Value:** Endustriyel testere operasyonlarinin guvenilir kontrolu ve serit testere sagliginin yapay zeka ile surekli izlenmesi

## v2.1 Requirements

Requirements for Otomatik Kesim Sayfası milestone. Each maps to roadmap phases.

### GUI (Sayfa & Navigasyon)

- [ ] **GUI-01**: Kullanıcı sidebar'dan Otomatik Kesim sayfasına geçebilir (2. sıra)
- [ ] **GUI-02**: Aktif kesim sırasında parametre giriş alanları devre dışı kalır
- [ ] **GUI-03**: Kesilmiş adet sayısı sayfada gerçek zamanlı görüntülenir

### PARAM (Parametre Girişi)

- [ ] **PARAM-01**: Kullanıcı P (hedef adet) değerini girebilir
- [ ] **PARAM-02**: Kullanıcı L (uzunluk mm, ondalıklı) değerini girebilir
- [ ] **PARAM-03**: Kullanıcı C (kesim hızı m/dk) değerini girebilir
- [ ] **PARAM-04**: Kullanıcı S (inme hızı m/dk) değerini girebilir
- [ ] **PARAM-05**: Kullanıcı X (paketteki adet) değerini girebilir

### PLC (PLC Haberleşme)

- [ ] **PLC-01**: P×X hesaplanıp D2050'ye Word olarak yazılır
- [ ] **PLC-02**: L×10 değeri D2064'e Double Word olarak yazılır
- [ ] **PLC-03**: D2056'dan kesilmiş adet periyodik olarak okunur
- [ ] **PLC-04**: MachineControl'a Double Word yazma desteği eklenir (write_registers FC16)

### CTRL (Kontrol Komutları)

- [ ] **CTRL-01**: START butonu Adres 20 Bit 13'ü set eder
- [ ] **CTRL-02**: RESET butonu hold-delay ile Adres 20 Bit 14'ü basılı tutma süresince set eder
- [ ] **CTRL-03**: İPTAL butonu Adres 20 Bit 4'ü set eder

### ML (ML Kesim Modu)

- [ ] **ML-01**: Kullanıcı otomatik kesim sayfasından ML kesim modunu etkinleştirebilir
- [ ] **ML-02**: Seri kesimde her yeni kesim başladığında ML state sıfırdan başlar

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

(None identified)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| İlerleme çubuğu (progress bar) | Kesilmiş adet gösterimi yeterli |
| Kesim geçmişi/log sayfası | Veri toplama önce, görselleştirme sonra |
| Otomatik hız optimizasyonu | ML modu zaten hız ayarı yapıyor |
| Multi-job kuyruk sistemi | Tek seri kesim işlemi yeterli |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GUI-01 | — | Pending |
| GUI-02 | — | Pending |
| GUI-03 | — | Pending |
| PARAM-01 | — | Pending |
| PARAM-02 | — | Pending |
| PARAM-03 | — | Pending |
| PARAM-04 | — | Pending |
| PARAM-05 | — | Pending |
| PLC-01 | — | Pending |
| PLC-02 | — | Pending |
| PLC-03 | — | Pending |
| PLC-04 | — | Pending |
| CTRL-01 | — | Pending |
| CTRL-02 | — | Pending |
| CTRL-03 | — | Pending |
| ML-01 | — | Pending |
| ML-02 | — | Pending |

**Coverage:**
- v2.1 requirements: 17 total
- Mapped to phases: 0
- Unmapped: 17 ⚠️

---
*Requirements defined: 2026-04-09*
*Last updated: 2026-04-09 after initial definition*
