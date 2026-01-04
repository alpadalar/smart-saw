"""
Database schema definitions for SQLite databases.
"""

# raw.db - Raw sensor data
SCHEMA_RAW_DB = """
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Motor measurements
    serit_motor_akim_a REAL,
    serit_motor_tork_percentage REAL,
    inme_motor_akim_a REAL,
    inme_motor_tork_percentage REAL,

    -- Speed values
    serit_kesme_hizi REAL,
    serit_inme_hizi REAL,

    -- Mechanical measurements
    kafa_yuksekligi_mm REAL,
    serit_sapmasi REAL,
    serit_gerginligi_bar REAL,
    mengene_basinc_bar REAL,

    -- Environmental measurements
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

    -- Statistics
    kesilen_parca_adeti INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_sensor_cutting_state ON sensor_data(testere_durumu);
CREATE INDEX IF NOT EXISTS idx_sensor_machine_id ON sensor_data(makine_id);
"""

# total.db - Processed data
SCHEMA_TOTAL_DB = """
CREATE TABLE IF NOT EXISTS processed_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- ML outputs
    ml_output REAL,
    kesme_hizi_degisim REAL,
    inme_hizi_degisim REAL,
    torque_guard_active INTEGER,

    -- Session tracking
    cutting_session_id TEXT,

    -- Anomaly detection
    anomalies TEXT,  -- JSON string

    -- Controller type
    controller_type TEXT
);

CREATE INDEX IF NOT EXISTS idx_processed_timestamp ON processed_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_processed_session ON processed_data(cutting_session_id);

CREATE TABLE IF NOT EXISTS cutting_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    controller_type TEXT,
    data_count INTEGER DEFAULT 0,
    duration_ms INTEGER
);

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

# Schema mapping
SCHEMAS = {
    'raw': SCHEMA_RAW_DB,
    'total': SCHEMA_TOTAL_DB,
    'log': SCHEMA_LOG_DB,
    'ml': SCHEMA_ML_DB
}
