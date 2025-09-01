# Bu script, seri port üzerinden gelen titreşim verilerini CSV dosyasına kaydeder.
# Kullanım: python data_logger.py
# Çıktı dosyası: vibration_data_YYYYMMDD_HHMMSS.csv
# Ctrl+C ile kayıt durdurulabilir.

import time
import serial
import csv
from datetime import datetime

class DataLogger:
    def __init__(self, port='COM6', baudrate=230400):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.is_running = False
        self.data_count = 0
        self.total_data_count = 0
        self.last_update_time = time.time()
        
        # CSV dosyasını oluştur
        self.filename = f"vibration_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(self.filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'VX', 'VY', 'VZ', 'DX', 'DY', 'DZ', 'TEMP', 'HX', 'HY', 'HZ'])

    def connect(self):
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=0.1
            )
            print(f"Seri port bağlantısı kuruldu: {self.port} ({self.baudrate} baud)")
            return True
        except Exception as e:
            print(f"Bağlantı hatası: {str(e)}")
            return False

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("Seri port bağlantısı kapatıldı")

    def parse_data(self, data):
        if not data or len(data) < 26:
            return None
            
        values = {}
        for i in range(0, 26, 2):
            value = (data[i] << 8) | data[i + 1]
            reg_addr = 0x3A + (i // 2)
            
            if 0x3A <= reg_addr <= 0x3C:  # Hız değerleri
                values[f'V{chr(88 + reg_addr - 0x3A)}'] = value / 100.0
            elif 0x3D <= reg_addr <= 0x3F:  # Açı değerleri
                values[f'A{chr(88 + reg_addr - 0x3D)}'] = value / 32768.0 * 180.0
            elif reg_addr == 0x40:  # Sıcaklık
                values['TEMP'] = value / 100.0
            elif 0x41 <= reg_addr <= 0x43:  # Yer değiştirme
                values[f'D{chr(88 + reg_addr - 0x41)}'] = value / 1000.0
            elif 0x44 <= reg_addr <= 0x46:  # Frekans
                values[f'H{chr(88 + reg_addr - 0x44)}'] = value / 10.0
                    
        return values

    def start_logging(self):
        self.is_running = True
        self.last_update_time = time.time()
        self.data_count = 0
        
        while self.is_running:
            try:
                data = self.serial.read(26)
                
                if len(data) == 26:
                    values = self.parse_data(data)
                    
                    if values:
                        current_time = time.time()
                        timestamp = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        
                        # Verileri CSV'ye kaydet
                        with open(self.filename, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                timestamp,
                                values.get('VX', ''),
                                values.get('VY', ''),
                                values.get('VZ', ''),
                                values.get('DX', ''),
                                values.get('DY', ''),
                                values.get('DZ', ''),
                                values.get('TEMP', ''),
                                values.get('HX', ''),
                                values.get('HY', ''),
                                values.get('HZ', '')
                            ])
                        
                        # Veri sayacını güncelle
                        self.data_count += 1
                        self.total_data_count += 1
                        
                        # Her saniye istatistikleri göster
                        if current_time - self.last_update_time >= 1.0:
                            print(f"Veri hızı: {self.data_count} satır/saniye")
                            print(f"Toplam veri sayısı: {self.total_data_count}")
                            print(f"Son veri: {timestamp} - {values}")
                            self.data_count = 0
                            self.last_update_time = current_time
                
            except Exception as e:
                print(f"Okuma hatası: {str(e)}")
                time.sleep(0.1)

    def stop_logging(self):
        self.is_running = False

def main():
    logger = DataLogger()
    if logger.connect():
        try:
            logger.start_logging()
        except KeyboardInterrupt:
            print("\nKayıt durduruluyor...")
        finally:
            logger.stop_logging()
            logger.disconnect()

if __name__ == "__main__":
    main() 