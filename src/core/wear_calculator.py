import os
import csv
import threading
import time
from typing import Optional, Dict, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WearCalculator:
    """
    Real-time wear percentage calculator that reads from CSV files
    and calculates running averages for each recording session.
    """
    
    def __init__(self, recordings_root: str, update_callback: Optional[Callable[[float], None]] = None):
        self.recordings_root = recordings_root
        self.update_callback = update_callback
        self._stop_event = threading.Event()
        self._watcher_thread: Optional[threading.Thread] = None
        self._current_averages: Dict[str, float] = {}  # recording_dir -> average
        self._current_counts: Dict[str, int] = {}      # recording_dir -> count
        self._lock = threading.Lock()
        self._last_processed_files = set()
        
    def start(self):
        """Start the wear calculator watcher thread."""
        self._stop_event.clear()
        self._watcher_thread = threading.Thread(target=self._watch_csv_files, daemon=True)
        self._watcher_thread.start()
        logger.info("Wear calculator başlatıldı")
        
    def stop(self):
        """Stop the wear calculator."""
        self._stop_event.set()
        if self._watcher_thread:
            self._watcher_thread.join(timeout=1.0)
        logger.info("Wear calculator durduruldu")
        
    def get_current_average(self, recording_dir: Optional[str] = None) -> float:
        """Get the current average wear percentage for the specified recording or overall."""
        with self._lock:
            if recording_dir:
                return self._current_averages.get(recording_dir, 0.0)
            else:
                # Return overall average across all recordings
                if not self._current_averages:
                    return 0.0
                total_sum = sum(self._current_averages.values())
                total_count = len(self._current_averages)
                return total_sum / total_count if total_count > 0 else 0.0
                
    def get_latest_recording_average(self) -> float:
        """Get the average wear percentage for the most recent recording."""
        with self._lock:
            if not self._current_averages:
                return 0.0
            # Find the most recent recording directory
            latest_dir = max(self._current_averages.keys(), key=lambda x: os.path.getctime(x))
            return self._current_averages.get(latest_dir, 0.0)
    
    def _watch_csv_files(self):
        """Watch for new CSV files and update averages in real-time."""
        logger.info(f"Wear calculator CSV izleme başladı: {self.recordings_root}")
        while not self._stop_event.is_set():
            try:
                if not os.path.isdir(self.recordings_root):
                    logger.warning(f"Recordings klasörü bulunamadı: {self.recordings_root}")
                    time.sleep(1.0)
                    continue
                    
                # Scan all recording directories
                recording_dirs = [f for f in os.listdir(self.recordings_root) 
                                if os.path.isdir(os.path.join(self.recordings_root, f))]
                logger.debug(f"Bulunan kayıt klasörleri: {recording_dirs}")
                
                for recording_name in recording_dirs:
                    recording_dir = os.path.join(self.recordings_root, recording_name)
                    csv_path = os.path.join(recording_dir, "wear.csv")
                    
                    if not os.path.exists(csv_path):
                        logger.debug(f"CSV dosyası bulunamadı: {csv_path}")
                        continue
                        
                    # Check if we've already processed this file
                    file_key = f"{csv_path}_{os.path.getmtime(csv_path)}"
                    if file_key in self._last_processed_files:
                        continue
                        
                    logger.info(f"Yeni CSV dosyası işleniyor: {csv_path}")
                    # Process the CSV file
                    self._process_csv_file(csv_path, recording_dir)
                    self._last_processed_files.add(file_key)
                    
                    # Keep only recent file keys to prevent memory growth
                    if len(self._last_processed_files) > 100:
                        self._last_processed_files.clear()
                        
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Wear calculator hatası: {e}")
                time.sleep(1.0)
    
    def _process_csv_file(self, csv_path: str, recording_dir: str):
        """Process a single CSV file and update the running average."""
        try:
            logger.info(f"CSV dosyası açılıyor: {csv_path}")
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                wear_values = []
                
                logger.info(f"CSV sütunları: {reader.fieldnames}")
                
                for row in reader:
                    try:
                        wear_percent = float(row.get('wear_percent', 0))
                        wear_values.append(wear_percent)
                        logger.debug(f"Wear değeri okundu: {wear_percent}")
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Satır işlenemedi: {row}, hata: {e}")
                        continue
                
                logger.info(f"Toplam {len(wear_values)} wear değeri okundu")
                
                if wear_values:
                    # Calculate new average
                    new_average = sum(wear_values) / len(wear_values)
                    new_count = len(wear_values)
                    
                    logger.info(f"Ortalama hesaplandı: {new_average:.2f}% ({new_count} değer)")
                    
                    with self._lock:
                        self._current_averages[recording_dir] = new_average
                        self._current_counts[recording_dir] = new_count
                    
                    # Call callback with latest average
                    if self.update_callback:
                        try:
                            latest_avg = self.get_latest_recording_average()
                            logger.info(f"Callback çağrılıyor: {latest_avg:.2f}%")
                            self.update_callback(latest_avg)
                        except Exception as e:
                            logger.error(f"Callback hatası: {e}")
                    
                    logger.info(f"Wear güncellendi: {recording_dir} -> {new_average:.2f}% ({new_count} değer)")
                else:
                    logger.warning(f"Hiç wear değeri bulunamadı: {csv_path}")
                    
        except Exception as e:
            logger.error(f"CSV işleme hatası {csv_path}: {e}")
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        with self._lock:
            return {
                "active_recordings": len(self._current_averages),
                "latest_average": self.get_latest_recording_average(),
                "overall_average": self.get_current_average(),
                "recording_averages": dict(self._current_averages)
            } 