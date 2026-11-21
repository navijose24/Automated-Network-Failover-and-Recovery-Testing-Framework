"""Core performance metric formulas for network resilience and failover evaluation."""

from typing import List, Optional, Dict, Any
import statistics

def calculate_failure_detection_time(failure_start_ts: float, detection_ts: float) -> float:
    """Detection Time = Detection timestamp minus failure start timestamp (in ms)."""
    return round((detection_ts - failure_start_ts) * 1000, 2)

def calculate_failover_recovery_time(failure_start_ts: float, restored_ts: float) -> float:
    """Recovery Time = Timestamp of restored connectivity minus failure start timestamp (in ms)."""
    return round((restored_ts - failure_start_ts) * 1000, 2)

def calculate_packet_loss_percentage(total_transmitted: int, lost_packets: int) -> float:
    """Packet Loss Percentage = (Lost packets / Total transmitted packets) * 100."""
    if total_transmitted <= 0:
        return 0.0
    return round((lost_packets / total_transmitted) * 100, 2)

def calculate_network_availability(total_checks: int, successful_checks: int) -> float:
    """Network Availability = (Successful connectivity checks / Total connectivity checks) * 100."""
    if total_checks <= 0:
        return 100.0
    return round((successful_checks / total_checks) * 100, 2)

def calculate_average_latency(successful_rtt_ms_list: List[float]) -> float:
    """Average Latency = Average round-trip time of successful probes (in ms)."""
    if not successful_rtt_ms_list:
        return 0.0
    return round(statistics.mean(successful_rtt_ms_list), 3)

def calculate_failover_success_rate(total_attempts: int, successful_attempts: int) -> float:
    """Failover Success Rate = (Successful failover attempts / Total failover attempts) * 100."""
    if total_attempts <= 0:
        return 0.0
    return round((successful_attempts / total_attempts) * 100, 2)
