import time
import serial
import struct
import threading
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque

class HighSpeedReader:
    def __init__(self, port='COM7', baudrate=230400):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.is_running = False
        self.log_callback = None
        
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
        self.log_callback = callback

    def log(self, message, data=None):
        timestamp = time.strftime('%H:%M:%S')
        if data:
            log_message = f"{timestamp} - {message}: {[hex(x) for x in data]}"
        else:
            log_message = f"{timestamp} - {message}"
            
        print(log_message)
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

    def parse_data(self, data):
        if not data or len(data) < 26:  # 13 register * 2 byte
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

    def start_reading(self):
        self.is_running = True
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.data_count = 0
        threading.Thread(target=self._reading_loop, daemon=True).start()

    def stop_reading(self):
        self.is_running = False

    def _reading_loop(self):
        while self.is_running:
            try:
                # Sürekli veri akışını oku
                data = self.serial.read(26)  # 13 register * 2 byte
                
                if len(data) == 26:
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
                self.log(f"Okuma hatası: {str(e)}")
                time.sleep(0.1)

class HighSpeedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Yüksek Hız Modu Okuyucu")
        self.root.geometry("1200x800")
        
        # Okuyucu nesnesi
        self.reader = HighSpeedReader()
        self.reader.set_log_callback(self.log_output)
        
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
        
        # Veri hızı göstergesi
        self.rate_var = tk.StringVar(value="Veri Hızı: 0 Hz")
        self.rate_label = ttk.Label(self.control_frame, textvariable=self.rate_var)
        self.rate_label.grid(row=0, column=3, padx=5)
        
        # Log alanı
        self.output_frame = ttk.LabelFrame(self.main_frame, text="Log", padding="5")
        self.output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.output_text = tk.Text(self.output_frame, height=10, width=80)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
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
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_graphs(self):
        if self.reader.is_running:
            self.rate_var.set(f"Veri Hızı: {self.reader.data_rate} Hz")
            
            # Titreşim hızı grafiği
            self.vel_ax.clear()
            self.vel_ax.set_title("Titreşim Hızı")
            self.vel_ax.set_ylabel("mm/s")
            self.vel_ax.grid(True)
            for axis, data in self.reader.velocity_data.items():
                if len(data) > 0:
                    self.vel_ax.plot(list(self.reader.time_data), list(data), label=axis)
            self.vel_ax.legend()
            
            # Yer değiştirme grafiği
            self.disp_ax.clear()
            self.disp_ax.set_title("Yer Değiştirme")
            self.disp_ax.set_ylabel("mm")
            self.disp_ax.grid(True)
            for axis, data in self.reader.displacement_data.items():
                if len(data) > 0:
                    self.disp_ax.plot(list(self.reader.time_data), list(data), label=axis)
            self.disp_ax.legend()
            
            # Sıcaklık grafiği
            self.temp_ax.clear()
            self.temp_ax.set_title("Sıcaklık")
            self.temp_ax.set_ylabel("°C")
            self.temp_ax.grid(True)
            if len(self.reader.temperature_data) > 0:
                self.temp_ax.plot(list(self.reader.time_data), list(self.reader.temperature_data), label="Sıcaklık")
                self.temp_ax.legend()
            
            # Frekans grafiği
            self.freq_ax.clear()
            self.freq_ax.set_title("Frekans")
            self.freq_ax.set_ylabel("Hz")
            self.freq_ax.grid(True)
            for axis, data in self.reader.frequency_data.items():
                if len(data) > 0:
                    self.freq_ax.plot(list(self.reader.time_data), list(data), label=axis)
            self.freq_ax.legend()
            
            self.fig.tight_layout()
            self.canvas.draw()
        
        self.root.after(50, self.update_graphs)

    def toggle_connection(self):
        if not self.reader.is_running:
            self.reader.port = self.port_var.get()
            if self.reader.connect():
                self.reader.start_reading()
                self.connect_btn.configure(text="Bağlantıyı Kes")
                self.status_var.set("Bağlantı kuruldu")
                self.port_combo.configure(state="disabled")
                self.log_output("Bağlantı başarıyla kuruldu")
        else:
            self.reader.stop_reading()
            self.reader.disconnect()
            self.connect_btn.configure(text="Bağlan")
            self.status_var.set("Bağlantı kesildi")
            self.port_combo.configure(state="normal")
            self.log_output("Bağlantı kesildi")

    def log_output(self, message):
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)

    def on_closing(self):
        if self.reader.is_running:
            self.reader.stop_reading()
            self.reader.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = HighSpeedGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 