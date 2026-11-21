"""Recovery Analyzer: computes end-to-end metrics and performance comparisons."""

from typing import List, Dict, Any, Optional
from analysis.metrics import (
    calculate_failure_detection_time,
    calculate_failover_recovery_time,
    calculate_packet_loss_percentage,
    calculate_network_availability,
    calculate_average_latency,
    calculate_failover_success_rate
)

class RecoveryAnalyzer:
    """Aggregates experiment telemetry and calculates the 6 formal resilience metrics."""

    @staticmethod
    def analyze_session(
        probes: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        failover_success: bool = True
    ) -> Dict[str, Any]:
        """Compute metrics for a session given its probe history and lifecycle events."""
        total_probes = len(probes)
        successful_probes = [p for p in probes if p.get("success")]
        failed_probes = [p for p in probes if not p.get("success")]
        
        loss_pct = calculate_packet_loss_percentage(total_probes, len(failed_probes))
        avail_pct = calculate_network_availability(total_probes, len(successful_probes))
        
        rtts = [p["rtt_ms"] for p in successful_probes if p.get("rtt_ms") is not None]
        avg_rtt = calculate_average_latency(rtts)
        min_rtt = round(min(rtts), 3) if rtts else 0.0
        max_rtt = round(max(rtts), 3) if rtts else 0.0

        # Find lifecycle event timestamps
        t_failure_start: Optional[float] = None
        t_failure_detected: Optional[float] = None
        t_failover_restored: Optional[float] = None
        t_primary_restored: Optional[float] = None
        t_failback_restored: Optional[float] = None

        for evt in events:
            etype = evt.get("event_type")
            ts = evt.get("timestamp")
            if etype == "FAILURE_TRIGGERED" and t_failure_start is None:
                t_failure_start = ts
            elif etype == "FAILURE_DETECTED" and t_failure_detected is None:
                t_failure_detected = ts
            elif etype == "FAILOVER_COMPLETED" and t_failover_restored is None:
                t_failover_restored = ts
            elif etype == "PRIMARY_RESTORED" and t_primary_restored is None:
                t_primary_restored = ts
            elif etype == "FAILBACK_COMPLETED" and t_failback_restored is None:
                t_failback_restored = ts

        # Fallback to first failed probe timestamp if FAILURE_TRIGGERED not recorded
        if t_failure_start is None and failed_probes:
            t_failure_start = failed_probes[0].get("timestamp")

        # 1. Failure Detection Time
        detection_time_ms = None
        if t_failure_start and t_failure_detected and t_failure_detected >= t_failure_start:
            detection_time_ms = calculate_failure_detection_time(t_failure_start, t_failure_detected)

        # 2. Failover Recovery Time
        recovery_time_ms = None
        if t_failure_start and t_failover_restored and t_failover_restored >= t_failure_start:
            recovery_time_ms = calculate_failover_recovery_time(t_failure_start, t_failover_restored)

        # Failback Recovery Time
        failback_time_ms = None
        if t_primary_restored and t_failback_restored and t_failback_restored >= t_primary_restored:
            failback_time_ms = round((t_failback_restored - t_primary_restored) * 1000, 2)

        return {
            "total_probes": total_probes,
            "successful_probes": len(successful_probes),
            "failed_probes": len(failed_probes),
            "packet_loss_percent": loss_pct,
            "availability_percent": avail_pct,
            "avg_latency_ms": avg_rtt,
            "min_latency_ms": min_rtt,
            "max_latency_ms": max_rtt,
            "failure_detection_time_ms": detection_time_ms,
            "failover_recovery_time_ms": recovery_time_ms,
            "failback_recovery_time_ms": failback_time_ms,
            "failover_success": failover_success,
            "failover_success_rate": 100.0 if failover_success else 0.0
        }
