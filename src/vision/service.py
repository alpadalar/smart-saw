import os
import sys
import threading
import time
import queue
import csv
from datetime import datetime
from typing import Optional, Tuple

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Try to import torch lazily; service can run without GPU too
try:
    import torch
    TORCH_AVAILABLE = True
except Exception as e:
    TORCH_AVAILABLE = False
    logger.error(f"torch import edilemedi: {e}")


class VisionService:
    """
    Thread-safe vision service that mirrors real_ldc behavior but processes frames
    incrementally as they are saved into recordings/<recording>/.

    - Watches the recordings root for new recording folders and new frame files
    - Runs LDC model per-frame (using real_ldc code) and saves edge map with original size
    - Runs wear calculation over the LDC-processed frame and appends percentage to one CSV per recording
    - Starts processing immediately without waiting recording to finish
    - Only processes the most recent active recording folder
    """

    def __init__(self,
                 recordings_root: Optional[str] = None,
                 real_ldc_root: Optional[str] = None,
                 watchdog_interval_s: float = 0.2,
                 max_queue_size: int = 1024):
        self.recordings_root = recordings_root or os.path.join(os.getcwd(), "recordings")
        self.real_ldc_root = real_ldc_root or os.path.join(os.getcwd(), "real_ldc")
        self.watchdog_interval_s = watchdog_interval_s
        self._stop_event = threading.Event()
        self._watcher_thread: Optional[threading.Thread] = None
        self._ldc_thread: Optional[threading.Thread] = None
        self._wear_thread: Optional[threading.Thread] = None
        
        # Thread-safe state management
        self._lock = threading.Lock()
        self._current_recording_dir: Optional[str] = None  # Sadece aktif recording klasörü
        self._seen_files_per_recording = {}  # Her recording için ayrı seen files set'i
        self._ldc_queue: "queue.Queue[Tuple[str, str]]" = queue.Queue(maxsize=max_queue_size)  # (frame_path, recording_dir)
        self._wear_queue: "queue.Queue[Tuple[str, str, str]]" = queue.Queue(maxsize=max_queue_size)  # (ldc_image_path, csv_path, recording_dir)

        # Model / real_ldc components
        self._ldc_device = None
        self._ldc_model = None
        self._test_dataset_ctor = None
        self._save_image_fn = None

        # Stats
        self.stats = {
            "frames_seen": 0,
            "frames_enqueued": 0,
            "ldc_processed": 0,
            "wear_processed": 0,
            "current_recording": None,
        }

    # ------ Public API ------
    def start(self) -> None:
        os.makedirs(self.recordings_root, exist_ok=True)
        self._load_real_ldc_components()
        self._stop_event.clear()
        self._watcher_thread = threading.Thread(target=self._watch_recordings_loop, daemon=True)
        self._ldc_thread = threading.Thread(target=self._ldc_worker, daemon=True)
        self._wear_thread = threading.Thread(target=self._wear_worker, daemon=True)
        self._watcher_thread.start()
        self._ldc_thread.start()
        self._wear_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        for q in (self._ldc_queue, self._wear_queue):
            try:
                q.put_nowait((None, None) if q is self._ldc_queue else (None, None, None))
            except Exception:
                pass
        for t in (self._watcher_thread, self._ldc_thread, self._wear_thread):
            if t:
                t.join(timeout=1.0)

    def get_stats(self) -> dict:
        with self._lock:
            st = dict(self.stats)
            st["current_recording"] = self._current_recording_dir
            st["ldc_queue_size"] = self._ldc_queue.qsize()
            st["wear_queue_size"] = self._wear_queue.qsize()
            return st

    # ------ Internal: real_ldc adapters ------
    def _load_real_ldc_components(self) -> None:
        """Import real_ldc components and load model once."""
        # Make real_ldc importable
        if self.real_ldc_root not in sys.path:
            sys.path.insert(0, self.real_ldc_root)
        try:
            from modelB4 import LDC  # type: ignore
        except Exception as e:
            logger.error(f"real_ldc import hatası (modelB4): {e}")
            self._ldc_model = None
            return

        if not TORCH_AVAILABLE:
            logger.error("torch bulunamadı, LDC devre dışı")
            self._ldc_model = None
            return
        # Device
        self._ldc_device = torch.device('cpu' if torch.cuda.device_count() == 0 else 'cuda')
        logger.info(f"LDC device: {self._ldc_device}, cuda_count={torch.cuda.device_count()}")
        # Model
        self._ldc_model = LDC().to(self._ldc_device)
        # Checkpoint path inside real_ldc
        checkpoint_path = os.path.join(self.real_ldc_root, "checkpoints", "BIPED", "16", "16_model.pth")
        if os.path.isfile(checkpoint_path):
            try:
                state = torch.load(checkpoint_path, map_location=self._ldc_device)
                self._ldc_model.load_state_dict(state)
                logger.info(f"LDC checkpoint yüklendi: {checkpoint_path}")
            except Exception as e:
                logger.error(f"Checkpoint yüklenemedi: {e}")
        else:
            logger.error(f"Checkpoint bulunamadı: {checkpoint_path}")
        self._ldc_model.eval()

    # ------ Watcher ------
    def _watch_recordings_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                # Scan recording folders and find the most recent one
                current_recording = self._find_current_recording()
                
                with self._lock:
                    # Update current recording if changed
                    if current_recording != self._current_recording_dir:
                        if self._current_recording_dir is not None:
                            logger.info(f"Recording klasörü değişti: {self._current_recording_dir} -> {current_recording}")
                        self._current_recording_dir = current_recording
                        self.stats["current_recording"] = current_recording
                        
                        # Initialize seen files set for new recording
                        if current_recording and current_recording not in self._seen_files_per_recording:
                            self._seen_files_per_recording[current_recording] = set()
                
                # Process frames only in current recording
                if current_recording and os.path.isdir(current_recording):
                    self._process_recording_frames(current_recording)
                
                time.sleep(self.watchdog_interval_s)
            except Exception as e:
                logger.error(f"Watch recordings loop hatası: {e}")
                time.sleep(self.watchdog_interval_s)

    def _find_current_recording(self) -> Optional[str]:
        """En son oluşturulan recording klasörünü bulur"""
        try:
            if not os.path.isdir(self.recordings_root):
                return None
                
            folders = []
            for name in os.listdir(self.recordings_root):
                rec_dir = os.path.join(self.recordings_root, name)
                if os.path.isdir(rec_dir):
                    # Check if it's a valid timestamp format (YYYYMMDD-HHMMSS)
                    if len(name) == 15 and name[8] == '-':
                        try:
                            datetime.strptime(name, '%Y%m%d-%H%M%S')
                            folders.append(rec_dir)
                        except ValueError:
                            continue
            
            if not folders:
                return None
                
            # Return the most recent folder
            return max(folders)
        except Exception as e:
            logger.error(f"Current recording bulma hatası: {e}")
            return None

    def _process_recording_frames(self, recording_dir: str) -> None:
        """Belirli bir recording klasöründeki frame'leri işler"""
        try:
            with self._lock:
                seen_files = self._seen_files_per_recording.get(recording_dir, set())
            
            # Ensure CSV path exists
            csv_path = os.path.join(recording_dir, "wear.csv")
            
            # Process new frames
            for fname in os.listdir(recording_dir):
                if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                    
                fpath = os.path.join(recording_dir, fname)
                
                with self._lock:
                    if fpath in seen_files:
                        continue
                    seen_files.add(fpath)
                    self._seen_files_per_recording[recording_dir] = seen_files
                
                # Consider file stable when size stops changing briefly
                if not self._is_file_ready(fpath):
                    continue
                
                try:
                    self._ldc_queue.put_nowait((fpath, recording_dir))
                    with self._lock:
                        self.stats["frames_enqueued"] += 1
                except queue.Full:
                    pass
            
            with self._lock:
                self.stats["frames_seen"] = sum(len(files) for files in self._seen_files_per_recording.values())
                
        except Exception as e:
            logger.error(f"Recording frames işleme hatası ({recording_dir}): {e}")

    @staticmethod
    def _is_file_ready(path: str, wait_s: float = 0.05) -> bool:
        try:
            s1 = os.path.getsize(path)
            time.sleep(wait_s)
            s2 = os.path.getsize(path)
            return s1 == s2 and s1 > 0
        except Exception:
            return False

    # ------ LDC worker ------
    def _ldc_worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._ldc_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if not item or item[0] is None:
                break
            frame_path, rec_dir = item
            try:
                ldc_out = self._run_ldc_on_image(frame_path)
                if ldc_out is None:
                    continue
                ldc_image, save_path = ldc_out
                # Save processed image alongside recording (ldc subfolder)
                out_dir = os.path.join(rec_dir, "ldc")
                os.makedirs(out_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(frame_path))[0] + ".png"
                out_path = os.path.join(out_dir, base_name)
                cv2.imwrite(out_path, ldc_image)
                # Prepare CSV path for wear worker
                csv_path = os.path.join(rec_dir, "wear.csv")
                try:
                    self._wear_queue.put_nowait((out_path, csv_path, rec_dir))
                except queue.Full:
                    pass
                with self._lock:
                    self.stats["ldc_processed"] += 1
            except Exception:
                pass
            finally:
                self._ldc_queue.task_done()

    def _run_ldc_on_image(self, image_path: str) -> Optional[Tuple[np.ndarray, str]]:
        if self._ldc_model is None:
            logger.error("LDC modeli yüklenmedi; ham görüntü kaydedilmeyecek")
            return None
        orig = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if orig is None:
            return None
        h, w = orig.shape[:2]
        target_h, target_w = 512, 512
        resized = cv2.resize(orig, (target_w, target_h))
        img = resized.astype(np.float32)
        mean_bgr = np.array([103.939, 116.779, 123.68], dtype=np.float32)
        img -= mean_bgr
        img = img.transpose(2, 0, 1)
        tensor = torch.from_numpy(img).unsqueeze(0).to(self._ldc_device)
        with torch.no_grad():
            outputs = self._ldc_model(tensor)
            logger.info(f"LDC forward tamam: type={type(outputs)}")
            # Ensure list of maps [B,1,H,W]
            if isinstance(outputs, torch.Tensor):
                maps = [outputs]
            else:
                maps = list(outputs)
            # Apply sigmoid and to numpy uint8 per map
            preds_uint8 = []
            for idx, m in enumerate(maps):
                logger.info(f"map[{idx}] shape={tuple(m.shape)}")
                m = torch.sigmoid(m).cpu().detach().numpy()  # [B,1,H,W] or [B,H,W]
                m = np.squeeze(m)  # [H,W]
                m = (m - m.min()) / (m.max() - m.min() + 1e-8)
                m = (m * 255.0).astype(np.uint8)
                m = cv2.bitwise_not(m)  # invert as in real_ldc
                # Resize to original input image size (w,h)
                m = cv2.resize(m, (w, h))
                preds_uint8.append(m)
            # fused = last, average = mean of all
            fused = preds_uint8[-1]
            average = np.uint8(np.mean(np.stack(preds_uint8, axis=0), axis=0))
        # Use fused for sharper edges, then binarize like real_ldc
        edge_gray = fused
        # Invert -> threshold -> invert back to get black edges on white
        inv = cv2.bitwise_not(edge_gray)
        _, binary = cv2.threshold(inv, 180, 255, cv2.THRESH_BINARY)
        edge_gray = cv2.bitwise_not(binary)
        edge_bgr = cv2.cvtColor(edge_gray, cv2.COLOR_GRAY2BGR)
        return edge_bgr, image_path

    # ------ Wear worker ------
    def _wear_worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._wear_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if not item or item[0] is None:
                break
            ldc_image_path, csv_path, rec_dir = item
            try:
                percent, marked = self._compute_wear(ldc_image_path)
                if percent is not None:
                    # Append one row to CSV per frame
                    self._append_csv(csv_path, ldc_image_path, percent)
                    # Save marked visualization next to ldc output
                    vis_dir = os.path.join(rec_dir, "wear_vis")
                    os.makedirs(vis_dir, exist_ok=True)
                    vis_path = os.path.join(vis_dir, os.path.basename(ldc_image_path))
                    cv2.imwrite(vis_path, marked)
                    with self._lock:
                        self.stats["wear_processed"] += 1
            except Exception:
                pass
            finally:
                self._wear_queue.task_done()

    # Adapted from real_ldc/wear_calculation.py
    def _compute_wear(self, image_path: str) -> Tuple[Optional[float], Optional[np.ndarray]]:
        TOP_LINE_Y = 170
        BOTTOM_LINE_Y = 236
        image = cv2.imread(image_path)
        if image is None:
            return None, None
        image_height, image_width = image.shape[:2]
        x_center_n, y_center_n = 0.500000, 0.530692
        width_n, height_n = 0.736888, 0.489510
        x_center = int(x_center_n * image_width)
        y_center = int(y_center_n * image_height)
        box_w   = int(width_n  * image_width)
        box_h   = int(height_n * image_height)
        x1 = int(x_center - box_w / 2)
        x2 = int(x_center + box_w / 2)
        y1 = TOP_LINE_Y
        y2 = BOTTOM_LINE_Y
        x1 = max(0, min(x1, image_width - 1))
        x2 = max(0, min(x2, image_width))
        y1 = max(0, min(y1, image_height - 1))
        y2 = max(0, min(y2, image_height))
        if y2 <= y1 or x2 <= x1:
            return None, image
        roi = image[y1:y2, x1:x2]
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # Adaptive threshold choice: if edges-on-black (low mean), use THRESH_BINARY; else use INV
        mean_val = float(gray_roi.mean())
        if mean_val < 90:
            _, binary_roi = cv2.threshold(gray_roi, 180, 255, cv2.THRESH_BINARY)
        else:
            _, binary_roi = cv2.threshold(gray_roi, 128, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, image
        ys = [pt[0][1] for c in contours for pt in c]
        if len(ys) < 5:
            return None, image
        ys = np.array(ys, dtype=np.int32)
        k = max(5, int(0.10 * ys.size))
        k = min(k, 50)
        smallest = np.partition(ys, k)[:k]
        min_y = int(np.mean(smallest))
        thresh = min_y + 10
        for c in contours:
            for pt in c:
                xx, yy = pt[0]
                if yy < thresh:
                    cv2.circle(image, (xx + x1, yy + y1), 3, (255, 0, 0), -1)
        wear_y = int(min_y + y1)
        cv2.line(image, (0, TOP_LINE_Y),     (image_width, TOP_LINE_Y),     (0, 0, 255), 2)
        cv2.line(image, (0, BOTTOM_LINE_Y),  (image_width, BOTTOM_LINE_Y),  (0, 0, 255), 2)
        band_h = max(1, BOTTOM_LINE_Y - TOP_LINE_Y)
        percent_raw = ((wear_y - TOP_LINE_Y) / band_h) * 100.0
        percent_raw = float(np.clip(percent_raw, 0.0, 100.0))
        asinma_yuzdesi = percent_raw
        text = f"Asinma : {asinma_yuzdesi:.2f}%"
        cv2.putText(image, text, (image_width - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        return asinma_yuzdesi, image

    @staticmethod
    def _append_csv(csv_path: str, ldc_image_path: str, percent: float) -> None:
        header_needed = not os.path.exists(csv_path)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if header_needed:
                writer.writerow(["timestamp", "frame", "wear_percent"])
            writer.writerow([datetime.now().isoformat(timespec='seconds'), os.path.basename(ldc_image_path), f"{percent:.2f}"]) 