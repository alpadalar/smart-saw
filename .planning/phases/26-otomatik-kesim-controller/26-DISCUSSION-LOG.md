# Phase 26: OtomatikKesimController - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 26-otomatik-kesim-controller
**Areas discussed:** Sayfa Düzeni, Parametre Girişi, Kontrol & Sayaç, ML Modu

---

## Sayfa Düzeni

| Option | Description | Selected |
|--------|-------------|----------|
| Üst-Alt iki bölüm | Üst: parametreler yatay. Alt: butonlar + sayaç | |
| Sol-Sağ iki sütun | Sol: parametreler dikey. Sağ: sayaç + kontrol | ✓ |
| Tek alan dikey akış | Tüm öğeler tek sütunda yukarıdan aşağı | |

**User's choice:** Sol-Sağ iki sütun
**Notes:** P ve X yan yana olsun (kullanıcı notu)

---

| Option | Description | Selected |
|--------|-------------|----------|
| NumpadDialog | Mevcut pattern, touch-friendly, kodda var | ✓ |
| Satır içi edit | QLineEdit ile doğrudan yazma | |
| Spinner/stepper | +/- butonları | |

**User's choice:** NumpadDialog (mevcut pattern)

---

| Option | Description | Selected |
|--------|-------------|----------|
| P+X üst, L, C, S alt | P ve X yan yana üst satır, P×X toplam altında | ✓ |
| Hepsi dikey P-L-C-S-X | Tüm alanlar tek sütunda alt alta | |
| 2x3 grid | P, L, C üst / S, X, Toplam alt | |

**User's choice:** P+X üst, L, C, S alt

---

| Option | Description | Selected |
|--------|-------------|----------|
| Sayaç üst, butonlar alt | Büyük sayaç gösterimi üstte + progress bar, kontrol butonları altta | ✓ |
| Butonlar üst, sayaç alt | Kontrol butonları üstte, sayaç altta | |
| Tek alan karışık | Butonlar ve sayaç aynı bölümde | |

**User's choice:** Sayaç üst, butonlar alt

---

| Option | Description | Selected |
|--------|-------------|----------|
| Evet, yatay bar | Gradient doluluk oranı gösteren bar | ✓ |
| Hayır, sadece sayı | Büyük puntoda "12 / 120" yeterli | |
| Dairesel (radial) | Yüzde daire içinde | |

**User's choice:** Evet, yatay bar (gradient)

---

## Parametre Girişi

| Option | Description | Selected |
|--------|-------------|----------|
| Tam sayı, geniş aralık | P, L, X hepsi tam sayı | |
| L ondalıklı | L ondalıklı (0.1mm), P ve X tam sayı | ✓ |
| Sen belirle | Claude seçsin | |

**User's choice:** L ondalıklı (0.1mm hassasiyet)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Aynı register'a yaz | write_cutting_speed / write_descent_speed kullanılır | ✓ |
| Sadece oku | Salt okunur, kontrol panelinde değiştirilir | |
| Bağımsız register | Otomatik kesim için ayrı register'lar | |

**User's choice:** Aynı register'a yaz (her iki sayfadan yazılabilir)

---

| Option | Description | Selected |
|--------|-------------|----------|
| NumpadDialog'a "." ekle | allow_decimal=True parametresi | ✓ |
| Sadece tam sayı mm | 1mm hassasiyet yeterli | |
| Sen belirle | Claude seçsin | |

**User's choice:** NumpadDialog'a allow_decimal parametresi eklenir

---

| Option | Description | Selected |
|--------|-------------|----------|
| P ve X arasında/altında | "Toplam: 120 adet" P-X altında, anlık güncellenir | ✓ |
| Sağ sütun sayaç üstünde | Hedef bilgisi sayaç bölümünde | |
| Gösterilmesin | Operatör hesaplasın | |

**User's choice:** P ve X altında, anlık güncellenir

---

## Kontrol & Sayaç

| Option | Description | Selected |
|--------|-------------|----------|
| Buton altında kırmızı uyarı | Kırmızı Türkçe hata mesajı, 3 saniye timeout | ✓ |
| Dialog/popup | Ayrı dialog kutusunda hata | |
| Boş alanları kırmızı çerçeve | Çerçeve renk değişimi, metin yok | |

**User's choice:** Buton altında kırmızı uyarı (3s timeout)

---

| Option | Description | Selected |
|--------|-------------|----------|
| 1.5s hold + progress | 1500ms basılı tutma, buton içi doluluk animasyonu | ✓ |
| 2s hold, sadece renk | 2000ms, renk değişimi | |
| Anında (hold yok) | Tek dokunma | |

**User's choice:** 1.5s hold + sol→sağ gradient progress animasyonu

---

| Option | Description | Selected |
|--------|-------------|----------|
| Parametreler açılır, sayaç sıfırlanır | Tam reset: alanlar aktif, sayaç sıfır, progress boş | ✓ |
| Sadece PLC komutu | GUI değişmez, D2056 polling ile güncellenir | |
| Onay dialogı ile | "Emin misiniz?" onayı | |

**User's choice:** Parametreler açılır, sayaç sıfırlanır

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yeşil renk + metin | Sayaç ve bar yeşile döner, "Tamamlandı!" mesajı | ✓ |
| Sadece renk değişimi | Yeşile döner, ek metin yok | |
| Flash/titreme | 3 kez yanıp söner | |

**User's choice:** Yeşil renk + "Tamamlandı!" mesajı, parametreler tekrar aktif

---

| Option | Description | Selected |
|--------|-------------|----------|
| Devre dışı + görsel | START gri/soluk, metin "DEVAM EDİYOR..." | ✓ |
| Gizle | START görünmez olur | |
| Aktif bırak | Her zaman tıklanabilir | |

**User's choice:** Devre dışı, metin "DEVAM EDİYOR..."

---

## ML Modu

| Option | Description | Selected |
|--------|-------------|----------|
| Checkbox | Tek açık/kapalı checkbox | |
| Toggle switch | iOS tarzı sürgü | |
| Manual/AI buton çifti | Kontrol panelindeki gibi iki buton | ✓ |

**User's choice:** Manual/AI buton çifti (kontrol paneli pattern'i)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Kapalı (Manual) | Sayfa açılışında her zaman Manual | |
| Kontrol paneli ile senkron | Mevcut mod okunarak butonlar güncellenir | ✓ |
| Son kullanılan | Önceki durumu hatırlar | |

**User's choice:** Kontrol paneli ile senkron (açılışta mevcut mod okunur)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Her kesim başlangıcında | D2056 değiştiğinde ML state reset | ✓ |
| START basıldığında | Tüm seri için bir kez reset | |
| Sen belirle | Claude seçsin | |

**User's choice:** Her kesim başlangıcında (D2056 değişim algılama)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Evet, iki yönlü senkron | Aynı control_manager, her iki sayfadan geçerli | ✓ |
| Bağımsız | Her sayfa kendi mod durumunu tutar | |

**User's choice:** İki yönlü senkron (aynı control_manager.set_mode())

---

## Claude's Discretion

- Sayfa widget sınıf yapısı ve iç metod organizasyonu
- Frame boyutları ve koordinatları
- Gradient renkleri ve font boyutları
- Hata mesajı timeout mekanizması
- RESET progress animasyonu implementasyonu
- D2056 değişim algılama mekanizması

## Deferred Ideas

None — discussion stayed within phase scope
