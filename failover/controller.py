"""Automatic Failover Controller: threshold-based failure detection and backup route activation."""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from config import (
    NS_CLIENT, IP_CONFIG, FAILURE_THRESHOLD
)
from network.executor import run_cmd
from network.routing import replace_route, get_active_route
from monitoring.connectivity import ProbeResult, test_interface_probe

logger = logging.getLogger("failover_controller")

class FailoverController:
    """Monitors incoming probes, detects failures via consecutive thresholds, 
    and enacts kernel route transitions to the backup path.
    """
    
    def __init__(self, failure_threshold: int = FAILURE_THRESHOLD):
        self.failure_threshold = failure_threshold
        self.consecutive_failures = 0
        self.lock = threading.Lock()
        
        # State tracking
        self.in_failure = False
        self.failed_over = False
        self.failure_start_time: Optional[float] = None
        self.failure_start_mono: Optional[float] = None
        self.detection_time: Optional[float] = None
        self.detection_mono: Optional[float] = None
        self.restored_time: Optional[float] = None
        self.restored_mono: Optional[float] = None
        
        self.active_path = "PRIMARY"
        self.last_failed_interface: Optional[str] = None
        self.active_scenario: Optional[str] = None
        
        # Performance metrics for current event
        self.detection_time_ms: Optional[float] = None
        self.recovery_time_ms: Optional[float] = None
        self.failover_success = False
        
        # Event callbacks
        self.event_listeners: List[Callable[[str, Dict[str, Any]], None]] = []

    def register_listener(self, cb: Callable[[str, Dict[str, Any]], None]):
        """Register callback for failover lifecycle events."""
        if cb not in self.event_listeners:
            self.event_listeners.append(cb)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit lifecycle event to all registered listeners."""
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception as ex:
                logger.error(f"Error in failover listener: {ex}")

    def notify_failure_triggered(self, scenario_id: str, start_time: float, affected_dev: str, start_mono: Optional[float] = None):
        """Notified by FailureEngine when a scenario begins, establishing the ground-truth T0."""
        with self.lock:
            self.failure_start_time = start_time
            self.failure_start_mono = start_mono or time.monotonic()
            self.active_scenario = scenario_id
            self.last_failed_interface = affected_dev
            self.consecutive_failures = 0
            self.in_failure = False
            self.failed_over = False
            self.detection_time = None
            self.detection_mono = None
            self.restored_time = None
            self.restored_mono = None
            self.detection_time_ms = None
            self.recovery_time_ms = None
            self.failover_success = False

    def process_probe(self, probe: ProbeResult):
        """Called on every probe emitted by PacketMonitor to evaluate health and thresholds."""
        with self.lock:
            if not probe.success:
                self.consecutive_failures += 1
                logger.debug(f"Consecutive failures: {self.consecutive_failures}/{self.failure_threshold}")
                
                # If ground-truth failure_start_time wasn't explicitly set by failure engine,
                # mark failure start at the first missed packet
                if self.failure_start_time is None and self.consecutive_failures == 1:
                    self.failure_start_time = probe.timestamp
                    self.failure_start_mono = time.monotonic()

                # Check if threshold reached to confirm failure
                if self.consecutive_failures >= self.failure_threshold and not self.in_failure and not self.failed_over:
                    self._handle_failure_detected(probe)
            else:
                # Successful probe
                if self.in_failure and self.failed_over and self.restored_time is None:
                    # Recovery confirmed!
                    self._handle_recovery_confirmed(probe)
                    
                # Reset consecutive failure counter on successful probe
                self.consecutive_failures = 0

    def _handle_failure_detected(self, probe: ProbeResult):
        """Threshold reached: declare failure and execute failover."""
        detect_t = time.time()
        detect_mono = time.monotonic()
        self.in_failure = True
        self.detection_time = detect_t
        self.detection_mono = detect_mono
        
        t0_mono = self.failure_start_mono or detect_mono
        self.detection_time_ms = max(0.0, round((detect_mono - t0_mono) * 1000, 2))
        t0_wall = self.failure_start_time or detect_t
        
        logger.warning(
            f"NETWORK FAILURE DETECTED after {self.consecutive_failures} consecutive missed probes. "
            f"Detection time: {self.detection_time_ms} ms"
        )
        
        detect_event = {
            "timestamp": detect_t,
            "failure_start_time": t0_wall,
            "detection_time_ms": self.detection_time_ms,
            "scenario": self.active_scenario or "UNKNOWN",
            "failed_interface": self.last_failed_interface or probe.active_interface,
            "missed_probes": self.consecutive_failures
        }
        self._emit_event("FAILURE_DETECTED", detect_event)

        # Trigger automatic failover
        self._activate_failover()

    def _activate_failover(self) -> bool:
        """Enact route modification to prioritize backup path and verify connectivity."""
        logger.info("Activating backup route in Linux kernel routing table...")
        
        activate_t = time.time()
        self._emit_event("FAILOVER_ACTIVATING", {
            "timestamp": activate_t,
            "backup_dev": IP_CONFIG["client_bak_dev"],
            "backup_gateway": IP_CONFIG["backup_gw"]
        })

        # Step 1: Promote backup route priority by lowering its metric to 50 (lower than primary's 100)
        # Linux Command: ip -n ns_client route replace 10.50.0.1 via 10.0.2.1 dev veth_c_b metric 50
        route_ok = replace_route(
            netns=NS_CLIENT,
            destination=IP_CONFIG["target_ip"],
            gateway=IP_CONFIG["backup_gw"],
            dev=IP_CONFIG["client_bak_dev"],
            metric=IP_CONFIG["metric_active_failover"]
        )
        
        # Flush route cache
        run_cmd(f"ip -n {NS_CLIENT} route flush cache")

        if not route_ok:
            logger.error("Failed to replace route to backup in kernel table!")
            self._emit_event("FAILOVER_FAILED", {"reason": "Kernel route replacement command failed."})
            return False

        # Step 2: Actively verify destination reachability through backup interface
        reachable = test_interface_probe(dev=IP_CONFIG["client_bak_dev"], target_ip=IP_CONFIG["target_ip"])
        
        if reachable:
            restored_t = time.time()
            restored_mono = time.monotonic()
            self.failed_over = True
            self.active_path = "BACKUP"
            self.restored_time = restored_t
            self.restored_mono = restored_mono
            self.failover_success = True
            
            t0_mono = self.failure_start_mono or self.detection_mono or restored_mono
            self.recovery_time_ms = max(0.0, round((restored_mono - t0_mono) * 1000, 2))
            
            logger.info(
                f"FAILOVER RESTORED via BACKUP! Recovery time: {self.recovery_time_ms} ms "
                f"(Detection: {self.detection_time_ms} ms)"
            )
            
            success_event = {
                "timestamp": restored_t,
                "recovery_time_ms": self.recovery_time_ms,
                "detection_time_ms": self.detection_time_ms,
                "active_path": "BACKUP",
                "active_device": IP_CONFIG["client_bak_dev"],
                "active_gateway": IP_CONFIG["backup_gw"]
            }
            self._emit_event("FAILOVER_COMPLETED", success_event)
            return True
        else:
            logger.error("Failover route applied but destination is unreachable via backup interface!")
            self._emit_event("FAILOVER_FAILED", {"reason": "Backup interface verification ping failed."})
            return False

    def _handle_recovery_confirmed(self, probe: ProbeResult):
        """Confirm probe successfully traveling through recovered path."""
        self.in_failure = False
        logger.info(f"Steady-state probe confirmed on path {probe.active_path} (RTT: {probe.rtt_ms} ms)")

    def manual_failover(self) -> Dict[str, Any]:
        """Manually trigger failover to backup route."""
        with self.lock:
            self.failure_start_time = time.time()
            self.failure_start_mono = time.monotonic()
            ok = self._activate_failover()
            return {
                "success": ok,
                "active_path": self.active_path,
                "recovery_time_ms": self.recovery_time_ms
            }

    def reset_state(self):
        """Reset internal detection state for a new test session."""
        with self.lock:
            self.consecutive_failures = 0
            self.in_failure = False
            self.failed_over = False
            self.failure_start_time = None
            self.failure_start_mono = None
            self.detection_time = None
            self.detection_mono = None
            self.restored_time = None
            self.restored_mono = None
            self.detection_time_ms = None
            self.recovery_time_ms = None
            self.failover_success = False
            self.active_path = "PRIMARY"
            self.last_failed_interface = None
            self.active_scenario = None

    def get_status(self) -> Dict[str, Any]:
        """Return current status of failover controller."""
        with self.lock:
            return {
                "in_failure": self.in_failure,
                "failed_over": self.failed_over,
                "active_path": self.active_path,
                "consecutive_failures": self.consecutive_failures,
                "failure_threshold": self.failure_threshold,
                "detection_time_ms": self.detection_time_ms,
                "recovery_time_ms": self.recovery_time_ms,
                "failover_success": self.failover_success,
                "active_scenario": self.active_scenario
            }
