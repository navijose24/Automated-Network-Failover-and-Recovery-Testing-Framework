"""Report Generator: generates downloadable CSV reports and Pandas analytics summaries."""

import io
import pandas as pd
from typing import Dict, Any, List, Optional
from database.models import (
    get_session, get_session_probes, get_session_events,
    get_session_metrics, get_all_sessions
)

class ReportGenerator:
    """Produces structured CSV and DataFrame outputs for academic evaluation and exports."""

    @staticmethod
    def generate_session_probes_csv(session_id: int) -> str:
        """Export raw probe telemetry for a session to CSV."""
        probes = get_session_probes(session_id)
        if not probes:
            return "session_id,sequence_num,timestamp,target_ip,success,rtt_ms,active_interface,active_path\n"
            
        df = pd.DataFrame(probes)
        # Drop internal id column if present
        if "id" in df.columns:
            df = df.drop(columns=["id"])
            
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def generate_session_summary_csv(session_id: int) -> str:
        """Export comprehensive summary of a single session to CSV."""
        session = get_session(session_id)
        metrics = get_session_metrics(session_id)
        
        if not session:
            return "error\nSession not found\n"
            
        summary_dict = {
            "session_id": [session["id"]],
            "session_name": [session["session_name"]],
            "scenario": [session["scenario_name"]],
            "start_time": [session["start_time"]],
            "end_time": [session.get("end_time")],
            "status": [session["status"]],
            "failback_enabled": [bool(session.get("failback_enabled"))],
            "failure_detection_time_ms": [metrics.get("failure_detection_time_ms") if metrics else None],
            "failover_recovery_time_ms": [metrics.get("failover_recovery_time_ms") if metrics else None],
            "failback_recovery_time_ms": [metrics.get("failback_recovery_time_ms") if metrics else None],
            "packet_loss_percent": [metrics.get("packet_loss_percent") if metrics else 0.0],
            "availability_percent": [metrics.get("availability_percent") if metrics else 100.0],
            "avg_latency_ms": [metrics.get("avg_latency_ms") if metrics else 0.0],
            "min_latency_ms": [metrics.get("min_latency_ms") if metrics else 0.0],
            "max_latency_ms": [metrics.get("max_latency_ms") if metrics else 0.0],
            "total_probes": [metrics.get("total_probes") if metrics else 0],
            "successful_probes": [metrics.get("successful_probes") if metrics else 0],
            "failed_probes": [metrics.get("failed_probes") if metrics else 0],
            "failover_success": [bool(metrics.get("failover_success")) if metrics else False]
        }
        df = pd.DataFrame(summary_dict)
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def generate_all_sessions_csv() -> str:
        """Export all recorded sessions and their metrics as a comparison CSV."""
        sessions = get_all_sessions(limit=500)
        if not sessions:
            return "session_id,session_name,scenario_name,status,avg_latency_ms,packet_loss_percent,recovery_time_ms\n"
            
        df = pd.DataFrame(sessions)
        if "id" in df.columns:
            df = df.rename(columns={"id": "session_id"})
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def get_scenario_comparison_summary() -> List[Dict[str, Any]]:
        """Compute aggregated averages grouped by scenario using Pandas."""
        sessions = get_all_sessions(limit=500)
        if not sessions:
            return []
            
        df = pd.DataFrame(sessions)
        if df.empty or "scenario_name" not in df.columns:
            return []

        # Convert numeric columns
        cols = [
            "failure_detection_time_ms", "failover_recovery_time_ms", 
            "packet_loss_percent", "availability_percent", "avg_latency_ms"
        ]
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        grouped = df.groupby("scenario_name").agg({
            "id": "count",
            "failure_detection_time_ms": "mean",
            "failover_recovery_time_ms": "mean",
            "packet_loss_percent": "mean",
            "availability_percent": "mean",
            "avg_latency_ms": "mean"
        }).reset_index()

        grouped.rename(columns={"id": "session_count"}, inplace=True)
        # Round numerical values
        for c in ["failure_detection_time_ms", "failover_recovery_time_ms", "packet_loss_percent", "availability_percent", "avg_latency_ms"]:
            if c in grouped.columns:
                grouped[c] = grouped[c].round(2)

        # Convert NaN → None so Flask's tojson filter serializes cleanly
        records = grouped.to_dict(orient="records")
        return [{k: (None if (v != v) else v) for k, v in row.items()} for row in records]
