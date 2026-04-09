# Phase 27: MainController Integration - Research

**Researched:** 2026-04-09
**Domain:** PySide6 QMainWindow sidebar navigasyon entegrasyonu, IntEnum sabitleri, QStackedWidget
**Confidence:** HIGH

## Summary

Bu faz, Phase 26'da tamamlanan `OtomatikKesimController` widget'ını mevcut `MainController`'a entegre etmeyi kapsar. Tek bir `.py` dosyasının (main_controller.py) ve bir yeni dosyanın (page_index.py) değiştirilmesini içerir; dışarıdan bağımlılık kurulumu gerekmez.

`main_controller.py` incelendiğinde tam olarak değiştirilmesi gereken 6 nokta tespit edilmiştir: sidebar buton tanımları (4 buton → 5 buton + y-koordinat shift), `nav_buttons` listesi, `stackedWidget.addWidget()` çağrıları, lambda'lardaki hardcoded indeksler, `closeEvent` sayfa listesi, ve yeni import. `OtomatikKesimController`'ın constructor imzası `(control_manager, data_pipeline, parent, event_loop)` ve `stop_timers()` metodu mevcut; entegrasyon için değişiklik gerekmez.

**Primary recommendation:** `src/gui/page_index.py` dosyasını oluştur (IntEnum), ardından `main_controller.py`'de 6 değişiklik noktasını atomik olarak güncelle. İki dosya, tek görev.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Otomatik Kesim butonu index 1'e (y=286) eklenir. Yeni sıralama: Kontrol Paneli (0, y=165) → Otomatik Kesim (1, y=286) → Konumlandırma (2, y=407) → Sensör Verileri (3, y=528) → İzleme (4, y=649) → Kamera (5, y=770, koşullu).
- **D-02:** Tüm mevcut butonlar 121px aşağı kayar (y-koordinatları güncellenir). Kamera butonu koşullu kalır, sadece y-koordinatı ve indeksi değişir.
- **D-03:** `src/gui/page_index.py` dosyasında IntEnum tanımlanır: `KONTROL_PANELI=0`, `OTOMATIK_KESIM=1`, `KONUMLANDIRMA=2`, `SENSOR=3`, `IZLEME=4`, `KAMERA=5`. Tüm `_switch_page` lambda'ları ve `nav_buttons` listesi bu sabitleri kullanır.
- **D-04:** Hardcoded sayısal indeksler (0, 1, 2, 3, 4) tamamen kaldırılır ve PageIndex enum değerleriyle değiştirilir.
- **D-05:** Sidebar buton etiketi: "  Otomatik Kesim" (mevcut butonlarla aynı padding pattern'i).
- **D-06:** Buton ikonu: mevcut `cutting-start-icon.svg` kullanılır. Yeni dosya gerekmez. IconSize mevcut butonlarla aynı (QSize(80, 80) veya QSize(70, 70) — mevcut pattern'e uygun).
- **D-07:** Otomatik Kesim sayfası koşulsuz — her zaman sidebar'da görünür ve stackedWidget'a eklenir. Kamera sayfası gibi koşullu değil.
- **D-08:** `closeEvent` içindeki sabit sayfa listesine `otomatik_kesim_page` eklenir. Kamera sayfası ayrı koşullu bloğunu korur.

### Claude's Discretion
- OtomatikKesimController constructor parametreleri (control_manager, data_pipeline, event_loop, parent — Phase 26 pattern'ine uygun)
- Import sıralaması ve dosya organizasyonu
- Buton `setCheckable(True)` ve diğer Qt property'leri mevcut butonlarla tutarlı olacak şekilde

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GUI-01 | Kullanıcı sidebar'dan Otomatik Kesim sayfasına geçebilir (2. sıra) | Tüm entegrasyon noktaları tespit edildi: buton ekleme, stackedWidget.addWidget, _switch_page lambda, nav_buttons, closeEvent |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | >=6.6.0 [VERIFIED: pyproject.toml] | Qt widget framework | Proje genelinde kullanılan tek GUI kütüphanesi |
| Python enum.IntEnum | stdlib [VERIFIED: codebase] | PageIndex sabitleri | Hem int hem de Enum özelliği gerekli (stackedWidget index olarak doğrudan kullanılabilir) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| QStackedWidget | PySide6 | Sayfa geçişleri | Zaten kullanımda — addWidget sırası indeks belirler |
| QPushButton.setCheckable | PySide6 | Aktif buton vurgulaması | Tüm nav butonlarında mevcut pattern |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| IntEnum | Enum | IntEnum `int` ile karşılaştırılabilir — `_switch_page(PageIndex.OTOMATIK_KESIM)` direkt çalışır çünkü IntEnum integer'dır |
| IntEnum | dict/constants | Enum type safety sağlar, typo'ları yakalar |

**Installation:**

Kurulum gerekmez — yalnızca `src/gui/page_index.py` yeni dosya, diğerleri kod değişikliği.

## Architecture Patterns

### Mevcut Proje Yapısı (değişmez)

```
src/gui/
├── controllers/
│   ├── main_controller.py        # BU DOSYA GÜNCELLENIR
│   ├── otomatik_kesim_controller.py  # DOKUNULMAZ (Phase 26 çıktısı)
│   ├── control_panel_controller.py
│   ├── positioning_controller.py
│   ├── sensor_controller.py
│   ├── monitoring_controller.py
│   └── camera_controller.py
├── page_index.py                 # YENİ DOSYA OLUŞTURULUR
└── images/
    └── cutting-start-icon.svg   # MEVCUT (dokunulmaz)
```

### Pattern 1: IntEnum PageIndex Sabiti

**What:** `src/gui/page_index.py` dosyasında IntEnum tanımlanır; tüm lambda'lar ve nav_buttons sıralaması bu değerleri kullanır.

**When to use:** Yeni sayfa eklendiğinde tek bir yerde güncelleme yeterli olur; hardcoded sayılar kalmaz.

**Example:**
```python
# Source: [VERIFIED: src/domain/enums.py pattern]
from enum import IntEnum

class PageIndex(IntEnum):
    KONTROL_PANELI = 0
    OTOMATIK_KESIM = 1
    KONUMLANDIRMA   = 2
    SENSOR          = 3
    IZLEME          = 4
    KAMERA          = 5
```

### Pattern 2: Sidebar Buton Ekleme (Mevcut Pattern)

**What:** Mutlak koordinat layout (setGeometry), `nav_btn_style` ortak stili, `setCheckable(True)`, clicked.connect(lambda: self._switch_page(PageIndex.X))

**Example:**
```python
# Source: [VERIFIED: src/gui/controllers/main_controller.py satır 179-220]
self.btnOtomatikKesim = QPushButton("  Otomatik Kesim", self.sidebarFrame)
self.btnOtomatikKesim.setGeometry(26, 286, 355, 110)   # D-01: y=286
self.btnOtomatikKesim.setIcon(self._icon("cutting-start-icon.svg"))
self.btnOtomatikKesim.setIconSize(QSize(80, 80))       # D-06: mevcut pattern
self.btnOtomatikKesim.setStyleSheet(nav_btn_style)
self.btnOtomatikKesim.setCheckable(True)
self.btnOtomatikKesim.clicked.connect(lambda: self._switch_page(PageIndex.OTOMATIK_KESIM))
```

### Pattern 3: StackedWidget Ekleme Sırası Kritik

**What:** `addWidget()` çağrılarının sırası stackedWidget'taki indeksi belirler. Yeni sayfa index 1'e gelmeli — bu mevcut widget'ların sırasının değiştirilmesini DEĞİL, `otomatik_kesim_page`'in `control_panel_page`'den hemen SONRA eklenmesini gerektirir.

**Example:**
```python
# Source: [VERIFIED: src/gui/controllers/main_controller.py satır 319-331]
self.stackedWidget.addWidget(self.control_panel_page)     # Index 0
self.stackedWidget.addWidget(self.otomatik_kesim_page)    # Index 1 (YENİ)
self.stackedWidget.addWidget(self.positioning_page)       # Index 2
self.stackedWidget.addWidget(self.sensor_page)            # Index 3
self.stackedWidget.addWidget(self.monitoring_page)        # Index 4
# Koşullu kamera hala Index 5
```

### Pattern 4: closeEvent Sabit Sayfa Listesi

**What:** Koşulsuz sayfalar tek bir liste iterasyonuyla durdurulur; kamera ayrı koşullu blokta kalır.

**Example:**
```python
# Source: [VERIFIED: src/gui/controllers/main_controller.py satır 438-445]
for page in [self.control_panel_page, self.otomatik_kesim_page,  # YENİ
             self.positioning_page,
             self.sensor_page, self.monitoring_page]:
    if page and hasattr(page, 'stop_timers'):
        page.stop_timers()

# Kamera koşullu blok değişmez
if hasattr(self, 'camera_page') and self.camera_page ...:
    self.camera_page.stop_timers()
```

### Anti-Patterns to Avoid

- **stackedWidget.insertWidget() kullanmak:** `insertWidget(1, widget)` mevcut widget'ların indekslerini kaydırır ama `nav_buttons` listesini güncellemez — tutarsızlık. `addWidget()` sırası ile `nav_buttons` listesi her zaman eşleşmeli; CONTEXT.md pattern'i addWidget sırasını değiştir, insertWidget kullanma.
- **Lambda capture bug:** `lambda: self._switch_page(i)` döngü içinde kullanılırsa son `i` değerini yakalar. Her buton için ayrı lambda satırı yazmak gerekir (mevcut kod zaten bu pattern'i kullanıyor).
- **PageIndex import'unu unutmak:** `main_controller.py`'de `from ..page_index import PageIndex` import'u eklenmeden enum kullanılamaz.
- **nav_buttons liste sırasını stackedWidget sırasından farklı yapmak:** `_switch_page(index)` hem `nav_buttons[index]` hem de `stackedWidget.setCurrentIndex(index)` kullanır — sıralar eşleşmeli.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sayfa index sabitleri | Sihirli sayılar (0, 1, 2...) | IntEnum | Type-safe, refactor-friendly |
| Buton style tanımı | Yeni CSS | Mevcut `nav_btn_style` değişkeni | Tutarlılık, DRY |
| Icon yükleme | os.path.join manuel | Mevcut `_icon(name)` metodu | Zaten tanımlı, yolu biliyor |
| Timer cleanup | Qt lifecycle'a bırakmak | Explicit `stop_timers()` çağrısı | Linux'ta segfault önlemek için kritik — app.py'deki yorum açıklıyor |

**Key insight:** Bu faz tamamen "kablo bağlama" — yeni bileşen yok, yalnızca mevcut parçaların doğru sıraya konması.

## Common Pitfalls

### Pitfall 1: nav_buttons Liste Sırası ile stackedWidget Sırası Uyuşmazlığı

**What goes wrong:** `_switch_page(index)` hem `nav_buttons[index].setChecked(True)` hem de `stackedWidget.setCurrentIndex(index)` çağrısı yapar. Eğer buton listesi ile addWidget sırası farklıysa yanlış buton highlight olur veya index out-of-range hatası alınır.

**Why it happens:** Bir yerde buton eklenir, diğer yerde unutulur.

**How to avoid:** `nav_buttons` listesine ekleme ve `addWidget()` çağrısı aynı sıra ile yapılmalı. Her ikisini aynı anda güncellemek için yan yana düzenleme.

**Warning signs:** Sidebar'da yanlış buton seçili görünüyor veya sayfa geçişlerinde IndexError.

### Pitfall 2: Kamera Buton İndeksinin Güncellenmesi

**What goes wrong:** Mevcut kamera butonu `lambda: self._switch_page(4)` kullanıyor. Yeni sayfa index 1'e eklenince kamera index 5 olur — bu lambda güncellenmezse kamera sayfası yanlış indekse geçer.

**Why it happens:** Kamera koşullu blokta olduğu için gözden kaçabilir.

**How to avoid:** Kamera lambda'sını da `PageIndex.KAMERA` ile güncelle. Hem lambda hem nav_buttons.append için geçerli.

**Warning signs:** Kamera sayfasına geçince başka bir sayfa görünüyor.

### Pitfall 3: OtomatikKesimController Oluşturulma Sırası

**What goes wrong:** `otomatik_kesim_page` oluşturma kodu `stackedWidget` oluşturulduktan SONRA ve `addWidget` çağrısından ÖNCE gelmelidir. Mevcut pattern'de tüm sayfalar `self.stackedWidget` oluşturulduktan sonra, `addWidget()` bloğundan önce oluşturuluyor.

**Why it happens:** Kod sırası önemli — Qt parent-child.

**How to avoid:** Mevcut sayfa oluşturma bloğuna (satır ~294-316) `otomatik_kesim_page` satırını doğru pozisyona ekle.

**Warning signs:** AttributeError veya widget parent sorunu.

### Pitfall 4: stop_timers() Çağrısı — OtomatikKesimController'ın İki Timer'ı Var

**What goes wrong:** `_polling_timer` ve `_reset_tick_timer` — ikisi de stop edilmeli. `stop_timers()` metodu zaten her ikisini de durduruyor (verified), ama closeEvent'e sadece nesnenin eklenmesi yeterli.

**Why it happens:** OtomatikKesimController 500ms D2056 polling timer'ı var — Linux'ta `closeEvent` tetiklendiğinde GUI thread'de durdurulmazsa segfault.

**How to avoid:** `otomatik_kesim_page` koşulsuz sayfa listesine eklenmeli (D-08). Verify: `stop_timers()` `_polling_timer` ve `_reset_tick_timer`'ı durduruyor — satır 534-545 doğrulandı.

**Warning signs:** Uygulama kapanırken "Timers cannot be stopped from another thread" hatası.

## Code Examples

Verified patterns from official sources:

### OtomatikKesimController Constructor İmzası

```python
# Source: [VERIFIED: src/gui/controllers/otomatik_kesim_controller.py satır 106-113]
class OtomatikKesimController(QWidget):
    def __init__(
        self,
        control_manager=None,
        data_pipeline=None,
        parent=None,
        event_loop=None,
    ):
```

Kullanım: `ControlPanelController` pattern'i ile aynı — `parent=self.stackedWidget`.

### Mevcut Buton Y-Koordinatları (Değişmeden Önce)

```python
# Source: [VERIFIED: src/gui/controllers/main_controller.py satır 170-219]
# Kontrol Paneli  → y=165  (değişmez, zaten index 0)
# Konumlandırma   → y=286  (→ 407 olacak, +121px)
# Sensör          → y=407  (→ 528 olacak, +121px)
# İzleme          → y=528  (→ 649 olacak, +121px)
# Kamera          → y=649  (→ 770 olacak, +121px, koşullu)
```

### Yeni Y-Koordinatları (D-01, D-02)

| Buton | Eski y | Yeni y | İndeks |
|-------|--------|--------|--------|
| Kontrol Paneli | 165 | 165 | 0 |
| Otomatik Kesim | — | 286 | 1 (YENİ) |
| Konumlandırma | 286 | 407 | 2 |
| Sensör Verileri | 407 | 528 | 3 |
| İzleme | 528 | 649 | 4 |
| Kamera (koşullu) | 649 | 770 | 5 |

### Mevcut Lambda Indeksleri (Değişmeden Önce — TAMAMI DEĞİŞECEK)

```python
# Source: [VERIFIED: src/gui/controllers/main_controller.py satır 177-219]
# btnControlPanel  → lambda: self._switch_page(0)  → PageIndex.KONTROL_PANELI
# btnPositioning   → lambda: self._switch_page(1)  → PageIndex.KONUMLANDIRMA
# btnSensor        → lambda: self._switch_page(2)  → PageIndex.SENSOR
# btnTracking      → lambda: self._switch_page(3)  → PageIndex.IZLEME
# btnCamera        → lambda: self._switch_page(4)  → PageIndex.KAMERA
```

### nav_buttons Listesi (Değişmeden Önce — satır 204-209)

```python
# Source: [VERIFIED: src/gui/controllers/main_controller.py satır 203-209]
self.nav_buttons = [
    self.btnControlPanel,   # index 0
    self.btnPositioning,    # index 1 → index 2 olacak
    self.btnSensor,         # index 2 → index 3 olacak
    self.btnTracking        # index 3 → index 4 olacak
]
# Kamera koşullu: self.nav_buttons.append(self.btnCamera)  → index 4 → 5 olacak
```

### Import Eklenmesi (main_controller.py başına)

```python
# Yeni satır — mevcut controller import'larının yanına eklenecek
from ..page_index import PageIndex
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded int indeksler | PageIndex IntEnum | Bu faz | Gelecek sayfa eklemelerinde tek nokta değişiklik |
| 4 sayfa | 5 sayfa + kamera | Bu faz | nav_buttons ve stackedWidget tutarlı güncellenmeli |

**Deprecated/outdated:**

- `lambda: self._switch_page(1)` (konumlandırma): PageIndex.KONUMLANDIRMA olacak
- `lambda: self._switch_page(2)` (sensör): PageIndex.SENSOR olacak
- `lambda: self._switch_page(3)` (izleme): PageIndex.IZLEME olacak
- `lambda: self._switch_page(4)` (kamera): PageIndex.KAMERA olacak

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | IconSize QSize(80, 80) — Kontrol Paneli QSize(70, 70) kullanıyor, diğerleri 80x80 | Standard Stack | Görsel tutarsızlık; düşük risk, kolay düzeltilir |

**Not:** A1 için: `btnControlPanel` `QSize(70, 70)` [VERIFIED satır 173], diğer 3 buton `QSize(80, 80)` [VERIFIED satır 181, 189, 197] kullanıyor. D-06 "mevcut butonlarla aynı" diyor — yeni buton için `QSize(80, 80)` kullanmak daha tutarlı (3'e karşı 1).

## Open Questions

1. **Kontrol Paneli butonu QSize(70, 70) mi, yeni buton QSize(80, 80) mi olmalı?**
   - What we know: `btnControlPanel` 70x70, diğer 3 buton 80x80 kullanıyor [VERIFIED]
   - What's unclear: D-06 "mevcut pattern'e uygun" diyor ama iki farklı boyut var
   - Recommendation: Çoğunluk pattern'ini (80x80) kullan; kontrol paneli tarihsel bir sapma gibi görünüyor

## Environment Availability

Step 2.6: SKIPPED — Bu faz yalnızca Python kod/dosya değişikliklerini kapsar. Dışarıdan CLI aracı, servis, veya runtime bağımlılığı yok; PySide6 zaten kurulu (`pyproject.toml` ve `src/gui/app.py` doğrulanmış).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (pyproject.toml'da setuptools, test'ler `import pytest` kullanıyor) |
| Config file | Yok — pytest.ini veya `[tool.pytest]` bölümü bulunamadı |
| Quick run command | `python -m pytest tests/test_otomatik_kesim_controller.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GUI-01 | Sidebar navigasyon: Otomatik Kesim sayfasına geçiş | unit (smoke) | `python -m pytest tests/test_main_controller_integration.py -x -q` | ❌ Wave 0 |
| GUI-01 | PageIndex enum değerleri doğru | unit | `python -m pytest tests/test_page_index.py -x -q` | ❌ Wave 0 |
| GUI-01 | closeEvent otomatik_kesim_page.stop_timers() çağırır | unit | `python -m pytest tests/test_main_controller_integration.py::test_close_event_stops_otomatik_kesim_timers -x -q` | ❌ Wave 0 |

**Not:** Mevcut `test_otomatik_kesim_controller.py` Phase 26 testlerini kapsıyor ve dokunulmayacak. Bu faz için yeni test dosyası gerekiyor — ancak QApplication bağımlılığı olmadan `__new__` injection pattern'i kullanılabilir (aynı proje pattern'i).

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_otomatik_kesim_controller.py -x -q` (mevcut testler bozulmadı mı?)
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_main_controller_integration.py` — GUI-01 navigasyon ve closeEvent testleri; `__new__` injection pattern ile QApplication gerektirmez
- [ ] `tests/test_page_index.py` — PageIndex enum değer doğrulaması (opsiyonel, basit)

*(Mevcut test altyapısı var; pytest kurulu; pattern biliniyor — gap yalnızca bu faza özel yeni test dosyaları)*

## Security Domain

Bu faz yalnızca GUI navigasyon entegrasyonunu kapsar — sayfa geçişleri, buton layout, ve timer cleanup. Kullanıcı giriş validasyonu, ağ, kriptografi, kimlik doğrulama veya erişim kontrolü yok. ASVS kategorileri uygulanamaz.

## Sources

### Primary (HIGH confidence)

- `src/gui/controllers/main_controller.py` — Tüm değiştirilecek kod satırları doğrudan incelendi (satır 170-453)
- `src/gui/controllers/otomatik_kesim_controller.py` — Constructor imzası (satır 106-113) ve stop_timers() (satır 534-545) doğrulandı
- `src/domain/enums.py` — Mevcut IntEnum pattern'i referans için incelendi
- `pyproject.toml` — PySide6 >=6.6.0 bağımlılığı doğrulandı
- `tests/test_otomatik_kesim_controller.py` — Test pattern'i (`__new__` injection) incelendi

### Secondary (MEDIUM confidence)

- `src/gui/app.py` — Qt lifecycle (shiboken6 delete, Linux segfault açıklaması) arka plan bilgisi
- `.planning/phases/27-maincontroller-integration/27-CONTEXT.md` — Tüm kararlar (D-01..D-08)

### Tertiary (LOW confidence)

Yok.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — PySide6 pyproject.toml'da doğrulandı; IntEnum stdlib
- Architecture: HIGH — Mevcut main_controller.py satır satır incelendi; tüm değişiklik noktaları tespit edildi
- Pitfalls: HIGH — nav_buttons/stackedWidget sıra uyuşmazlığı kodu okuyarak doğrulandı; kamera lambda güncelleme gereksinimi doğrulandı

**Research date:** 2026-04-09
**Valid until:** 2026-05-09 (kararlı kod tabanı, hızlı değişmiyor)
