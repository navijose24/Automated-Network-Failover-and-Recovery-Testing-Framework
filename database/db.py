"""SQLite Database connection manager and schema initializer."""

import sqlite3
import logging
from config import DATABASE_PATH

logger = logging.getLogger("database")

def get_connection() -> sqlite3.Connection:
    """Return an SQLite connection with Row factory and WAL mode for high concurrency."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def init_db():
    """Create all required tables if they do not exist."""
    conn = get_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            scenario_name TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL,
            status TEXT NOT NULL DEFAULT 'RUNNING',
            failback_enabled INTEGER NOT NULL DEFAULT 0,
            config_json TEXT
        );

        CREATE TABLE IF NOT EXISTS probe_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            sequence_num INTEGER NOT NULL,
            target_ip TEXT NOT NULL,
            success INTEGER NOT NULL,
            rtt_ms REAL,
            active_interface TEXT,
            active_path TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_probe_session ON probe_records(session_id);

        CREATE TABLE IF NOT EXISTS network_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            event_type TEXT NOT NULL,
            scenario TEXT,
            affected_interface TEXT,
            details TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_event_session ON network_events(session_id);

        CREATE TABLE IF NOT EXISTS session_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL UNIQUE,
            failure_detection_time_ms REAL,
            failover_recovery_time_ms REAL,
            failback_recovery_time_ms REAL,
            packet_loss_percent REAL,
            availability_percent REAL,
            avg_latency_ms REAL,
            min_latency_ms REAL,
            max_latency_ms REAL,
            total_probes INTEGER,
            successful_probes INTEGER,
            failed_probes INTEGER,
            failover_success INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        );
        """)
    conn.close()
    logger.info("Database schema initialized successfully.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("Database initialization complete.")
