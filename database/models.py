"""Data access layer and repository functions for experiment records."""

import json
import time
from typing import Dict, Any, List, Optional
from database.db import get_connection

def create_session(
    session_name: str,
    scenario_name: str = "normal_operation",
    failback_enabled: bool = False,
    config_dict: Optional[Dict[str, Any]] = None
) -> int:
    """Create a new experiment session and return its ID."""
    conn = get_connection()
    now = time.time()
    cfg_json = json.dumps(config_dict or {})
    
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO sessions (session_name, scenario_name, start_time, status, failback_enabled, config_json)
            VALUES (?, ?, ?, 'RUNNING', ?, ?)
            """,
            (session_name, scenario_name, now, 1 if failback_enabled else 0, cfg_json)
        )
        session_id = cursor.lastrowid
    conn.close()
    return session_id

def end_session(session_id: int, status: str = "COMPLETED"):
    """Mark a test session as ended."""
    conn = get_connection()
    now = time.time()
    with conn:
        conn.execute(
            "UPDATE sessions SET end_time = ?, status = ? WHERE id = ?",
            (now, status, session_id)
        )
    conn.close()

def log_probe(session_id: int, probe_dict: Dict[str, Any]):
    """Insert an ICMP probe measurement."""
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO probe_records 
            (session_id, timestamp, sequence_num, target_ip, success, rtt_ms, active_interface, active_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                probe_dict["timestamp"],
                probe_dict.get("sequence_num") or probe_dict.get("seq", 0),
                probe_dict.get("target_ip", "10.50.0.1"),
                1 if probe_dict["success"] else 0,
                probe_dict.get("rtt_ms"),
                probe_dict.get("active_interface") or probe_dict.get("active_dev"),
                probe_dict.get("active_path", "UNKNOWN")
            )
        )
    conn.close()

def log_event(
    session_id: int,
    event_type: str,
    scenario: Optional[str] = None,
    affected_interface: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    timestamp: Optional[float] = None
):
    """Insert a network lifecycle event."""
    conn = get_connection()
    ts = timestamp or time.time()
    details_str = json.dumps(details or {})
    with conn:
        conn.execute(
            """
            INSERT INTO network_events (session_id, timestamp, event_type, scenario, affected_interface, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, ts, event_type, scenario, affected_interface, details_str)
        )
    conn.close()

def save_metrics(session_id: int, metrics: Dict[str, Any]):
    """Save computed performance and recovery metrics for a session."""
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO session_metrics 
            (session_id, failure_detection_time_ms, failover_recovery_time_ms, failback_recovery_time_ms,
             packet_loss_percent, availability_percent, avg_latency_ms, min_latency_ms, max_latency_ms,
             total_probes, successful_probes, failed_probes, failover_success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                metrics.get("failure_detection_time_ms"),
                metrics.get("failover_recovery_time_ms"),
                metrics.get("failback_recovery_time_ms"),
                metrics.get("packet_loss_percent", 0.0),
                metrics.get("availability_percent", 100.0),
                metrics.get("avg_latency_ms", 0.0),
                metrics.get("min_latency_ms", 0.0),
                metrics.get("max_latency_ms", 0.0),
                metrics.get("total_probes", 0),
                metrics.get("successful_probes", 0),
                metrics.get("failed_probes", 0),
                1 if metrics.get("failover_success") else 0
            )
        )
    conn.close()

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    """Fetch session details by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent experiment sessions with their metrics joined."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.*, m.failure_detection_time_ms, m.failover_recovery_time_ms, 
               m.packet_loss_percent, m.availability_percent, m.avg_latency_ms, m.failover_success
        FROM sessions s
        LEFT JOIN session_metrics m ON s.id = m.session_id
        ORDER BY s.id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_probes(session_id: int) -> List[Dict[str, Any]]:
    """Retrieve all ICMP probes for a given session."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM probe_records WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_events(session_id: int) -> List[Dict[str, Any]]:
    """Retrieve all lifecycle events for a given session."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM network_events WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_metrics(session_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve computed metrics for a given session."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM session_metrics WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_aggregate_stats() -> Dict[str, Any]:
    """Retrieve high-level experiment statistics across all sessions."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT 
            COUNT(DISTINCT s.id) AS total_sessions,
            SUM(CASE WHEN m.failover_success = 1 THEN 1 ELSE 0 END) AS successful_failovers,
            SUM(CASE WHEN m.failover_success = 0 THEN 1 ELSE 0 END) AS failed_failovers,
            AVG(m.failure_detection_time_ms) AS avg_detection_ms,
            AVG(m.failover_recovery_time_ms) AS avg_recovery_ms,
            AVG(m.packet_loss_percent) AS avg_loss_pct,
            AVG(m.avg_latency_ms) AS overall_avg_latency
        FROM sessions s
        LEFT JOIN session_metrics m ON s.id = m.session_id
        """
    ).fetchone()
    conn.close()
    
    total = row["total_sessions"] or 0
    succ = row["successful_failovers"] or 0
    fail = row["failed_failovers"] or 0
    
    return {
        "total_sessions": total,
        "successful_failovers": succ,
        "failed_failovers": fail,
        "avg_detection_ms": round(row["avg_detection_ms"] or 0.0, 2),
        "avg_recovery_ms": round(row["avg_recovery_ms"] or 0.0, 2),
        "avg_loss_pct": round(row["avg_loss_pct"] or 0.0, 2),
        "overall_avg_latency": round(row["overall_avg_latency"] or 0.0, 3)
    }
