import cv2  # OpenCV kütüphanesi - görüntü işleme için
import time  # Zaman işlemleri için
import os  # Dosya sistemi işlemleri için
import threading  # Çoklu iş parçacığı desteği için
from queue import Queue  # Thread'ler arası veri paylaşımı için
from datetime import datetime  # Tarih/saat işlemleri için
import logging  # Loglama işlemleri için
from core.constants import (  # Sabit değerler için
    CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS,
    CAMERA_DEVICE_ID, CAMERA_JPEG_QUALITY, CAMERA_NUM_THREADS,
    CAMERA_RECORDINGS_DIR
)
from core.logger import logger  # Loglama fonksiyonları için
from core.broken_detect import detect_broken_objects  # Nesne tespiti fonksiyonu için

class CameraModule:
    def __init__(self):
        self.cap = None  # Kamera nesnesi
        self.is_recording = False  # Kayıt durumu
        self.is_viewing = False  # Görüntüleme durumu
        self.frame_queue = Queue(maxsize=100)  # Frame kuyruğu
        self.frame_count = 0  # Frame sayacı
        self.start_time = None  # Başlangıç zamanı
        self.output_dir = None  # Çıkış klasörü
        self.base_output_dir = os.path.join(os.getcwd(), CAMERA_RECORDINGS_DIR)  # Ana çıkış klasörü
        os.makedirs(self.base_output_dir, exist_ok=True)  # Çıkış klasörünü oluştur
        self.threads = []  # Thread listesi
        self.view_window = None  # Görüntüleme penceresi
        self.is_initialized = False  # Başlatma durumu
        self.initialization_lock = threading.Lock()  # Başlatma kilidi
        self.view_thread = None  # Görüntüleme thread'i
        self.stop_event = threading.Event()  # Durdurma olayı
        self.current_frame = None  # Mevcut frame
        self.frame_ready = threading.Event()  # Frame hazır olayı
        self.capture_thread = None  # Yakalama thread'i
        self.recording_thread = None  # Kayıt thread'i
        self.frame_count_callback = None  # Frame sayısı güncelleme callback'i
        self.detection_thread = None  # Nesne tespiti thread'i
        self.is_detecting = False  # Tespit durumu
        self.detection_lock = threading.Lock()  # Tespit kilidi
        self.detection_stop_event = threading.Event()  # Tespit durdurma olayı
        
    def set_frame_count_callback(self, callback):
        """Frame sayısı güncellemesi için callback fonksiyonu ayarlar"""
        self.frame_count_callback = callback

    def _lazy_initialize(self):
        """Kamerayı lazy olarak başlatır"""
        if not self.is_initialized:
            with self.initialization_lock:
                if not self.is_initialized:  # Double-check locking
                    try:
                        if self._initialize_camera():
                            self._start_save_threads()
                            self.is_initialized = True
                        else:
                            logger.error("Kamera başlatılamadı")
                            return False
                    except Exception as e:
                        logger.error(f"Kamera başlatma hatası: {str(e)}")
                        return False
        return True

    def _initialize_camera(self):
        """Kamera bağlantısını başlatır ve ayarları yapar"""
        try:
            if self.cap is not None:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(CAMERA_DEVICE_ID, cv2.CAP_DSHOW)  # DirectShow kullan
            if not self.cap.isOpened():
                logger.error("Kamera açılamadı! Lütfen bağlantıyı kontrol edin.")
                return False
            
            # Kamera ayarlarını yap
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer boyutunu küçült
            
            # Ayarların uygulanıp uygulanmadığını kontrol et
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            # Sürekli frame yakalama thread'ini başlat
            self._start_capture_thread()
            
            logger.info(f"Kamera başlatıldı - Çözünürlük: {actual_width}x{actual_height}, FPS: {actual_fps}")
            return True
            
        except Exception as e:
            logger.error(f"Kamera başlatma hatası: {str(e)}")
            return False

    def _start_capture_thread(self):
        """Sürekli frame yakalama thread'ini başlatır"""
        def capture_loop():
            while not self.stop_event.is_set():
                if self.cap is None or not self.cap.isOpened():
                    time.sleep(0.1)
                    continue
                    
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = frame.copy()
                    self.frame_ready.set()
                    
                    # Kayıt yapılıyorsa frame'i kaydet
                    if self.is_recording and self.output_dir is not None:
                        self.frame_count += 1
                        try:
                            self.frame_queue.put_nowait((self.frame_count, frame.copy(), self.output_dir))
                            
                            # Frame sayısını güncelle
                            if self.frame_count_callback:
                                self.frame_count_callback(self.frame_count)
                                
                            # Her 100 karede bir log bas
                            if self.frame_count % 100 == 0:
                                elapsed_time = time.time() - self.start_time
                                logger.info(f"Kayıt devam ediyor - Kare: {self.frame_count}, Süre: {elapsed_time:.2f} saniye")
                        except Queue.Full:
                            logger.warning("Frame kuyruğu dolu, frame atlanıyor")
                else:
                    time.sleep(0.01)
            
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()

    def _save_frames(self):
        """Frame kaydetme işlemini gerçekleştiren thread fonksiyonu"""
        while True:
            frame_data = self.frame_queue.get()
            if frame_data is None:
                break
                
            frame_count, frame, output_dir = frame_data
            frame_filename = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), CAMERA_JPEG_QUALITY]
            
            try:
                cv2.imwrite(frame_filename, frame, encode_params)
            except Exception as e:
                logger.error(f"Frame kaydetme hatası: {str(e)}")
                
            self.frame_queue.task_done()

    def _start_save_threads(self):
        """Frame kaydetme thread'lerini başlatır"""
        for _ in range(CAMERA_NUM_THREADS):
            t = threading.Thread(target=self._save_frames, daemon=True)
            t.start()
            self.threads.append(t)

    def start_recording(self):
        """Kayıt işlemini başlatır"""
        if not self._lazy_initialize():
            return False
            
        if not self.is_recording and self.cap is not None:
            try:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                self.output_dir = os.path.join(self.base_output_dir, timestamp)
                os.makedirs(self.output_dir, exist_ok=True)
                self.is_recording = True
                self.frame_count = 0
                self.start_time = time.time()
                
                # Frame sayacını sıfırla
                if self.frame_count_callback:
                    self.frame_count_callback(0)
                    
                logger.info(f"Kayıt başladı: {self.output_dir}")
                return True
            except Exception as e:
                logger.error(f"Kayıt başlatma hatası: {str(e)}")
                self.is_recording = False
                return False
        return False

    def stop_recording(self):
        """Kayıt işlemini durdurur"""
        if self.is_recording:
            try:
                self.is_recording = False
                elapsed_time = time.time() - self.start_time
                total_frames = self.frame_count
                
                # Frame kuyruğunun boşalmasını bekle
                self.frame_queue.join()
                
                logger.info(f"Kayıt durduruldu - Toplam kare: {total_frames}, Süre: {elapsed_time:.2f} saniye")
                
                # Frame sayacını sıfırla
                self.frame_count = 0
                if self.frame_count_callback:
                    self.frame_count_callback(0)
                    
                return True
            except Exception as e:
                logger.error(f"Kayıt durdurma hatası: {str(e)}")
                return False
        return False

    def start_detection(self):
        """Nesne tespiti işlemini başlatır"""
        with self.detection_lock:  # Thread-safe kontrol
            if not self.is_detecting:
                try:
                    self.is_detecting = True
                    self.detection_stop_event.clear()  # Durdurma olayını sıfırla
                    self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
                    self.detection_thread.start()
                    logger.info("Nesne tespiti başlatıldı")
                    return True
                except Exception as e:
                    logger.error(f"Nesne tespiti başlatma hatası: {str(e)}")
                    self.is_detecting = False
                    return False
        return False

    def stop_detection(self):
        """Nesne tespiti işlemini durdurur"""
        with self.detection_lock:  # Thread-safe kontrol
            if self.is_detecting:
                try:
                    self.detection_stop_event.set()  # Durdurma sinyali gönder
                    if self.detection_thread and self.detection_thread.is_alive():
                        self.detection_thread.join(timeout=1.0)  # Thread'in kapanmasını bekle
                    self.is_detecting = False
                    logger.info("Nesne tespiti durduruldu")
                    return True
                except Exception as e:
                    logger.error(f"Nesne tespiti durdurma hatası: {str(e)}")
        return False

    def _detection_loop(self):
        """Nesne tespiti döngüsü"""
        try:
            while not self.detection_stop_event.is_set():
                detect_broken_objects()
                # Tespit işlemi tamamlandıktan sonra bekle
                time.sleep(1)  # Örnek olarak 1 saniye bekle
        except Exception as e:
            logger.error(f"Nesne tespiti döngüsü hatası: {str(e)}")
        finally:
            with self.detection_lock:
                self.is_detecting = False

    def start_viewing(self):
        """Kamera görüntüsünü göstermeye başlar"""
        if not self._lazy_initialize():
            return False
            
        if not self.is_viewing and self.cap is not None:
            try:
                self.is_viewing = True
                self.view_window = "Kamera Görüntüsü"
                self.stop_event.clear()
                
                def view_thread():
                    cv2.namedWindow(self.view_window, cv2.WINDOW_NORMAL)
                    cv2.resizeWindow(self.view_window, 800, 600)
                    
                    while self.is_viewing and not self.stop_event.is_set():
                        try:
                            if not self.frame_ready.wait(timeout=0.1):
                                continue
                                
                            if self.current_frame is not None:
                                frame = cv2.resize(self.current_frame.copy(), (800, 600))
                                cv2.imshow(self.view_window, frame)
                            
                            self.frame_ready.clear()
                            
                            key = cv2.waitKey(1) & 0xFF
                            if key == 27:  # ESC tuşu ile çık
                                self.stop_viewing()
                                break
                                
                        except Exception as e:
                            logger.error(f"Kamera görüntüleme hatası: {str(e)}")
                            time.sleep(0.1)
                    
                    try:
                        cv2.destroyWindow(self.view_window)
                    except:
                        pass
                
                self.view_thread = threading.Thread(target=view_thread, daemon=True)
                self.view_thread.start()
                logger.info("Kamera görüntüleme başlatıldı")
                return True
            except Exception as e:
                logger.error(f"Kamera görüntüleme başlatma hatası: {str(e)}")
                self.is_viewing = False
                return False
        return False

    def stop_viewing(self):
        """Kamera görüntüsünü göstermeyi durdurur"""
        if self.is_viewing:
            try:
                self.stop_event.set()
                self.is_viewing = False
                if self.view_thread and self.view_thread.is_alive():
                    self.view_thread.join(timeout=1.0)
                logger.info("Kamera görüntüleme durduruldu")
                return True
            except Exception as e:
                logger.error(f"Kamera görüntüleme durdurma hatası: {str(e)}")
        return False

    def close(self):
        """Kamera modülünü kapatır"""
        try:
            self.stop_event.set()  # Tüm thread'lere durma sinyali gönder
            
            # Kayıt ve görüntülemeyi durdur
            if self.is_recording:
                self.stop_recording()
            if self.is_viewing:
                self.stop_viewing()
            if self.is_detecting:
                self.stop_detection()
            
            # Frame kuyruğunu temizle
            try:
                while not self.frame_queue.empty():
                    self.frame_queue.get_nowait()
                    self.frame_queue.task_done()
                    
                for _ in self.threads:
                    self.frame_queue.put(None)
                for t in self.threads:
                    t.join(timeout=1.0)
            except:
                pass
            
            # Capture thread'ini bekle
            if self.capture_thread:
                self.capture_thread.join(timeout=1.0)
            
            # Kamerayı kapat
            if self.cap is not None:
                try:
                    self.cap.release()
                    self.cap = None
                except:
                    pass
            
            try:
                cv2.destroyAllWindows()
            except:
                pass
                
            logger.info("Kamera modülü kapatıldı")
            
        except Exception as e:
            logger.error(f"Kamera kapatma hatası: {str(e)}") 