# Phase 25: MachineControl Extension - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

PLC ile dogrudan iletisimi yoneten MachineControl singleton'a otomatik kesim sayfasinin ihtiyac duydugu tum register ve bit operasyonlarini ekle. Yeni register sabitleri (D2050, D2064/D2065, D2056), Double Word yazma destegi (FC16), ve kontrol bit metodlari (start/reset/cancel) eklenir. UI veya sayfa mantigi bu faza dahil degildir.

</domain>

<decisions>
## Implementation Decisions

### Bit 20.4 Cakismasi
- **D-01:** Mevcut `CUTTING_STOP_BIT = 4` sabiti korunacak. `cancel_auto_cutting()` ayni sabiti kullanacak. PLC tarafinda tek bir stop/cancel biti var, kodda da tek sabit olmali.

### Start Latch Davranisi
- **D-02:** `start_auto_cutting()` bit 20.13'u set edip birakacak (fire-and-forget). PLC acknowledge ettikten sonra kendisi temizleyecek. MachineControl tarafinda timer/delay/pulse yok. Mevcut `start_cutting()` pattern'i ile tutarli.

### Double Word API Tasarimi
- **D-03:** Genel amacli `_write_double_word(register: int, value: int) -> bool` metodu eklenecek. Mitsubishi low-word-first convention icinde: `low_word = value & 0xFFFF`, `high_word = (value >> 16) & 0xFFFF`. `client.write_registers(address=register, values=[low_word, high_word])` ile FC16 cagrisi. Tek kullanim (D2064) olsa da gelecek icin genel amacli.

### Sinif Organizasyonu
- **D-04:** Yeni metodlar `# Auto Cutting Control (Otomatik Kesim)` basligi altinda ayri bir bolumde olacak. Bu bolum su sirayla icerir:
  - Register address sabitleri: `TARGET_ADET_REGISTER = 2050`, `TARGET_LENGTH_REGISTER = 2064`, `CUT_COUNT_REGISTER = 2056`
  - Bit position sabitleri: `AUTO_CUTTING_START_BIT = 13`, `AUTO_CUTTING_RESET_BIT = 14`
  - Metodlar: `write_target_adet(p, x)`, `write_target_uzunluk(l_mm)`, `read_kesilmis_adet()`, `start_auto_cutting()`, `reset_auto_cutting(active)`, `cancel_auto_cutting()`

### Claude's Discretion
- Hata loglama detaylari ve exception handling pattern'i mevcut _write_register/_read_register ile tutarli olacak sekilde Claude belirler
- _write_double_word icindeki _ensure_connected cagrisi ve error handling Claude'un takdirine birakildi

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### MachineControl Kaynak Dosyasi
- `src/services/control/machine_control.py` — Mevcut MachineControl singleton, tum register/bit sabitleri ve metodlari burada

### Proje Arsitekturu
- `.planning/codebase/ARCHITECTURE.md` — Katmanli mimari, concurrency modeli, MachineControl'un service layer'daki yeri
- `.planning/codebase/CONVENTIONS.md` — Naming, import, error handling, docstring conventions

### Gereksinimler ve Roadmap
- `.planning/REQUIREMENTS.md` — PLC-01..04, CTRL-01..03 gereksinimleri (Phase 25'e mapped)
- `.planning/milestones/v2.1-ROADMAP.md` — Phase 25 detaylari, success criteria, word order verification notu

### Proje Durumu
- `.planning/STATE.md` — Onceki kararlar: register 20 bit ops MachineControl uzerinden, D2064/D2065 FC16, Mitsubishi low-word-first, open verification items

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_read_register(register)` — Tek register okuma, D2056 icin dogrudan kullanilabilir
- `_write_register(register, value)` — Tek register yazma, D2050 Word yazimi icin kullanilabilir
- `_set_bit(register, bit_position, value)` — Bit set/clear, start/reset/cancel icin kullanilabilir
- `_ensure_connected()` — Baglanti kontrolu, yeni _write_double_word icinde de kullanilmali
- `_write_register_atomic(register, set_bits, clear_bits)` — Coklu bit islemleri icin (gerekirse)

### Established Patterns
- Singleton pattern: `__new__` + `_lock` ile thread-safe
- Synchronous Modbus: `ModbusTcpClient` (pymodbus), async degil
- Connection cooldown: `_should_attempt_connect()` ile reconnect limiti
- Section-based class organization: Her kontrol grubu icin `# ===` baslikli bolum
- Bit constants: Class-level, 0-based (`BIT_NAME = N  # register.N`)
- Register constants: Class-level (`REGISTER_NAME = address`)

### Integration Points
- `cancel_auto_cutting()` mevcut `CUTTING_STOP_BIT = 4` sabitini paylasacak
- `write_cutting_speed()` ve `write_descent_speed()` zaten Speed Control bolumunde — C ve S parametreleri Phase 26'da bu metodlar uzerinden yazilabilir
- `pymodbus.client.ModbusTcpClient.write_registers()` FC16 icin kullanilacak (mevcut client instance)

</code_context>

<specifics>
## Specific Ideas

- D2064 word order dogrulamasi: L=1000mm icin D2064=0x2710 (10000), D2065=0x0000 olmali — unit test ile kontrol edilmeli
- Bit 20.13 latch: PLC tarafinin temizleyecegi varsayildi, ancak gercek PLC'de dogrulanmali
- RESET hold duration (1500ms) Phase 26'da GUI tarafinda uygulanacak; Phase 25'teki `reset_auto_cutting(active: bool)` sadece set/clear yapar

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 25-machinecontrol-extension*
*Context gathered: 2026-04-09*
