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
            values=["Manuel", "Fuzzy", "Lineer", "Dinamik", "LSTM"],
            state="readonly"
        )
        self.control_mode.set("Manuel")
        self.control_mode.pack(fill=tk.X, padx=5, pady=5)
        
        # Durum göstergesi
        status_frame = ttk.LabelFrame(top_frame, text="Durum", padding=(5, 5))
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="Hazır")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
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