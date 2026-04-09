# Phase 27: MainController Integration - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Tamamlanan OtomatikKesimController sayfasını sidebar'dan erişilebilir hale getir ve mevcut tüm navigasyon butonlarını doğru sayfa indekslerine güncelle. Yeni sayfa index 1'e eklenir; mevcut tüm _switch_page lambda'ları PageIndex sabitlerini kullanacak şekilde güncellenir.

</domain>

<decisions>
## Implementation Decisions

### Sidebar Sıralama & İndeks Shift
- **D-01:** Otomatik Kesim butonu index 1'e (y=286) eklenir. Yeni sıralama: Kontrol Paneli (0, y=165) → Otomatik Kesim (1, y=286) → Konumlandırma (2, y=407) → Sensör Verileri (3, y=528) → İzleme (4, y=649) → Kamera (5, y=770, koşullu).
- **D-02:** Tüm mevcut butonlar 121px aşağı kayar (y-koordinatları güncellenir). Kamera butonu koşullu kalır, sadece y-koordinatı ve indeksi değişir.

### PageIndex Sabitleri
- **D-03:** `src/gui/page_index.py` dosyasında IntEnum tanımlanır: `KONTROL_PANELI=0`, `OTOMATIK_KESIM=1`, `KONUMLANDIRMA=2`, `SENSOR=3`, `IZLEME=4`, `KAMERA=5`. Tüm `_switch_page` lambda'ları ve `nav_buttons` listesi bu sabitleri kullanır.
- **D-04:** Hardcoded sayısal indeksler (0, 1, 2, 3, 4) tamamen kaldırılır ve PageIndex enum değerleriyle değiştirilir.

### Buton İkonu ve Etiketi
- **D-05:** Sidebar buton etiketi: "  Otomatik Kesim" (mevcut butonlarla aynı padding pattern'i).
- **D-06:** Buton ikonu: mevcut `cutting-start-icon.svg` kullanılır. Yeni dosya gerekmez. IconSize mevcut butonlarla aynı (QSize(80, 80) veya QSize(70, 70) — mevcut pattern'e uygun).

### Koşullu vs Sabit Ekleme
- **D-07:** Otomatik Kesim sayfası koşulsuz — her zaman sidebar'da görünür ve stackedWidget'a eklenir. Kamera sayfası gibi koşullu değil. MachineControl singleton zaten bağlantı yokken sessizce başarısız olur.

### closeEvent & Timer Cleanup
- **D-08:** `closeEvent` içindeki sabit sayfa listesine `otomatik_kesim_page` eklenir. Kamera sayfası ayrı koşullu bloğunu korur (koşullu olduğu için).

### Claude's Discretion
- OtomatikKesimController constructor parametreleri (control_manager, data_pipeline, event_loop, parent — Phase 26 pattern'ine uygun)
- Import sıralaması ve dosya organizasyonu
- Buton `setCheckable(True)` ve diğer Qt property'leri mevcut butonlarla tutarlı olacak şekilde

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### MainController (entegrasyon noktası)
- `src/gui/controllers/main_controller.py` — Sidebar butonları, QStackedWidget, _switch_page, closeEvent, nav_buttons listesi, sayfa oluşturma ve ekleme pattern'i

### OtomatikKesimController (Phase 26 çıktısı)
- `src/gui/controllers/otomatik_kesim_controller.py` — Entegre edilecek sayfa widget'ı, constructor parametreleri, stop_timers() metodu

### Mevcut Sayfa Pattern'leri
- `src/gui/controllers/control_panel_controller.py` — Sayfa constructor pattern'i (control_manager, data_pipeline, parent, event_loop)
- `src/gui/controllers/camera_controller.py` — Koşullu sayfa ekleme pattern'i (karşılaştırma için)

### İkon Dosyası
- `src/gui/images/cutting-start-icon.svg` — Otomatik Kesim sidebar ikonu

### Gereksinimler ve Roadmap
- `.planning/REQUIREMENTS.md` — GUI-01 (sidebar navigasyon)
- `.planning/milestones/v2.1-ROADMAP.md` — Phase 27 success criteria
- `.planning/phases/26-otomatik-kesim-controller/26-CONTEXT.md` — Phase 26 kararları (sayfa layout, timer'lar, constructor bağımlılıkları)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_switch_page(index)` metodu — zaten indeks bazlı sayfa değiştirme yapıyor, sadece PageIndex enum'a geçiş gerekli
- `nav_btn_style` — tüm sidebar butonları için ortak stil, yeni buton da aynı stili kullanır
- `_icon(name)` — src/gui/images/ klasöründen SVG yükler

### Established Patterns
- Mutlak koordinat layout (setGeometry) — tüm sidebar butonları bu pattern'i kullanıyor
- `setCheckable(True)` + `setChecked` — aktif sayfa vurgulaması
- `nav_buttons` listesi — buton indeksi ile sayfa indeksi eşleşir
- Koşullu sayfa ekleme (Kamera): constructor'da `if store is not None` bloğu
- Import: lazy import sadece koşullu sayfalar için (CameraController)

### Integration Points
- `stackedWidget.addWidget()` — sayfa ekleme sırası indeks belirler
- `nav_buttons` listesine buton ekleme sırası _switch_page indeksi ile eşleşmeli
- `closeEvent` sabit sayfa listesi — yeni sayfa eklenmeli
- OtomatikKesimController'a geçirilecek parametreler: control_manager, data_pipeline, event_loop, parent (stackedWidget)

</code_context>

<specifics>
## Specific Ideas

- PageIndex IntEnum sayesinde gelecekte yeni sayfa eklemek tek bir enum değeri ve sıralama güncellemesiyle yapılabilir
- Kamera sayfası koşullu kalmaya devam eder — PageIndex.KAMERA sabiti tanımlı olsa da, kamera devre dışıyken stackedWidget'a eklenmez
- Buton y-koordinatları 121px aralıkla (y=165'ten başlayarak): 165, 286, 407, 528, 649, 770

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 27-maincontroller-integration*
*Context gathered: 2026-04-09*
