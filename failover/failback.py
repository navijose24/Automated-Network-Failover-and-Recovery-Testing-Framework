"""Failback Mechanism: primary path stability verification and safe route restoration."""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from config import (
    NS_CLIENT, IP_CONFIG, FAILBACK_STABILITY_THRESHOLD, AUTO_FAILBACK_DEFAULT
)
from network.executor import run_cmd
from network.routing import replace_route, get_active_route
from monitoring.connectivity import test_interface_probe

logger = logging.getLogger("failback_controller")

class FailbackController:
    """Monitors primary path recovery, confirms link stability, 
    and handles automatic or manual failback.
    """
    
    def __init__(self, stability_threshold: int = FAILBACK_STABILITY_THRESHOLD, auto_failback: bool = AUTO_FAILBACK_DEFAULT):
        self.stability_threshold = stability_threshold
        self.auto_failback = auto_failback
        
        self.primary_consecutive_success = 0
        self.primary_is_stable = False
        self.failback_in_progress = False
        self.failback_completed = False
        
        self.primary_restored_time: Optional[float] = None
        self.failback_time: Optional[float] = None
        self.failback_duration_ms: Optional[float] = None
        
        self.lock = threading.Lock()
        self.checker_thread: Optional[threading.Thread] = None
        self.running = False
        
        self.event_listeners: List[Callable[[str, Dict[str, Any]], None]] = []

    def register_listener(self, cb: Callable[[str, Dict[str, Any]], None]):
        """Register listener for failback lifecycle events."""
        if cb not in self.event_listeners:
            self.event_listeners.append(cb)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all registered listeners."""
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception as ex:
                logger.error(f"Error in failback listener: {ex}")

    def set_auto_failback(self, enabled: bool):
        """Enable or disable automatic failback."""
        with self.lock:
            self.auto_failback = enabled
            logger.info(f"Auto-failback set to: {enabled}")

    def notify_primary_restored(self, restored_time: float):
        """Notification that primary hardware/scenario has been restored."""
        with self.lock:
            self.primary_restored_time = restored_time
            self.primary_consecutive_success = 0
            self.primary_is_stable = False
            self.failback_completed = False

    def check_primary_health(self) -> bool:
        """Probe the primary interface to test if primary path is currently reachable."""
        return test_interface_probe(dev=IP_CONFIG["client_pri_dev"], target_ip=IP_CONFIG["target_ip"])

    def process_health_tick(self, is_failed_over: bool):
        """Periodic check called while in failover state to evaluate primary stability."""
        if not is_failed_over:
            return

        is_up = self.check_primary_health()
        
        with self.lock:
            if is_up:
                self.primary_consecutive_success += 1
                logger.debug(f"Primary probe successful: {self.primary_consecutive_success}/{self.stability_threshold}")
                
                if self.primary_consecutive_success >= self.stability_threshold and not self.primary_is_stable:
                    self.primary_is_stable = True
                    logger.info("Primary path confirmed STABLE after consecutive successful checks.")
                    
                    stable_event = {
                        "timestamp": time.time(),
                        "consecutive_success": self.primary_consecutive_success,
                        "auto_failback_enabled": self.auto_failback
                    }
                    self._emit_event("PRIMARY_STABLE", stable_event)
                    
                    if self.auto_failback and not self.failback_completed:
                        self._execute_failback()
            else:
                self.primary_consecutive_success = 0
                self.primary_is_stable = False

    def execute_failback(self) -> Dict[str, Any]:
        """Manually trigger failback to primary route."""
        with self.lock:
            return self._execute_failback()

    def _execute_failback(self) -> Dict[str, Any]:
        """Restore primary route preference and demote backup route metric."""
        logger.info("Executing failback: restoring primary route preference...")
        t_start = time.time()
        t_start_mono = time.monotonic()
        
        from network.routing import delete_route
        
        # 1. Remove the failover-promoted metric 50 route
        delete_route(
            netns=NS_CLIENT,
            destination=IP_CONFIG["target_ip"],
            gateway=IP_CONFIG["backup_gw"],
            dev=IP_CONFIG["client_bak_dev"],
            metric=IP_CONFIG["metric_active_failover"]
        )
        
        # 2. Restore primary route with metric 100
        ok_pri = replace_route(
            netns=NS_CLIENT,
            destination=IP_CONFIG["target_ip"],
            gateway=IP_CONFIG["primary_gw"],
            dev=IP_CONFIG["client_pri_dev"],
            metric=IP_CONFIG["metric_primary"]
        )
        
        # 3. Reset backup route with metric 200
        ok_bak = replace_route(
            netns=NS_CLIENT,
            destination=IP_CONFIG["target_ip"],
            gateway=IP_CONFIG["backup_gw"],
            dev=IP_CONFIG["client_bak_dev"],
            metric=IP_CONFIG["metric_backup"]
        )
        
        # Flush route cache
        run_cmd(f"ip -n {NS_CLIENT} route flush cache")
        
        # 4. Verify destination reachability on primary
        verified = test_interface_probe(dev=IP_CONFIG["client_pri_dev"], target_ip=IP_CONFIG["target_ip"])
        t_end = time.time()
        t_end_mono = time.monotonic()
        
        duration_ms = max(0.0, round((t_end_mono - t_start_mono) * 1000, 2))
        self.failback_time = t_end
        self.failback_duration_ms = duration_ms
        self.failback_completed = verified
        
        if verified:
            logger.info(f"FAILBACK COMPLETED successfully in {duration_ms} ms. Traffic routed via PRIMARY.")
            event_data = {
                "timestamp": t_end,
                "duration_ms": duration_ms,
                "active_path": "PRIMARY",
                "active_dev": IP_CONFIG["client_pri_dev"],
                "active_gw": IP_CONFIG["primary_gw"]
            }
            self._emit_event("FAILBACK_COMPLETED", event_data)
            return {"success": True, "data": event_data}
        else:
            logger.error("Failback routes applied but primary verification failed!")
            self._emit_event("FAILBACK_FAILED", {"reason": "Verification probe on primary interface failed."})
            return {"success": False, "error": "Primary verification probe failed."}

    def reset_state(self):
        """Reset internal failback state."""
        with self.lock:
            self.primary_consecutive_success = 0
            self.primary_is_stable = False
            self.failback_in_progress = False
            self.failback_completed = False
            self.primary_restored_time = None
            self.failback_time = None
            self.failback_duration_ms = None

    def get_status(self) -> Dict[str, Any]:
        """Return current status of failback controller."""
        with self.lock:
            return {
                "auto_failback": self.auto_failback,
                "primary_is_stable": self.primary_is_stable,
                "primary_consecutive_success": self.primary_consecutive_success,
                "stability_threshold": self.stability_threshold,
                "failback_completed": self.failback_completed,
                "failback_duration_ms": self.failback_duration_ms
            }
