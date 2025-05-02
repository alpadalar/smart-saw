import plotly.graph_objects as go
from plotly.subplots import make_subplots
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from tkinter import ttk, messagebox
from tkhtmlview import HTMLLabel
import tkinter as tk

class InfoGrid:
    """Sensör verilerini gösteren grid"""
    def __init__(self, parent, fields):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Her satırda 3 değer göster
        row = 0
        col = 0
        for field in fields:
            # Label oluştur
            label = ttk.Label(self.frame, text=field.replace('_', ' ').title())
            label.grid(row=row, column=col*2, padx=5, pady=2, sticky=tk.E)
            
            # Değer göstergesi
            value = ttk.Label(self.frame, text="-")
            value.grid(row=row, column=col*2+1, padx=5, pady=2, sticky=tk.W)
            
            # Sonraki sütuna geç
            col += 1
            if col >= 3:  # 3 sütun dolunca alt satıra geç
                col = 0
                row += 1

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Akıllı Testere Kontrol Sistemi")
        
        # Ana frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Üst kısım - Kontrol ve durum
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Kontrol modu seçimi
        control_frame = ttk.LabelFrame(top_frame, text="Kontrol Modu", padding=(5, 5))
        control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.control_mode = ttk.Combobox(
            control_frame,
            values=["Manuel", "Fuzzy", "Lineer", "Dinamik", "LSTM", "ML"],
            state="readonly"
        )
        self.control_mode.set("Manuel")
        self.control_mode.pack(fill=tk.X, padx=5, pady=5)
        
        # Katsayı ayarı
        coefficient_frame = ttk.LabelFrame(top_frame, text="Katsayı Ayarı", padding=(5, 5))
        coefficient_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.coefficient_var = tk.StringVar(value="1.0")
        coefficient_entry = ttk.Entry(coefficient_frame, textvariable=self.coefficient_var, width=10)
        coefficient_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        coefficient_button = ttk.Button(coefficient_frame, text="Uygula", command=self.on_coefficient_change)
        coefficient_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Durum göstergesi ve Kesim Özeti butonu
        status_frame = ttk.LabelFrame(top_frame, text="Durum", padding=(5, 5))
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        status_button_frame = ttk.Frame(status_frame)
        status_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_button_frame, text="Hazır")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.summary_button = ttk.Button(status_button_frame, text="Kesim Özeti", command=self.show_cutting_summary)
        self.summary_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Orta kısım - Sensör verileri
        self.info_grid = InfoGrid(main_frame, [
            'serit_motor_akim_a',
            'serit_motor_tork_percentage',
            'serit_kesme_hizi',
            'serit_inme_hizi',
            'serit_sapmasi',
            'serit_gerginligi_bar',
            'mengene_basinc_bar',
            'kafa_yuksekligi_mm',
            'ortam_sicakligi_c',
            'ortam_nem_percentage',
            'sogutma_sivi_sicakligi_c',
            'hidrolik_yag_sicakligi_c',
            'ivme_olcer_x',
            'ivme_olcer_y',
            'ivme_olcer_z',
            'ivme_olcer_x_hz',
            'ivme_olcer_y_hz',
            'ivme_olcer_z_hz'
        ])
        
        # Alt kısım - Grafik
        plot_frame = ttk.LabelFrame(main_frame, text="Grafik", padding=(5, 5))
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()
        
        # Grafik ayarları
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Sensör Verileri')
        self.ax.set_xlabel('Zaman')
        self.ax.set_ylabel('Değer')
        self.figure.tight_layout() 

    def on_coefficient_change(self):
        """Katsayı değişikliği butonuna tıklandığında çağrılır"""
        new_value = self.coefficient_var.get()
        if hasattr(self, 'controller'):
            self.controller._on_coefficient_change(new_value) 

    def show_cutting_summary(self):
        """Son kesimin akım değerlerini gösteren pencereyi açar"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Kesim Özeti")
        summary_window.geometry("1920x1080")
        # screen_width = summary_window.winfo_screenwidth()
        # screen_height = summary_window.winfo_screenheight()
        # summary_window.geometry(f"{screen_width}x{screen_height}")


        # Grafik için frame
        plot_frame = ttk.Frame(summary_window, padding="10")
        plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Plotly grafiği için figure oluştur
        fig = go.Figure()
        
        # Verileri ekle (controller'dan alınacak)
        if hasattr(self, 'controller'):
            last_cut_data = self.controller.get_last_cut_data()
            if last_cut_data:
                fig.add_trace(go.Scatter(
                    x=last_cut_data['timestamp'],
                    y=last_cut_data['serit_motor_akim_a'],
                    name='Sol Kol Akım',
                    hovertemplate='Zaman: %{x}<br>' +
                                'Akım: %{y:.2f} A<br>' +
                                'Hız: %{customdata[0]:.2f} mm/s<br>' +
                                'Sapma: %{customdata[1]:.2f} mm<br>' +
                                '<extra></extra>',
                    customdata=list(zip(
                        last_cut_data['serit_kesme_hizi'],
                        last_cut_data['serit_sapmasi']
                    ))
                ))
                
                fig.add_trace(go.Scatter(
                    x=last_cut_data['timestamp'],
                    y=last_cut_data['inme_motor_akim_a'],
                    name='Alt Kol Akım',
                    hovertemplate='Zaman: %{x}<br>' +
                                'Akım: %{y:.2f} A<br>' +
                                'Hız: %{customdata[0]:.2f} mm/s<br>' +
                                'Sapma: %{customdata[1]:.2f} mm<br>' +
                                '<extra></extra>',
                    customdata=list(zip(
                        last_cut_data['serit_inme_hizi'],
                        last_cut_data['serit_sapmasi']
                    ))
                ))
                
                fig.add_trace(go.Scatter(
                    x=last_cut_data['timestamp'],
                    y=last_cut_data['kafa_yuksekligi_mm'],
                    name='Kafa Yüksekliği',
                    hovertemplate='Zaman: %{x}<br>' +
                                'Yükseklik: %{y:.2f} mm<br>' +
                                'Hız: %{customdata[0]:.2f} mm/s<br>' +
                                'Sapma: %{customdata[1]:.2f} mm<br>' +
                                '<extra></extra>',
                    customdata=list(zip(
                        last_cut_data['serit_inme_hizi'],
                        last_cut_data['serit_sapmasi']
                    ))
                ))
                
                # Grafik düzeni
                fig.update_layout(
                    title='Son Kesim Verileri',
                    xaxis_title='Zaman',
                    yaxis_title='Değer',
                    hovermode='x unified'
                )
                
                # Plotly grafiğini HTML olarak kaydet ve göster
                html_widget = HTMLLabel(plot_frame, html=fig.to_html(include_plotlyjs='cdn'))
                html_widget.pack(fill=tk.BOTH, expand=True) 