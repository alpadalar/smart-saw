import cv2
import os
import time
import json
from ultralytics import RTDETR
import torch
import threading
from core.logger import logger

# Global değişkenler ve kilitler
_crack_model = None
_crack_model_lock = threading.Lock()
_crack_model_loaded = False


def _load_crack_model():
    """RT-DETR crack modelini yükler (lazy-load)."""
    global _crack_model, _crack_model_loaded
    with _crack_model_lock:
        if not _crack_model_loaded:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            _crack_model = RTDETR(r"./catlak-best.pt")
            _crack_model.to(device)
            _crack_model_loaded = True
            logger.info(f"Crack modeli yüklendi - Kullanılan cihaz: {device}")
    return _crack_model


def detect_crack_objects():
    """
    En son kayıt klasöründeki frame'lerde çatlak (crack) tespiti yapar.
    - Tespit edilen çatlak bulunan kareler, ilgili kayıt klasöründeki 'detected' klasörüne kaydedilir.
    - Kayıt klasöründeki detection_stats.json dosyasına 'total_crack' değeri eklenir/güncellenir.
    """
    model = _load_crack_model()

    base_dir = os.path.join(os.getcwd(), "recordings")

    if not os.path.exists(base_dir):
        logger.error(f"Hata: {base_dir} klasörü bulunamadı!")
        return

    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    if not folders:
        logger.warning("İşlenecek kayıt bulunamadı!")
        return

    latest_folder = max(folders)
    input_dir = os.path.join(base_dir, latest_folder)
    output_dir = os.path.join(input_dir, "detected-crack")

    logger.info(f"Son kayıt klasörü üzerinde CRACK tespiti başlatılıyor: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    frames = sorted([f for f in os.listdir(input_dir) if f.startswith("frame_") and f.endswith(".jpg")])

    if not frames:
        logger.warning("Klasörde frame bulunamadı!")
        return

    logger.info(f"Toplam {len(frames)} kare incelenecek (crack tespiti)...")

    total_crack = 0

    for i, frame_name in enumerate(frames):
        frame_path = os.path.join(input_dir, frame_name)
        frame = cv2.imread(frame_path)

        if frame is None:
            logger.error(f"Hata: {frame_name} okunamadı!")
            continue

        with _crack_model_lock:
            results = model.predict(source=frame, device=model.device, conf=0.5, imgsz=960, verbose=False)

        crack_count_in_frame = 0

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Varsayım: modelde sınıf 0 = crack
                class_id = int(box.cls[0].item())
                if class_id == 0:
                    crack_count_in_frame += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0].item()
                    label = f"crack ({conf:.2f})"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if crack_count_in_frame > 0:
            total_crack += crack_count_in_frame
            base_name = frame_name.split('.')[0]
            output_name = f"{base_name}_crack{crack_count_in_frame}.jpg"
            output_path = os.path.join(output_dir, output_name)
            cv2.imwrite(output_path, frame)

        if (i + 1) % 100 == 0:
            logger.info(f"İşlenen kare: {i + 1}/{len(frames)}")

    # detection_stats.json güncelle
    stats_file = os.path.join(input_dir, "detection_stats.json")
    existing_stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                existing_stats = json.load(f)
        except Exception:
            existing_stats = {}

    existing_stats["total_crack"] = total_crack
    existing_stats["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    existing_stats["total_frames"] = len(frames)

    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(existing_stats, f, indent=4, ensure_ascii=False)

    logger.info("CRACK tespiti tamamlandı!")
    logger.info(f"Crack içeren kareler {output_dir} klasöründe kaydedildi.")
    logger.info(f"Toplam Crack Sayısı: {total_crack}")
    logger.info(f"İstatistikler {stats_file} dosyasına kaydedildi.")


if __name__ == "__main__":
    detect_crack_objects() 