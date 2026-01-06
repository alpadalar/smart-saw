"""
Database schema definitions for SQLite databases.
"""

# raw.db - Raw Modbus register values (unprocessed)
# Stores exactly what comes from PLC registers without any scaling/conversion
SCHEMA_RAW_DB = """
CREATE TABLE IF NOT EXISTS raw_registers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Registers 1000-1012: Machine & Material Info
    reg_1000_makine_id INTEGER,
    reg_1001_serit_id INTEGER,
    reg_1002_serit_dis_mm INTEGER,
    reg_1003_serit_tip INTEGER,
    reg_1004_serit_marka INTEGER,
    reg_1005_serit_malz INTEGER,
    reg_1006_malzeme_cinsi INTEGER,
    reg_1007_malzeme_sertlik INTEGER,
    reg_1008_kesit_yapisi INTEGER,
    reg_1009_a_mm INTEGER,
    reg_1010_b_mm INTEGER,
    reg_1011_c_mm INTEGER,
    reg_1012_d_mm INTEGER,

    -- Registers 1013-1018: Head & Motor
    reg_1013_kafa_yuksekligi INTEGER,
    reg_1014_kesilen_parca_adeti INTEGER,
    reg_1015_serit_motor_akim INTEGER,
    reg_1016_serit_motor_tork INTEGER,
    reg_1017_inme_motor_akim INTEGER,
    reg_1018_inme_motor_tork INTEGER,

    -- Registers 1019-1024: Mechanical
    reg_1019_mengene_basinc INTEGER,
    reg_1020_serit_gerginligi INTEGER,
    reg_1021_ivme_olcer_x INTEGER,
    reg_1022_ivme_olcer_y INTEGER,
    reg_1023_ivme_olcer_z INTEGER,
    reg_1024_serit_sapmasi INTEGER,

    -- Registers 1025-1032: Environment & State
    reg_1025_ortam_sicakligi INTEGER,
    reg_1026_ortam_nem INTEGER,
    reg_1027_sogutma_sivi_sicakligi INTEGER,
    reg_1028_hidrolik_yag_sicakligi INTEGER,
    reg_1029_serit_sicakligi INTEGER,
    reg_1030_testere_durumu INTEGER,
    reg_1031_alarm_status INTEGER,
    reg_1032_alarm_bilgisi INTEGER,

    -- Registers 1033-1041: Speed & Vibration
    reg_1033_serit_kesme_hizi INTEGER,
    reg_1034_serit_inme_hizi INTEGER,
    reg_1035_ivme_olcer_x_hz INTEGER,
    reg_1036_ivme_olcer_y_hz INTEGER,
    reg_1037_ivme_olcer_z_hz INTEGER,
    reg_1038_fark_hz_x INTEGER,
    reg_1039_fark_hz_y INTEGER,
    reg_1040_fark_hz_z INTEGER,
    reg_1041_malzeme_genisligi INTEGER,

    -- Registers 1042-1043: Power (IEEE754 float as two 16-bit registers)
    reg_1042_guc_1 INTEGER,
    reg_1043_guc_2 INTEGER
);

CREATE INDEX IF NOT EXISTS idx_raw_timestamp ON raw_registers(timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_testere_durumu ON raw_registers(reg_1030_testere_durumu);
"""

# total.db - Processed sensor data + cutting sessions
SCHEMA_TOTAL_DB = """
-- Processed sensor data (scaled/converted from raw registers)
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Cutting session reference (NULL if not cutting)
    kesim_id INTEGER,

    -- Motor measurements (scaled)
    serit_motor_akim_a REAL,
    serit_motor_tork_percentage REAL,
    inme_motor_akim_a REAL,
    inme_motor_tork_percentage REAL,

    -- Speed values (scaled)
    serit_kesme_hizi REAL,
    serit_inme_hizi REAL,
    kesme_hizi_hedef REAL,
    inme_hizi_hedef REAL,

    -- Mechanical measurements (scaled)
    kafa_yuksekligi_mm REAL,
    serit_sapmasi REAL,
    serit_gerginligi_bar REAL,
    mengene_basinc_bar REAL,

    -- Environmental measurements (scaled)
    ortam_sicakligi_c REAL,
    ortam_nem_percentage REAL,
    sogutma_sivi_sicakligi_c REAL,
    hidrolik_yag_sicakligi_c REAL,

    -- Vibration measurements
    ivme_olcer_x REAL,
    ivme_olcer_y REAL,
    ivme_olcer_z REAL,
    ivme_olcer_x_hz REAL,
    ivme_olcer_y_hz REAL,
    ivme_olcer_z_hz REAL,
    max_titresim_hz REAL,

    -- State information
    testere_durumu INTEGER,
    alarm_status INTEGER,
    alarm_bilgisi TEXT,

    -- Identification
    makine_id INTEGER,
    serit_id INTEGER,

    -- Material information
    malzeme_cinsi TEXT,
    malzeme_sertlik TEXT,
    kesit_yapisi TEXT,
    malzeme_a_mm INTEGER,
    malzeme_b_mm INTEGER,
    malzeme_c_mm INTEGER,
    malzeme_d_mm INTEGER,
    malzeme_genisligi REAL,

    -- Band information
    serit_tip TEXT,
    serit_marka TEXT,
    serit_malz TEXT,
    serit_dis_mm INTEGER,

    -- Statistics
    kesilen_parca_adeti INTEGER,

    -- Power measurement (decoded IEEE754)
    guc_kwh REAL,

    -- ML control outputs
    ml_output REAL,
    kesme_hizi_degisim REAL,
    inme_hizi_degisim REAL,
    torque_guard_active INTEGER,

    -- Controller type
    controller_type TEXT,

    -- Anomaly detection
    anomalies TEXT
);

CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_sensor_kesim_id ON sensor_data(kesim_id);
CREATE INDEX IF NOT EXISTS idx_sensor_testere_durumu ON sensor_data(testere_durumu);

-- Cutting sessions table
CREATE TABLE IF NOT EXISTS cutting_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kesim_id INTEGER UNIQUE NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    controller_type TEXT,
    start_height_mm REAL,
    end_height_mm REAL,
    duration_ms INTEGER,
    data_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sessions_kesim_id ON cutting_sessions(kesim_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON cutting_sessions(start_time);
"""

# log.db - System logs
SCHEMA_LOG_DB = """
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level TEXT,
    logger_name TEXT,
    message TEXT,
    exception TEXT
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_logger ON system_logs(logger_name);
"""

# ml.db - ML predictions
SCHEMA_ML_DB = """
CREATE TABLE IF NOT EXISTS ml_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Input features
    akim_input REAL,
    sapma_input REAL,
    kesme_hizi_input REAL,
    inme_hizi_input REAL,

    -- Output speeds
    yeni_kesme_hizi REAL,
    yeni_inme_hizi REAL,

    -- ML outputs
    katsayi REAL,
    ml_output REAL
);

CREATE INDEX IF NOT EXISTS idx_ml_timestamp ON ml_predictions(timestamp);
"""

# anomaly.db - Anomaly detection tracking
SCHEMA_ANOMALY_DB = """
-- Individual anomaly events
CREATE TABLE IF NOT EXISTS anomaly_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sensor_name TEXT NOT NULL,
    sensor_value REAL,
    detection_method TEXT,
    kesim_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON anomaly_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_anomaly_sensor ON anomaly_events(sensor_name);
CREATE INDEX IF NOT EXISTS idx_anomaly_kesim ON anomaly_events(kesim_id);

-- Reset history (tracks when anomalies were cleared)
CREATE TABLE IF NOT EXISTS anomaly_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reset_time TEXT NOT NULL,
    reset_by TEXT DEFAULT 'user'
);

CREATE INDEX IF NOT EXISTS idx_reset_time ON anomaly_resets(reset_time);
"""

# Schema mapping
SCHEMAS = {
    'raw': SCHEMA_RAW_DB,
    'total': SCHEMA_TOTAL_DB,
    'log': SCHEMA_LOG_DB,
    'ml': SCHEMA_ML_DB,
    'anomaly': SCHEMA_ANOMALY_DB
}
