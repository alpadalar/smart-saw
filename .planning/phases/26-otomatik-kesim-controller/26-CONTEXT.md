# Phase 26: OtomatikKesimController - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Operatör, otomatik kesim sayfasında iş parametrelerini girebilir, sayaç gerçek zamanlı izlenebilir, ML modu etkinleştirilebilir ve kontrol butonları PLC'yi tetikler. Bu faz tam sayfa widget'ı oluşturur — MachineControl altyapısı Phase 25'te tamamlandı, navigasyon entegrasyonu Phase 27'de yapılacak.

</domain>

<decisions>
## Implementation Decisions

### Sayfa Düzeni
- **D-01:** Sol-Sağ iki sütun layout. Sol sütun: parametre alanları. Sağ sütun: sayaç gösterimi (üst) + kontrol butonları (alt).
- **D-02:** P ve X yan yana (üst satır), aralarında/altlarında P×X toplam etiketi. L, C, S alt kısımda tek sütun dikey sıralı.
- **D-03:** Sağ sütun üst bölümünde büyük sayaç gösterimi "X / Y" formatında + yatay gradient progress bar. Alt bölümünde kontrol butonları (START, RESET, İPTAL) + ML modu butonları.

### Parametre Girişi
- **D-04:** Tüm parametre alanlarına dokunulduğunda mevcut NumpadDialog açılır (kontrol paneli ile aynı pattern). `NumpadDialog(parent, initial_value=str)` kullanımı.
- **D-05:** NumpadDialog'a `allow_decimal=True` parametresi eklenir. True olduğunda "." butonu görünür (L alanı için). Mevcut tamsayı davranışı varsayılan olarak korunur.
- **D-06:** Değer aralıkları: P (hedef adet): 1-9999 tamsayı, L (uzunluk): 1-99999 mm ondalıklı (0.1mm hassasiyet), X (paketteki adet): 1-999 tamsayı. C ve S: 0-500 m/dk (mevcut kontrol paneli ile aynı aralık).
- **D-07:** C ve S parametreleri aynı PLC register'larına yazılır: `MachineControl.write_cutting_speed()` ve `MachineControl.write_descent_speed()`. Her iki sayfadan yazılabilir, son yazan kazanır.
- **D-08:** P×X toplam etiketi P ve X frame'lerinin hemen altında gösterilir: "Toplam: {P×X} adet". P veya X değiştiğinde anlık güncellenir.

### Kontrol Butonları
- **D-09:** START butonu: Önce `_validate_params()` çalışır. Hata varsa START butonunun altında kırmızı Türkçe uyarı mesajı görünür (3 saniye sonra kaybolur). Geçerliyse `MachineControl.start_auto_cutting()` çağrılır.
- **D-10:** Aktif kesim sırasında START butonu devre dışı olur (gri/soluk), metni "DEVAM EDİYOR..." olarak değişir. RESET ve İPTAL aktif kalır.
- **D-11:** RESET butonu: TouchButton widget'ı kullanılır (4 sinyal: pressed/released + touch_pressed/touch_released). 1500ms basılı tutma. Buton içinde sol→sağ doluluk animasyonu (gradient progress). Erken bırakılırsa animasyon sıfırlanır, reset edilmez. Tutma süresi dolduğunda `MachineControl.reset_auto_cutting(True)` çağrılır, bırakıldığında `reset_auto_cutting(False)`.
- **D-12:** İPTAL butonu: `MachineControl.cancel_auto_cutting()` çağrılır. Sonrasında parametre alanları tekrar aktif olur (setEnabled(True)), sayaç gösterimi sıfırlanır, progress bar boşalır.

### Sayaç ve Tamamlanma
- **D-13:** Kesilmiş adet sayacı 500ms QTimer ile D2056'dan okunur (`MachineControl.read_kesilmis_adet()`). Format: "X / Y" (kesilen / hedef).
- **D-14:** Aktif kesim sırasında (D2056 > 0 ve hedef aşılmamış) P, L, X, C, S parametre alanları `setEnabled(False)` ile devre dışı.
- **D-15:** Hedef adede ulaşıldığında sayaç ve progress bar yeşile döner, "Tamamlandı!" mesajı gösterilir. Parametreler tekrar aktif olur.

### ML Modu
- **D-16:** Manual/AI buton çifti kullanılır (kontrol panelindeki ile aynı pattern). Checkbox yerine iki toggle buton.
- **D-17:** Sayfa açıldığında mevcut mod control_manager'dan okunarak butonlar senkronize edilir. İki yönlü senkron: bu sayfadan mod değiştirince kontrol panelindeki butonlar da güncellenir (aynı `control_manager.set_mode()` çağrısı).
- **D-18:** Her yeni kesim başlangıcında ML state sıfırlanır. D2056 sayacı değiştiğinde (yeni kesim) ML state reset tetiklenir.

### Claude's Discretion
- Sayfa widget sınıf yapısı ve iç metod organizasyonu
- Frame boyutları ve koordinatları (1528x1080 içerik alanına uygun)
- Gradient renkleri ve font boyutları (mevcut tema ile tutarlı)
- Hata mesajı timeout mekanizması (QTimer veya QPropertyAnimation)
- RESET progress animasyonunun implementasyon detayı (QPainter overlay veya style sheet)
- D2056 değişim algılama mekanizması (önceki değer karşılaştırması)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### MachineControl (Phase 25 altyapısı)
- `src/services/control/machine_control.py` — Auto Cutting Control bölümü: write_target_adet, write_target_uzunluk, read_kesilmis_adet, start/reset/cancel_auto_cutting
- `src/services/control/machine_control.py` — Speed Control bölümü: write_cutting_speed, write_descent_speed (C ve S parametreleri)

### GUI Bileşenleri
- `src/gui/numpad.py` — NumpadDialog sınıfı. allow_decimal parametresi eklenecek.
- `src/gui/widgets/touch_button.py` — TouchButton widget'ı (RESET butonu için pressed/released + touch_pressed/touch_released sinyalleri)
- `src/gui/controllers/control_panel_controller.py` — Numpad kullanım pattern'i (_handle_cutting_speed_frame_click, _handle_descent_speed_frame_click) ve ML mod değiştirme (_handle_cutting_mode_buttons, _switch_controller)
- `src/gui/controllers/main_controller.py` — Sayfa yapısı, QStackedWidget, sidebar navigasyonu, closeEvent timer cleanup

### Domain Modelleri
- `src/domain/enums.py` — ControlMode enum (MANUAL, ML)

### Gereksinimler ve Roadmap
- `.planning/REQUIREMENTS.md` — PARAM-01..05, GUI-02, GUI-03, ML-01, ML-02
- `.planning/milestones/v2.1-ROADMAP.md` — Phase 26 success criteria
- `.planning/phases/25-machinecontrol-extension/25-CONTEXT.md` — Phase 25 kararları (bit operasyonları, fire-and-forget, word order)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NumpadDialog` (src/gui/numpad.py): Touch-friendly numpad, initial_value desteği. allow_decimal parametresi eklenecek.
- `TouchButton` (src/gui/widgets/touch_button.py): pressed/released + touch_pressed/touch_released sinyalleri. RESET hold-delay için ideal.
- `MachineControl` auto cutting methods: write_target_adet(p, x), write_target_uzunluk(l_mm), read_kesilmis_adet(), start/reset/cancel_auto_cutting()
- `MachineControl` speed methods: write_cutting_speed(), write_descent_speed()
- `ControlMode` enum ve `control_manager.set_mode()` pattern'i

### Established Patterns
- Mutlak koordinat layout (QFrame.setGeometry) — tüm sayfalar bu pattern'i kullanıyor
- Koyu gradient tema: navy (#060B2A) -> mavi (#226AFC), Plus Jakarta Sans font
- NumpadDialog -> exec() -> Accepted -> get_value() -> MachineControl yazma akışı
- Thread-safe mod değiştirme: asyncio.run_coroutine_threadsafe(control_manager.set_mode(), event_loop)
- Sayfa boyutu: 1528x1080 (content area)
- Qt timer cleanup: closeEvent'te stop_timers() çağrısı

### Integration Points
- QStackedWidget'a yeni sayfa olarak eklenir (Phase 27'de)
- control_manager ve data_pipeline constructor parametreleri olarak geçer (MainController pattern'i)
- event_loop parametresi async mode switch için gerekli
- 500ms QTimer -> D2056 polling (async pipeline'a dokunmaz)

</code_context>

<specifics>
## Specific Ideas

- RESET buton animasyonu: Basılı tutulduğunda buton içinde sol->sağ gradient doluluk (1.5s). TouchButton sinyalleri ile tetiklenir.
- Sayaç büyük font ile sağ sütün üst kısmında göze çarpar pozisyonda. Progress bar altında gradient (mavi->yeşil tamamlandığında).
- P*X toplam hesaplanır ama PLC'ye yazılan değer write_target_adet(p, x) ile gider (MachineControl içinde P*X çarpımı yapılır).
- START validasyonu: P, L, X zorunlu (>0). C ve S opsiyonel (kontrol panelinden girilmiş olabilir).
- ML state sıfırlama: D2056 polling callback'inde önceki değer ile karşılaştırma — değişiklik algılandığında control_manager.set_mode() ile temiz başlangıç.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 26-otomatik-kesim-controller*
*Context gathered: 2026-04-09*
