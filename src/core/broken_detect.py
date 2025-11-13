import cv2  
import json
import os   
import re
import threading
import time

import torch
from ultralytics import RTDETR, YOLO

from core.logger import logger
from core.constants import BROKEN_DETECTION_MODEL_PATH 

# Global değişkenler ve kilitler
_model = None
_model_lock = threading.Lock()
_model_loaded = False

_stats_lock = threading.Lock()  # JSON dosyası için thread-safe lock


def _load_model():
    global _model, _model_loaded
    with _model_lock:
        if not _model_loaded:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            # Config'den model path al
            # Önce RTDETR ile yüklemeyi dene, başarısız olursa YOLO ile dene
            try:
                _model = RTDETR(BROKEN_DETECTION_MODEL_PATH)
                _model.to(device)
                _model_loaded = True
                logger.info(f"Broken detection model (RTDETR) yüklendi: {BROKEN_DETECTION_MODEL_PATH} - Cihaz: {device}")
            except Exception as e:
                logger.warning(f"RTDETR ile model yüklenemedi, YOLO deneniyor: {e}")
                try:
                    _model = YOLO(BROKEN_DETECTION_MODEL_PATH)
                    _model.to(device)
                    _model_loaded = True
                    logger.info(f"Broken detection model (YOLO) yüklendi: {BROKEN_DETECTION_MODEL_PATH} - Cihaz: {device}")
                except Exception as e2:
                    logger.error(f"Model yüklenemedi (RTDETR ve YOLO denendi): {e2}")
                    raise RuntimeError(f"Model yüklenemedi: {e2}")
    return _model


def _update_stats_file(stats_file: str, new_stats: dict):
    """Thread-safe olarak detection_stats.json dosyasını günceller"""
    with _stats_lock:
        existing_stats = {}
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    existing_stats = json.load(f)
            except Exception as e:
                logger.error(f"Stats dosyası okuma hatası: {e}")
                existing_stats = {}
        
        # Mevcut değerleri koru, yeni değerleri ekle/güncelle
        existing_stats.update(new_stats)
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(existing_stats, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Stats dosyası yazma hatası: {e}")

def _calculate_stats_from_detected_files(detected_dir: str) -> dict:
    """Detection dosyalarının isimlerinden istatistikleri hesaplar"""
    total_tooth = 0
    total_broken = 0
    
    if not os.path.exists(detected_dir):
        return {"total_tooth": 0, "total_broken": 0}
    
    # Detection dosyalarını tara
    for filename in os.listdir(detected_dir):
        if filename.endswith('.jpg'):
            # Dosya isminden broken ve tooth sayılarını çıkar
            # Örnek: frame_000001_broken4_tooth1.jpg
            broken_match = re.search(r'_broken(\d+)', filename)
            tooth_match = re.search(r'_tooth(\d+)', filename)
            
            if broken_match:
                total_broken += int(broken_match.group(1))
            if tooth_match:
                total_tooth += int(tooth_match.group(1))
    
    broken_ratio = total_broken / total_tooth if total_tooth > 0 else 0
    
    return {
        "total_tooth": total_tooth,
        "total_broken": total_broken,
        "broken_ratio": broken_ratio
    }

def detect_broken_objects():
    model = _load_model()
    
    # Ana klasör yolunu 'recordings' olarak değiştir
    base_dir = os.path.join(os.getcwd(), "recordings")

    
    # En son oluşturulan klasörü bul
    if not os.path.exists(base_dir):
        logger.error(f"Hata: {base_dir} klasörü bulunamadı!")
        return
    
    # Klasörleri al ve sırala
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    if not folders:
        logger.warning("İşlenecek kayıt bulunamadı!")
        return
    
    # En son oluşturulan klasörü bul
    latest_folder = max(folders)
    input_dir = os.path.join(base_dir, latest_folder)
    output_dir = os.path.join(input_dir, "detected")
    
    logger.info(f"Son kayıt klasörü üzerinde nesne tespiti başlatılıyor: {input_dir}")
    
    # Çıkış klasörünü oluştur
    os.makedirs(output_dir, exist_ok=True)
    
    # Klasördeki tüm frame'leri al ve sırala
    frames = sorted([f for f in os.listdir(input_dir) if f.startswith("frame_") and f.endswith(".jpg")])
    
    if not frames:
        logger.warning("Klasörde frame bulunamadı!")
        return
    
    logger.info(f"Toplam {len(frames)} kare işlenecek...")
    
    # İstatistik değişkenleri
    total_tooth = 0
    total_broken = 0

    stats_file = os.path.join(input_dir, "detection_stats.json")

    
    # Her frame için nesne tespiti yap
    for i, frame_name in enumerate(frames):
        frame_path = os.path.join(input_dir, frame_name)
        frame = cv2.imread(frame_path)
        
        if frame is None:
            logger.error(f"Hata: {frame_name} okunamadı!")
            continue
        
        # Model ile tahmin yap
        with _model_lock:

            results = model.predict(source=frame, device=model.device, conf=0.5, imgsz=960, verbose=False)
        
        # Sınıf sayacı
        class_counts = {0: 0, 1: 0}  # 0: tooth, 1: broken

        # Tespit edilen nesneler için bounding box çiz
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0].item()
                class_id = int(box.cls[0].item())
                label = f"{class_id:.2f} ({conf:.2f})"

                # Sınıfa göre istatistikleri güncelle
                if class_id == 0:  # tooth sınıfı
                    total_tooth += 1
                    class_counts[0] += 1
                elif class_id == 1:  # broken sınıfı
                    total_broken += 1
                    class_counts[1] += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Dosya adı oluştur
        base_name = frame_name.split('.')[0]
        suffix = ""
        if class_counts[0] > 0:
            suffix += f"_tooth{class_counts[0]}"
        if class_counts[1] > 0:
            suffix += f"_broken{class_counts[1]}"
        output_name = f"{base_name}{suffix}.jpg"
        output_path = os.path.join(output_dir, output_name)
        cv2.imwrite(output_path, frame)
        
        # Real-time stats güncelleme (her frame işlendikten sonra)
        broken_ratio = total_broken / total_tooth if total_tooth > 0 else 0
        new_stats = {
            "total_tooth": total_tooth,
            "total_broken": total_broken,
            "broken_ratio": broken_ratio,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_frames": i + 1,
            "processed_frames": i + 1
        }
        _update_stats_file(stats_file, new_stats)
        
        if (i + 1) % 100 == 0:
            logger.info(f"İşlenen kare: {i + 1}/{len(frames)} - Tooth: {total_tooth}, Broken: {total_broken}, Oran: {broken_ratio:.2%}")
    
    # Final stats güncelleme
    broken_ratio = total_broken / total_tooth if total_tooth > 0 else 0
    final_stats = {
        "total_tooth": total_tooth,
        "total_broken": total_broken,
        "broken_ratio": broken_ratio,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),

        "total_frames": len(frames),
        "processed_frames": len(frames),
        "status": "completed"
    }
    _update_stats_file(stats_file, final_stats)

    
    # İstatistikleri loglara yaz
    logger.info("Nesne tespiti tamamlandi!")
    logger.info(f"İşlenmiş kareler {output_dir} klasöründe kaydedildi.")
    logger.info("Tespit İstatistikleri:")
    logger.info(f"Toplam Diş Sayisi: {total_tooth}")
    logger.info(f"Toplam Kirik Sayisi: {total_broken}")
    logger.info(f"Kirik Orani: {broken_ratio:.2%}")
    logger.info(f"İstatistikler {stats_file} dosyasina kaydedildi.")

def update_stats_from_detected_files(recording_dir: str = None):
    """Detection dosyalarının isimlerinden istatistikleri hesaplar ve günceller"""
    if recording_dir is None:
        # En son recording klasörünü bul
        base_dir = os.path.join(os.getcwd(), "recordings")
        if not os.path.exists(base_dir):
            logger.error(f"Hata: {base_dir} klasörü bulunamadı!")
            return
        
        folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
        if not folders:
            logger.warning("İşlenecek kayıt bulunamadı!")
            return
        
        recording_dir = os.path.join(base_dir, max(folders))
    
    detected_dir = os.path.join(recording_dir, "detected")
    stats_file = os.path.join(recording_dir, "detection_stats.json")
    
    # Dosya isimlerinden istatistikleri hesapla
    stats = _calculate_stats_from_detected_files(detected_dir)
    
    # Timestamp ekle
    stats["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Thread-safe olarak güncelle
    _update_stats_file(stats_file, stats)
    
    logger.info(f"Detection dosyalarından hesaplanan istatistikler:")
    logger.info(f"Toplam Diş Sayisi: {stats['total_tooth']}")
    logger.info(f"Toplam Kirik Sayisi: {stats['total_broken']}")
    logger.info(f"Kirik Orani: {stats['broken_ratio']:.2%}")
    logger.info(f"İstatistikler {stats_file} dosyasina kaydedildi.")

# Eğer bu dosya doğrudan çalıştırılırsa fonksiyonu çağır
if __name__ == "__main__":
    detect_broken_objects()
