import cv2
import time
import os
import threading
from queue import Queue

# Kamera Ayarları
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1200
FPS = 50
NUM_THREADS = 8

# FPS için değişkenler
fps = 0
prev_time = time.time()
fps_update_interval = 1.0  # FPS'i her 1 saniyede bir güncelle

# Kamera bağlantısı
cap = cv2.VideoCapture(2)  # 0 for internal camera, 1 for external camera

if not cap.isOpened():
    print("Kamera açılamadı! Lütfen bağlantıyı kontrol edin.")
    exit()

# Kamera çözünürlüğü ve FPS ayarla
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer boyutunu küçült
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)  # Auto exposure (3: ON, 1: OFF)

# Windows'ta v4l2 çalışmadığı için bu kısmı atlıyoruz
if os.name != 'nt':  # Eğer Windows değilse
    try:
        import subprocess
        # Kamera ayarlarını varsayılan değerlere getir
        subprocess.run(['v4l2-ctl', '-d', '/dev/video1', 
                        '-c', 'brightness=0',      # default=0, range=-64 to 64
                        '-c', 'contrast=10',       # default=10, range=0 to 100
                        '-c', 'saturation=10',     # default=10, range=0 to 100
                        '-c', 'gain=100',          # default=100, range=100 to 1066
                        '-c', 'white_balance_automatic=1',  # default=1 (on)
                        '-c', 'auto_exposure=0'])  # 0=Auto Mode
        print("Kamera parametreleri varsayılan değerlere ayarlandı")
    except Exception as e:
        print(f"Kamera parametre ayarları yapılamadı: {e}")

# Ayarların uygulanması için kısa bir bekleme
time.sleep(1)

# Test frame'i al
for _ in range(5):  # İlk 5 frame'i at
    ret, _ = cap.read()
    if not ret:
        print("Test frame alınamadı")
        time.sleep(0.1)

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
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 90]  # JPEG kalite ayarı yüzde 90
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

        # FPS hesapla
        current_time = time.time()
        if current_time - prev_time >= fps_update_interval:
            fps = 1.0 / (current_time - prev_time)
            prev_time = current_time

        # FPS'i ekrana yaz
        fps_text = f"FPS: {fps:.1f}"
        # cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Kayıt yapılıyorsa frameleri kuyruğa ekle
        if is_recording and output_dir is not None:
            frame_count += 1
            frame_queue.put((frame_count, frame, output_dir))

            # Her 100 karede bir log bas
            if frame_count % 100 == 0:
                elapsed_time = time.time() - start_time
                print(f"Toplam Kare: {frame_count}, Süre: {elapsed_time:.2f} saniye")

        # Kareyi göster (pencereli mod - maksimize)
        cv2.namedWindow("Arducam UVC Kamera", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Arducam UVC Kamera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
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