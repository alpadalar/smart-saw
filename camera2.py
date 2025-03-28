import cv2
import time
import os
import threading
from queue import Queue
from ultralytics import RTDETR
import torch

# Kamera Ayarları
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1200
FPS = 50
NUM_THREADS = 8

# FPS ve işleme süresi için değişkenler
fps = 0
process_time = 0
prev_time = time.time()
fps_update_interval = 1.0  # FPS'i her 1 saniyede bir güncelle

# GPU kontrolü
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Kullanılan cihaz: {device}")

# Modeli yükleme
model = RTDETR(r"./best.pt")
model.to(device)  # Modeli GPU'ya taşı

# Kamera bağlantısı
cap = cv2.VideoCapture(0)  # 0 for internal camera, 1 for external camera

if not cap.isOpened():
    print("Kamera açılamadı! Lütfen bağlantıyı kontrol edin.")
    exit()

# Kamera çözünürlüğü ve FPS ayarla
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)  # Auto exposure (3: ON, 1: OFF)

# Kamera ayarlarının uygulanıp uygulanmadığını kontrol et
actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
actual_fps = int(cap.get(cv2.CAP_PROP_FPS))

print("Kamera ayarları (gerçek değerler):")
print(f"Çözünürlük: {actual_width}x{actual_height}, FPS: {actual_fps}")

# Kayıt ayarları
base_output_dir = os.path.join(os.getcwd(), "frames")
output_dir = None
is_recording = False
frame_queue = Queue()
frame_count = 0
start_time = None


# Frame kaydetme fonksiyonu
def save_frames():
    while True:
        frame_data = frame_queue.get()
        if frame_data is None:
            break

        frame_count, frame, output_dir = frame_data
        frame_filename = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 92]  # JPEG kalite ayarı yüzde 92
        cv2.imwrite(frame_filename, frame, encode_params)
        frame_queue.task_done()


# Threadleri başlat
threads = []
for _ in range(NUM_THREADS):
    t = threading.Thread(target=save_frames, daemon=True)
    t.start()
    threads.append(t)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kare okunamıyor, tekrar deneniyor...")
            time.sleep(1)
            continue

        # İşleme süresini ölçmeye başla
        process_start = time.time()

        # Model ile tahmin yap
        results = model.predict(source=frame, device=device, conf=0.5, imgsz=960)

        # İşleme süresini hesapla
        process_time = (time.time() - process_start) * 1000  # milisaniye cinsinden

        # FPS hesapla
        current_time = time.time()
        if current_time - prev_time >= fps_update_interval:
            fps = 1.0 / (current_time - prev_time)
            prev_time = current_time

        # Bounding box çizimi
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0].item()
                label = f"{box.cls[0].item():.2f} ({conf:.2f})"

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # FPS ve işleme süresini ekrana yaz
        fps_text = f"FPS: {fps:.1f}"
        time_text = f"Process: {process_time:.1f}ms"
        cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, time_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Kayıt yapılıyorsa frameleri kuyruğa ekle
        if is_recording and output_dir is not None:
            frame_count += 1
            frame_queue.put((frame_count, frame, output_dir))

            # Her 100 karede bir log bas
            if frame_count % 100 == 0:
                elapsed_time = time.time() - start_time
                print(f"Toplam Kare: {frame_count}, Süre: {elapsed_time:.2f} saniye")

        # Kareyi göster (tam ekran)
        cv2.namedWindow("Arducam UVC Kamera", cv2.WINDOW_FULLSCREEN)
        cv2.imshow("Arducam UVC Kamera", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):  # Çıkış
            break
        elif key == ord('r'):  # Kayıt başlat/durdur
            if not is_recording:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_dir = os.path.join(base_output_dir, timestamp)
                os.makedirs(output_dir, exist_ok=True)
                is_recording = True
                frame_count = 0
                start_time = time.time()
                print(f"Kayıt başladı: {output_dir}")
            else:
                is_recording = False
                print("Kayıt durduruldu.")

except KeyboardInterrupt:
    print("Program sonlandırıldı.")

finally:
    # Kuyruğu boşalt
    frame_queue.join()
    for _ in threads:
        frame_queue.put(None)
    for t in threads:
        t.join()

    # Kamera kapat
    cap.release()
    cv2.destroyAllWindows()
    print("Kamera kapatıldı.")