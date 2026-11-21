"""Background Packet Monitor: continuous probe generation, metrics aggregation, and event dispatch."""

import threading
import time
import logging
from typing import List, Callable, Dict, Any, Optional
from monitoring.connectivity import send_probe, ProbeResult
from monitoring.latency import LatencyTracker
from config import PROBE_INTERVAL, PROBE_TIMEOUT

logger = logging.getLogger("packet_monitor")

class PacketMonitor:
    """Continuously probes the destination network and maintains real-time telemetry."""
    
    def __init__(self, probe_interval: float = PROBE_INTERVAL, timeout: float = PROBE_TIMEOUT):
        self.probe_interval = probe_interval
        self.timeout = timeout
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        self.seq_num = 0
        self.total_transmitted = 0
        self.total_received = 0
        self.total_lost = 0
        
        self.latency_tracker = LatencyTracker()
        self.recent_probes: List[Dict[str, Any]] = []
        self.max_recent_probes = 100
        
        self.current_active_path = "UNKNOWN"
        self.current_active_dev = "unknown"
        self.last_probe_status = False
        
        # Callbacks registered to receive probe events (e.g., Failover Controller, DB)
        self.callbacks: List[Callable[[ProbeResult], None]] = []

    def register_callback(self, cb: Callable[[ProbeResult], None]):
        """Register a callback function to be invoked on every probe result."""
        with self.lock:
            if cb not in self.callbacks:
                self.callbacks.append(cb)

    def unregister_callback(self, cb: Callable[[ProbeResult], None]):
        """Unregister a callback function."""
        with self.lock:
            if cb in self.callbacks:
                self.callbacks.remove(cb)

    def start(self):
        """Start the background monitoring thread."""
        with self.lock:
            if self.running:
                return
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("Packet monitor started.")

    def stop(self):
        """Stop the background monitoring thread."""
        with self.lock:
            self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        logger.info("Packet monitor stopped.")

    def reset_stats(self):
        """Reset all counters and telemetry."""
        with self.lock:
            self.seq_num = 0
            self.total_transmitted = 0
            self.total_received = 0
            self.total_lost = 0
            self.latency_tracker.reset()
            self.recent_probes.clear()
            self.current_active_path = "UNKNOWN"
            self.last_probe_status = False

    def _run_loop(self):
        """Main probing loop running in background thread."""
        while self.running:
            self.seq_num += 1
            result = send_probe(sequence_num=self.seq_num, timeout=self.timeout)
            
            with self.lock:
                self.total_transmitted += 1
                if result.success:
                    self.total_received += 1
                    self.latency_tracker.record(result.rtt_ms)
                else:
                    self.total_lost += 1
                    
                self.current_active_path = result.active_path
                self.current_active_dev = result.active_interface
                self.last_probe_status = result.success
                
                probe_dict = {
                    "timestamp": result.timestamp,
                    "seq": result.sequence_num,
                    "success": result.success,
                    "rtt_ms": result.rtt_ms,
                    "active_dev": result.active_interface,
                    "active_path": result.active_path
                }
                self.recent_probes.append(probe_dict)
                if len(self.recent_probes) > self.max_recent_probes:
                    self.recent_probes.pop(0)

                callbacks_to_invoke = list(self.callbacks)

            # Invoke callbacks outside lock
            for cb in callbacks_to_invoke:
                try:
                    cb(result)
                except Exception as ex:
                    logger.error(f"Error in monitor callback: {ex}")

            time.sleep(self.probe_interval)

    def get_current_status(self) -> Dict[str, Any]:
        """Return thread-safe snapshot of network telemetry."""
        with self.lock:
            loss_pct = round((self.total_lost / self.total_transmitted * 100), 2) if self.total_transmitted > 0 else 0.0
            avail_pct = round((self.total_received / self.total_transmitted * 100), 2) if self.total_transmitted > 0 else 100.0
            lat_summary = self.latency_tracker.get_summary()
            
            return {
                "running": self.running,
                "seq_num": self.seq_num,
                "total_transmitted": self.total_transmitted,
                "total_received": self.total_received,
                "total_lost": self.total_lost,
                "packet_loss_percent": loss_pct,
                "availability_percent": avail_pct,
                "avg_latency_ms": lat_summary["avg_latency"],
                "min_latency_ms": lat_summary["min_latency"],
                "max_latency_ms": lat_summary["max_latency"],
                "jitter_ms": lat_summary["jitter"],
                "active_path": self.current_active_path,
                "active_dev": self.current_active_dev,
                "last_probe_status": self.last_probe_status,
                "recent_probes": list(self.recent_probes)
            }
