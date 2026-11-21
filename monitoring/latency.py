"""Latency tracking and statistical calculations."""

from typing import List, Optional, Dict, Any
import statistics

class LatencyTracker:
    """Tracks latency measurements and calculates real-time summary statistics."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.rtt_history: List[float] = []
        self.all_rtt: List[float] = []

    def record(self, rtt_ms: Optional[float]):
        """Record a new latency measurement."""
        if rtt_ms is not None and rtt_ms >= 0:
            self.rtt_history.append(rtt_ms)
            self.all_rtt.append(rtt_ms)
            if len(self.rtt_history) > self.window_size:
                self.rtt_history.pop(0)

    def get_summary(self) -> Dict[str, Any]:
        """Compute average, min, max, and jitter over recorded latency values."""
        if not self.all_rtt:
            return {
                "avg_latency": 0.0,
                "min_latency": 0.0,
                "max_latency": 0.0,
                "jitter": 0.0,
                "samples": 0
            }

        avg_lat = statistics.mean(self.all_rtt)
        min_lat = min(self.all_rtt)
        max_lat = max(self.all_rtt)
        jitter = statistics.stdev(self.all_rtt) if len(self.all_rtt) > 1 else 0.0

        return {
            "avg_latency": round(avg_lat, 3),
            "min_latency": round(min_lat, 3),
            "max_latency": round(max_lat, 3),
            "jitter": round(jitter, 3),
            "samples": len(self.all_rtt)
        }

    def reset(self):
        """Reset all tracked history."""
        self.rtt_history.clear()
        self.all_rtt.clear()
