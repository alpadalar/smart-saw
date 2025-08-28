import cv2  
import os   
import time
import json 
from ultralytics import RTDETR  
import torch 
import threading
from core.logger import logger 

# Global değişkenler ve kilitler
_model = None
_model_lock = threading.Lock()
_model_loaded = False

def _load_model():
    global _model, _model_loaded
    with _model_lock:
        if not _model_loaded:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            _model = RTDETR(r"./best.pt")
            _model.to(device)
            _model_loaded = True
            logger.info(f"Model yüklendi - Kullanılan cihaz: {device}")
    return _model

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
        class_counts = {0: 0, 1: 0}  # 0: broken, 1: tooth
        # Tespit edilen nesneler için bounding box çiz
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0].item()
                class_id = int(box.cls[0].item())
                label = f"{class_id:.2f} ({conf:.2f})"
                # Sınıfa göre istatistikleri güncelle
                if class_id == 1:  # tooth sınıfı
                    total_tooth += 1
                    class_counts[1] += 1
                elif class_id == 0:  # broken sınıfı
                    total_broken += 1
                    class_counts[0] += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        # Dosya adı oluştur
        base_name = frame_name.split('.')[0]
        suffix = ""
        if class_counts[0] > 0:
            suffix += f"_broken{class_counts[0]}"
        if class_counts[1] > 0:
            suffix += f"_tooth{class_counts[1]}"
        output_name = f"{base_name}{suffix}.jpg"
        output_path = os.path.join(output_dir, output_name)
        cv2.imwrite(output_path, frame)
        
        if (i + 1) % 100 == 0:
            logger.info(f"İşlenen kare: {i + 1}/{len(frames)}")
    
    # Kırık oranını hesapla
    broken_ratio = total_broken / total_tooth if total_tooth > 0 else 0
    
    # İstatistikleri JSON dosyasına kaydet (mevcut alanları koru)
    stats_file = os.path.join(input_dir, "detection_stats.json")
    existing_stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                existing_stats = json.load(f)
        except Exception:
            existing_stats = {}

    # Bu tespitin ürettiği alanları güncelle
    existing_stats["total_tooth"] = total_tooth
    existing_stats["total_broken"] = total_broken
    existing_stats["broken_ratio"] = broken_ratio
    existing_stats["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    existing_stats["total_frames"] = len(frames)

    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(existing_stats, f, indent=4, ensure_ascii=False)
    
    # İstatistikleri loglara yaz
    logger.info("Nesne tespiti tamamlandi!")
    logger.info(f"İşlenmiş kareler {output_dir} klasöründe kaydedildi.")
    logger.info("Tespit İstatistikleri:")
    logger.info(f"Toplam Diş Sayisi: {total_tooth}")
    logger.info(f"Toplam Kirik Sayisi: {total_broken}")
    logger.info(f"Kirik Orani: {broken_ratio:.2%}")
    logger.info(f"İstatistikler {stats_file} dosyasina kaydedildi.")

# Eğer bu dosya doğrudan çalıştırılırsa fonksiyonu çağır
if __name__ == "__main__":
    detect_broken_objects()
