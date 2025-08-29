import cv2
import numpy as np
import os
import re

# ---- Sabit çizgi konumları ----
TOP_LINE_Y = 88    # Üst kırmızı çizgi
BOTTOM_LINE_Y = 154    # Alt kırmızı çizgi (sabit)

# Ardışık frameler arası izin verilen max yüzde değişimi (ör. 0.5 => %0.5)
MAX_STEP_PERCENT = 0.5

def natural_key(s: str):
    """Dosya adlarını doğal sırada sıralamak için (1,2,10)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r'\d+|\D+', s)]

def wear_calculation():
    # Öncelikli giriş klasörleri (sırayla kontrol edilir)
    candidate_dirs = [
        "ldc_project/ldc_project/rsults/fused/Odakli",   # Odaklı orijinal kopyalar
        "ldc_project/ldc_project/rsults/fused",         # Fused/avg çıktıları
        "input-images"                                  # Son çare: ham giriş görüntüleri
    ]

    input_dir = None
    for d in candidate_dirs:
        if os.path.isdir(d) and any(fn.lower().endswith((".jpg", ".jpeg", ".png")) for fn in os.listdir(d)):
            input_dir = d
            break

    if input_dir is None:
        print("Hata: İşlenecek görüntü bulunamadı. input-images veya LDC çıktıları boş.")
        return

    wear_values = []
    prev_percent = None  # adım sınırlayıcı için

    # Dosyaları frame sırasına göre sırala
    files = [f for f in os.listdir(input_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    files.sort(key=natural_key)

    # Klasördeki tüm görüntüleri işle
    for filename in files:
        image_path = os.path.join(input_dir, filename)
        image = cv2.imread(image_path)
        if image is None:
            print(f"Hata: {filename} görüntüsü okunamadı")
            continue

        image_height, image_width = image.shape[:2]

        # (İstersen değiştir) Varsayılan YOLO kutu normalleştirilmiş değerleri
        x_center_n, y_center_n = 0.500000, 0.530692
        width_n, height_n = 0.736888, 0.489510

        # Piksel koordinatlarına çevir
        x_center = int(x_center_n * image_width)
        y_center = int(y_center_n * image_height)
        box_w   = int(width_n  * image_width)
        box_h   = int(height_n * image_height)

        x1 = int(x_center - box_w / 2)
        x2 = int(x_center + box_w / 2)

        # ROI'yi sabit çizgilere göre tanımla
        y1 = TOP_LINE_Y
        y2 = BOTTOM_LINE_Y

        # Koordinat sınırlarını güvenli hale getir
        x1 = max(0, min(x1, image_width - 1))
        x2 = max(0, min(x2, image_width))
        y1 = max(0, min(y1, image_height - 1))
        y2 = max(0, min(y2, image_height))

        if y2 <= y1 or x2 <= x1:
            print(f"Uyarı: ROI geçersiz atlandı: {filename}")
            continue

        # Bölgeyi kırp
        roi = image[y1:y2, x1:x2]

        # Grayscale + basit threshold ile tepe adaylarını çıkar (ORİJİNAL)
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, binary_roi = cv2.threshold(gray_roi, 128, 255, cv2.THRESH_BINARY_INV)

        # Konturları bul (ORİJİNAL)
        contours, _ = cv2.findContours(binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print(f"Uyarı: Kontur bulunamadı: {filename}")
            continue

        # --- ROBUST TEPE (tek piksel min yerine) ---
        # Tüm y'leri topla ve en küçük %10'un (min 5, max 50) ortalamasını al
        ys = [pt[0][1] for c in contours for pt in c]
        if len(ys) < 5:
            print(f"Uyarı: Yetersiz tepe örneği: {filename}")
            continue
        ys = np.array(ys, dtype=np.int32)
        k = max(5, int(0.10 * ys.size))
        k = min(k, 50)  # aşırı genişleme olmasın
        smallest = np.partition(ys, k)[:k]
        min_y = int(np.mean(smallest))

        # Mavi tepe noktalarını işaretlemek için (ORİJİNAL görsellik)
        thresh = min_y + 10
        for c in contours:
            for pt in c:
                xx, yy = pt[0]
                if yy < thresh:
                    cv2.circle(image, (xx + x1, yy + y1), 3, (255, 0, 0), -1)

        # Aşınmış tepenin global y'si
        wear_y = int(min_y + y1)

        # --- Çizgileri çiz (SABİT) ---
        cv2.line(image, (0, TOP_LINE_Y),     (image_width, TOP_LINE_Y),     (0, 0, 255), 2)
        cv2.line(image, (0, BOTTOM_LINE_Y),  (image_width, BOTTOM_LINE_Y),  (0, 0, 255), 2)
        # (İstemezsen gösterme) Dinamik ölçüm çizgisi
        # cv2.line(image, (0, wear_y), (image_width, wear_y), (0, 0, 255), 3)

        # --- Aşınma yüzdesi: sabit bant [TOP_LINE_Y, BOTTOM_LINE_Y] ---
        band_h = max(1, BOTTOM_LINE_Y - TOP_LINE_Y)  # sıfıra bölme güvenliği
        percent_raw = ((wear_y - TOP_LINE_Y) / band_h) * 100.0
        percent_raw = float(np.clip(percent_raw, 0.0, 100.0))

        # --- ADIM SINIRLAYICI: ani sıçramayı engelle ---
        if prev_percent is None:
            asinma_yuzdesi = percent_raw
        else:
            delta = percent_raw - prev_percent
            if   delta >  MAX_STEP_PERCENT: asinma_yuzdesi = prev_percent + MAX_STEP_PERCENT
            elif delta < -MAX_STEP_PERCENT: asinma_yuzdesi = prev_percent - MAX_STEP_PERCENT
            else:                           asinma_yuzdesi = percent_raw
        prev_percent = asinma_yuzdesi

        # Yüzde bilgisini yaz
        text = f"Asinma : {asinma_yuzdesi:.2f}%"
        cv2.putText(image, text, (image_width - 300, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Sonucu kaydet
        os.makedirs("results", exist_ok=True)
        output_path = os.path.join("results", f"wear_{filename}")
        cv2.imwrite(output_path, image)

        wear_values.append(asinma_yuzdesi)
        print(f"{filename}: Aşınma yüzdesi = {asinma_yuzdesi:.2f}% (raw={percent_raw:.2f}%)")

    if wear_values:
        ortalama = sum(wear_values) / len(wear_values)
        print(f"Ortalama aşınma yüzdesi: {ortalama:.2f}% ({len(wear_values)} görüntü)")
    else:
        print("Uyarı: Aşınma hesaplanamadı, geçerli görüntü bulunamadı.")

if __name__ == "__main__":
    wear_calculation()
