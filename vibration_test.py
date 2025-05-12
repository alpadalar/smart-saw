import time
import serial
import struct
import threading
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import deque

class VibrationSensor:
    def __init__(self, port='COM7', baudrate=9600, addr=0x50):
        self.port = port
        self.baudrate = baudrate
        self.addr = addr
        self.serial = None
        self.is_running = False
        self.temp_bytes = []
        self.highspeed_mode = False
        self.log_callback = None  # Log callback fonksiyonu
        
        # Veri depolama için deques (son 100 ölçüm)
        self.data_points = 100
        self.time_data = deque(maxlen=self.data_points)
        self.velocity_data = {
            'VX': deque(maxlen=self.data_points),
            'VY': deque(maxlen=self.data_points),
            'VZ': deque(maxlen=self.data_points)
        }
        self.displacement_data = {
            'DX': deque(maxlen=self.data_points),
            'DY': deque(maxlen=self.data_points),
            'DZ': deque(maxlen=self.data_points)
        }
        self.temperature_data = deque(maxlen=self.data_points)
        self.frequency_data = {
            'HX': deque(maxlen=self.data_points),
            'HY': deque(maxlen=self.data_points),
            'HZ': deque(maxlen=self.data_points)
        }
        
        # Veri hızı hesaplama için
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.data_count = 0
        self.data_rate = 0

    def set_log_callback(self, callback):
        """Log callback fonksiyonunu ayarla"""
        self.log_callback = callback

    def log(self, message, data=None):
        """Log mesajı gönder"""
        timestamp = time.strftime('%H:%M:%S')
        if data:
            log_message = f"{timestamp} - {message}: {[hex(x) for x in data]}"
        else:
            log_message = f"{timestamp} - {message}"
            
        # Terminale yazdır
        print(log_message)
        
        # Arayüze yazdır
        if self.log_callback:
            self.log_callback(log_message)

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
            self.log(f"Seri port bağlantısı kuruldu: {self.port} ({self.baudrate} baud)")
            return True
        except Exception as e:
            self.log(f"Bağlantı hatası: {str(e)}")
            return False

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.log("Seri port bağlantısı kapatıldı")

    def get_crc(self, data):
        """CRC hesaplama"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return crc

    def read_registers(self, start_addr, count):
        """Register okuma komutu gönder"""
        command = [
            self.addr,           # Cihaz adresi
            0x03,               # Fonksiyon kodu (03: okuma)
            start_addr >> 8,    # Başlangıç adresi (yüksek byte)
            start_addr & 0xFF,  # Başlangıç adresi (düşük byte)
            count >> 8,         # Register sayısı (yüksek byte)
            count & 0xFF        # Register sayısı (düşük byte)
        ]
        
        # CRC ekle
        crc = self.get_crc(command)
        command.append(crc & 0xFF)
        command.append(crc >> 8)
        
        # Komutu gönder
        self.serial.write(bytes(command))
        
        # Yanıtı bekle
        response = self.serial.read(5 + count * 2)  # Header(5) + Data(count*2)
        
        if len(response) == 5 + count * 2:
            # CRC kontrolü
            received_crc = response[-2] | (response[-1] << 8)
            calculated_crc = self.get_crc(response[:-2])
            
            if received_crc == calculated_crc:
                return response[3:-2]  # Sadece veri kısmını döndür
        return None

    def parse_data(self, data):
        """Gelen veriyi çözümle"""
        if not data:
            return None
            
        values = {}
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                value = (data[i] << 8) | data[i + 1]
                reg_addr = 0x3A + (i // 2)  # 0x3A'dan başlayan register adresleri
                
                # Register adresine göre değeri yorumla
                if 0x3A <= reg_addr <= 0x3C:  # Hız değerleri (VX, VY, VZ)
                    values[f'V{chr(88 + reg_addr - 0x3A)}'] = value / 100.0  # mm/s
                elif 0x3D <= reg_addr <= 0x3F:  # Açı değerleri (AX, AY, AZ)
                    values[f'A{chr(88 + reg_addr - 0x3D)}'] = value / 32768.0 * 180.0  # derece
                elif reg_addr == 0x40:  # Sıcaklık
                    values['TEMP'] = value / 100.0  # °C
                elif 0x41 <= reg_addr <= 0x43:  # Yer değiştirme (DX, DY, DZ)
                    values[f'D{chr(88 + reg_addr - 0x41)}'] = value / 1000.0  # mm
                elif 0x44 <= reg_addr <= 0x46:  # Frekans (HX, HY, HZ)
                    values[f'H{chr(88 + reg_addr - 0x44)}'] = value / 10.0  # Hz
                    
        return values

    def start_reading(self):
        """Sürekli okuma başlat"""
        self.is_running = True
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.data_count = 0
        threading.Thread(target=self._reading_loop, daemon=True).start()

    def stop_reading(self):
        """Sürekli okumayı durdur"""
        self.is_running = False

    def _reading_loop(self):
        """Sürekli okuma döngüsü"""
        while self.is_running:
            try:
                # 0x3A adresinden 13 register oku (tüm değerler)
                data = self.read_registers(0x3A, 13)
                values = self.parse_data(data)
                
                if values:
                    current_time = time.time()
                    self.time_data.append(current_time - self.start_time)
                    
                    # Verileri kaydet
                    for axis in ['VX', 'VY', 'VZ']:
                        if axis in values:
                            self.velocity_data[axis].append(values[axis])
                    
                    for axis in ['DX', 'DY', 'DZ']:
                        if axis in values:
                            self.displacement_data[axis].append(values[axis])
                    
                    if 'TEMP' in values:
                        self.temperature_data.append(values['TEMP'])
                    
                    for axis in ['HX', 'HY', 'HZ']:
                        if axis in values:
                            self.frequency_data[axis].append(values[axis])
                    
                    # Veri hızını hesapla
                    self.data_count += 1
                    if current_time - self.last_update_time >= 1.0:
                        self.data_rate = self.data_count
                        self.data_count = 0
                        self.last_update_time = current_time
                
            except Exception as e:
                print(f"Okuma hatası: {str(e)}")
                time.sleep(0.1)

    def write_register(self, reg_addr, value):
        """Register'a yazma yap"""
        command = [
            self.addr,           # Cihaz adresi
            0x06,               # Fonksiyon kodu (06: yazma)
            reg_addr >> 8,      # Register adresi (yüksek byte)
            reg_addr & 0xFF,    # Register adresi (düşük byte)
            value >> 8,         # Değer (yüksek byte)
            value & 0xFF        # Değer (düşük byte)
        ]
        
        # CRC ekle
        crc = self.get_crc(command)
        command.append(crc & 0xFF)
        command.append(crc >> 8)
        
        # Komutu gönder
        self.serial.write(bytes(command))
        self.log(f"Register yazma komutu gönderildi (0x{reg_addr:04X} -> 0x{value:04X})", command)
        
        # Yanıtı bekle
        response = self.serial.read(8)  # 8 byte yanıt bekliyoruz
        
        if len(response) == 8:
            # CRC kontrolü
            received_crc = response[-2] | (response[-1] << 8)
            calculated_crc = self.get_crc(response[:-2])
            
            if received_crc == calculated_crc:
                self.log("Register yazma başarılı", response)
                return True
            else:
                self.log("CRC hatası", response)
        else:
            self.log(f"Geçersiz yanıt uzunluğu: {len(response)}", response)
        return False

    def set_highspeed_mode(self, enable=True):
        """Yüksek hız modunu ayarla"""
        try:
            if enable:
                self.log("Yüksek hız modu aktifleştiriliyor...")
                # Kilidi açmak için sabit komut
                unlock_command = [0x50, 0x06, 0x00, 0x69, 0xB5, 0x88]
                # CRC ekle
                crc = self.get_crc(unlock_command)
                unlock_command.append(crc & 0xFF)
                unlock_command.append(crc >> 8)
                
                self.serial.write(bytes(unlock_command))
                self.log("Kilit açma komutu gönderildi", unlock_command)
                time.sleep(0.5)  # Yanıt için bekleme süresini artırdım
                
                # Yanıtı kontrol et
                response = self.serial.read(8)
                if len(response) == 8:
                    self.log("Kilit açma yanıtı alındı", response)
                    if all(x == 0 for x in response):
                        self.log("UYARI: Kilit açma yanıtı boş geldi! Tekrar deneniyor...")
                        time.sleep(0.5)
                        self.serial.write(bytes(unlock_command))
                        response = self.serial.read(8)
                        if all(x == 0 for x in response):
                            self.log("HATA: İkinci denemede de kilit açılamadı!")
                            return False
                
                # Yüksek hız modunu aktif et
                if self.write_register(0x62, 0x0001):
                    time.sleep(0.5)
                    # Değişiklikleri kaydet
                    save_command = [0x50, 0x06, 0x00, 0x00, 0x00, 0x84]
                    # CRC ekle
                    crc = self.get_crc(save_command)
                    save_command.append(crc & 0xFF)
                    save_command.append(crc >> 8)
                    
                    self.serial.write(bytes(save_command))
                    self.log("Save komutu gönderildi", save_command)
                    time.sleep(0.5)
                    
                    # Save yanıtını kontrol et
                    response = self.serial.read(8)
                    if len(response) == 8:
                        self.log("Save yanıtı alındı", response)
                        if all(x == 0 for x in response):
                            self.log("UYARI: Save yanıtı boş geldi! Tekrar deneniyor...")
                            time.sleep(0.5)
                            self.serial.write(bytes(save_command))
                            response = self.serial.read(8)
                            if all(x == 0 for x in response):
                                self.log("HATA: İkinci denemede de save yapılamadı!")
                                return False
                    
                    # Baud rate'i 230400'e ayarla
                    self.serial.baudrate = 230400
                    self.highspeed_mode = True
                    self.log("Baud rate 230400'e ayarlandı")
                    return True
                else:
                    self.log("HATA: Register yazma başarısız!")
                    return False
            else:
                self.log("Normal moda geçiliyor...")
                # Kilidi açmak için sabit komut
                unlock_command = [0x50, 0x06, 0x00, 0x69, 0xB5, 0x88]
                # CRC ekle
                crc = self.get_crc(unlock_command)
                unlock_command.append(crc & 0xFF)
                unlock_command.append(crc >> 8)
                
                self.serial.write(bytes(unlock_command))
                self.log("Kilit açma komutu gönderildi", unlock_command)
                time.sleep(0.5)
                
                # Yanıtı kontrol et
                response = self.serial.read(8)
                if len(response) == 8:
                    self.log("Kilit açma yanıtı alındı", response)
                    if all(x == 0 for x in response):
                        self.log("UYARI: Kilit açma yanıtı boş geldi! Tekrar deneniyor...")
                        time.sleep(0.5)
                        self.serial.write(bytes(unlock_command))
                        response = self.serial.read(8)
                        if all(x == 0 for x in response):
                            self.log("HATA: İkinci denemede de kilit açılamadı!")
                            return False
                
                # Normal moda dön
                if self.write_register(0x62, 0x0000):
                    time.sleep(0.5)
                    # Değişiklikleri kaydet
                    save_command = [0x50, 0x06, 0x00, 0x00, 0x00, 0x84]
                    # CRC ekle
                    crc = self.get_crc(save_command)
                    save_command.append(crc & 0xFF)
                    save_command.append(crc >> 8)
                    
                    self.serial.write(bytes(save_command))
                    self.log("Save komutu gönderildi", save_command)
                    time.sleep(0.5)
                    
                    # Save yanıtını kontrol et
                    response = self.serial.read(8)
                    if len(response) == 8:
                        self.log("Save yanıtı alındı", response)
                        if all(x == 0 for x in response):
                            self.log("UYARI: Save yanıtı boş geldi! Tekrar deneniyor...")
                            time.sleep(0.5)
                            self.serial.write(bytes(save_command))
                            response = self.serial.read(8)
                            if all(x == 0 for x in response):
                                self.log("HATA: İkinci denemede de save yapılamadı!")
                                return False
                    
                    # Baud rate'i 9600'e geri döndür
                    self.serial.baudrate = 9600
                    self.highspeed_mode = False
                    self.log("Baud rate 9600'e ayarlandı")
                    return True
                else:
                    self.log("HATA: Register yazma başarısız!")
                    return False
        except Exception as e:
            self.log(f"HATA: {str(e)}")
            return False

class VibrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Titreşim Sensörü Arayüzü")
        self.root.geometry("1200x800")
        
        # Sensör nesnesi
        self.sensor = VibrationSensor()
        self.sensor.set_log_callback(self.log_output)  # Log callback'i ayarla
        
        # Ana frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Kontrol frame
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Kontroller", padding="5")
        self.control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Port seçimi
        ttk.Label(self.control_frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_var = tk.StringVar(value="COM7")
        self.port_combo = ttk.Combobox(self.control_frame, textvariable=self.port_var, values=["COM7", "COM8", "COM9"])
        self.port_combo.grid(row=0, column=1, padx=5)
        
        # Bağlantı butonu
        self.connect_btn = ttk.Button(self.control_frame, text="Bağlan", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=2, padx=5)
        
        # Yüksek hız modu butonu
        self.highspeed_btn = ttk.Button(self.control_frame, text="Yüksek Hız Modu", command=self.toggle_highspeed)
        self.highspeed_btn.grid(row=0, column=3, padx=5)
        self.highspeed_btn.configure(state="disabled")
        
        # Veri hızı göstergesi
        self.rate_var = tk.StringVar(value="Veri Hızı: 0 Hz")
        self.rate_label = ttk.Label(self.control_frame, textvariable=self.rate_var)
        self.rate_label.grid(row=0, column=4, padx=5)
        
        # Komut çıktıları için text alanı
        self.output_frame = ttk.LabelFrame(self.main_frame, text="Komut Çıktıları", padding="5")
        self.output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.output_text = tk.Text(self.output_frame, height=10, width=80)  # Yüksekliği artırdım
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(self.output_text, command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        # Grafik frame
        self.graph_frame = ttk.Frame(self.main_frame)
        self.graph_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grafikleri oluştur
        self.create_graphs()
        
        # Durum çubuğu
        self.status_var = tk.StringVar(value="Bağlantı bekleniyor...")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Pencere kapatıldığında
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Grafik güncelleme
        self.update_graphs()

    def create_graphs(self):
        # Grafik figürü
        self.fig = Figure(figsize=(12, 8), dpi=100)
        
        # Titreşim hızı grafiği
        self.vel_ax = self.fig.add_subplot(221)
        self.vel_ax.set_title("Titreşim Hızı")
        self.vel_ax.set_ylabel("mm/s")
        self.vel_ax.grid(True)
        
        # Yer değiştirme grafiği
        self.disp_ax = self.fig.add_subplot(222)
        self.disp_ax.set_title("Yer Değiştirme")
        self.disp_ax.set_ylabel("mm")
        self.disp_ax.grid(True)
        
        # Sıcaklık grafiği
        self.temp_ax = self.fig.add_subplot(223)
        self.temp_ax.set_title("Sıcaklık")
        self.temp_ax.set_ylabel("°C")
        self.temp_ax.grid(True)
        
        # Frekans grafiği
        self.freq_ax = self.fig.add_subplot(224)
        self.freq_ax.set_title("Frekans")
        self.freq_ax.set_ylabel("Hz")
        self.freq_ax.grid(True)
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_graphs(self):
        if self.sensor.is_running:
            # Veri hızını güncelle
            self.rate_var.set(f"Veri Hızı: {self.sensor.data_rate} Hz")
            
            # Titreşim hızı grafiği
            self.vel_ax.clear()
            self.vel_ax.set_title("Titreşim Hızı")
            self.vel_ax.set_ylabel("mm/s")
            self.vel_ax.grid(True)
            has_velocity_data = False
            for axis, data in self.sensor.velocity_data.items():
                if len(data) > 0:
                    self.vel_ax.plot(list(self.sensor.time_data), list(data), label=axis)
                    has_velocity_data = True
            if has_velocity_data:
                self.vel_ax.legend()
            
            # Yer değiştirme grafiği
            self.disp_ax.clear()
            self.disp_ax.set_title("Yer Değiştirme")
            self.disp_ax.set_ylabel("mm")
            self.disp_ax.grid(True)
            has_displacement_data = False
            for axis, data in self.sensor.displacement_data.items():
                if len(data) > 0:
                    self.disp_ax.plot(list(self.sensor.time_data), list(data), label=axis)
                    has_displacement_data = True
            if has_displacement_data:
                self.disp_ax.legend()
            
            # Sıcaklık grafiği
            self.temp_ax.clear()
            self.temp_ax.set_title("Sıcaklık")
            self.temp_ax.set_ylabel("°C")
            self.temp_ax.grid(True)
            if len(self.sensor.temperature_data) > 0:
                self.temp_ax.plot(list(self.sensor.time_data), list(self.sensor.temperature_data), label="Sıcaklık")
                self.temp_ax.legend()
            
            # Frekans grafiği
            self.freq_ax.clear()
            self.freq_ax.set_title("Frekans")
            self.freq_ax.set_ylabel("Hz")
            self.freq_ax.grid(True)
            has_frequency_data = False
            for axis, data in self.sensor.frequency_data.items():
                if len(data) > 0:
                    self.freq_ax.plot(list(self.sensor.time_data), list(data), label=axis)
                    has_frequency_data = True
            if has_frequency_data:
                self.freq_ax.legend()
            
            self.fig.tight_layout()
            self.canvas.draw()
        
        self.root.after(50, self.update_graphs)

    def toggle_connection(self):
        if not self.sensor.is_running:
            # Bağlan
            self.sensor.port = self.port_var.get()
            if self.sensor.connect():
                self.sensor.start_reading()
                self.connect_btn.configure(text="Bağlantıyı Kes")
                self.status_var.set("Bağlantı kuruldu")
                self.port_combo.configure(state="disabled")
                self.highspeed_btn.configure(state="normal")  # Yüksek hız butonunu aktif et
                self.log_output("Bağlantı başarıyla kuruldu")
        else:
            # Bağlantıyı kes
            self.sensor.stop_reading()
            self.sensor.disconnect()
            self.connect_btn.configure(text="Bağlan")
            self.status_var.set("Bağlantı kesildi")
            self.port_combo.configure(state="normal")
            self.highspeed_btn.configure(state="disabled")  # Yüksek hız butonunu devre dışı bırak
            self.log_output("Bağlantı kesildi")

    def toggle_highspeed(self):
        try:
            if not self.sensor.highspeed_mode:
                self.log_output("Yüksek hız modu aktifleştiriliyor...")
                if self.sensor.set_highspeed_mode(True):
                    self.highspeed_btn.configure(text="Normal Mod")
                    self.status_var.set("Yüksek hız modu aktif")
                    self.log_output("Yüksek hız modu başarıyla aktifleştirildi")
                else:
                    self.log_output("Yüksek hız modu aktifleştirilemedi!")
                    self.status_var.set("Yüksek hız modu aktifleştirilemedi")
            else:
                self.log_output("Normal moda geçiliyor...")
                if self.sensor.set_highspeed_mode(False):
                    self.highspeed_btn.configure(text="Yüksek Hız Modu")
                    self.status_var.set("Normal mod aktif")
                    self.log_output("Normal moda başarıyla geçildi")
                else:
                    self.log_output("Normal moda geçilemedi!")
                    self.status_var.set("Normal moda geçilemedi")
        except Exception as e:
            self.log_output(f"HATA: {str(e)}")
            self.status_var.set("Hata oluştu")

    def log_output(self, message):
        """Komut çıktılarını text alanına yaz"""
        self.output_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.output_text.see(tk.END)  # Otomatik kaydır

    def on_closing(self):
        if self.sensor.is_running:
            self.sensor.stop_reading()
            self.sensor.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = VibrationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
