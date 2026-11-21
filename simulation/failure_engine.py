"""Failure Simulation Engine: schedules, triggers, and restores controlled network disruptions."""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from simulation.scenarios import SCENARIOS, apply_failure, restore_failure

logger = logging.getLogger("failure_engine")

class FailureEngine:
    """Manages active network failure injections with timestamp logging and timer-based recovery."""
    
    def __init__(self):
        self.active_scenario: Optional[str] = None
        self.failure_start_time: Optional[float] = None
        self.failure_end_time: Optional[float] = None
        self.duration_seconds: float = 0.0
        self.is_active = False
        
        self.timer_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        self.event_listeners: List[Callable[[str, Dict[str, Any]], None]] = []

    def register_listener(self, cb: Callable[[str, Dict[str, Any]], None]):
        """Register listener for failure engine events (e.g. FAILURE_TRIGGERED, FAILURE_RESTORED)."""
        if cb not in self.event_listeners:
            self.event_listeners.append(cb)

    def trigger_failure(self, scenario_id: str, duration_seconds: float = 0.0) -> Dict[str, Any]:
        """Inject a specific failure scenario into the virtual network.
        
        Args:
            scenario_id: One of the 5 defined failure scenario IDs
            duration_seconds: If > 0, automatically restore after this duration
        """
        if scenario_id not in SCENARIOS:
            raise ValueError(f"Invalid scenario: {scenario_id}")

        with self.lock:
            if self.is_active:
                return {
                    "success": False,
                    "error": f"Another failure scenario ({self.active_scenario}) is currently active."
                }
                
            success = apply_failure(scenario_id)
            if not success:
                return {
                    "success": False,
                    "error": f"Failed to apply scenario {scenario_id} via iproute2."
                }

            start_t = time.time()
            self.is_active = True
            self.active_scenario = scenario_id
            self.failure_start_time = start_t
            self.failure_end_time = None
            self.duration_seconds = duration_seconds

            event_data = {
                "scenario_id": scenario_id,
                "scenario_name": SCENARIOS[scenario_id]["name"],
                "start_time": start_t,
                "duration_seconds": duration_seconds,
                "affected_component": SCENARIOS[scenario_id]["affected_component"],
                "linux_command": SCENARIOS[scenario_id]["linux_command"]
            }

        # Dispatch FAILURE_TRIGGERED
        for listener in self.event_listeners:
            try:
                listener("FAILURE_TRIGGERED", event_data)
            except Exception as ex:
                logger.error(f"Error invoking failure listener: {ex}")

        # If a positive duration is specified, launch a background recovery timer
        if duration_seconds > 0:
            def _timed_recovery():
                time.sleep(duration_seconds)
                if self.is_active and self.active_scenario == scenario_id:
                    logger.info(f"Auto-restoring failure scenario {scenario_id} after {duration_seconds}s")
                    self.restore_failure()

            self.timer_thread = threading.Thread(target=_timed_recovery, daemon=True)
            self.timer_thread.start()

        return {
            "success": True,
            "scenario": event_data
        }

    def restore_failure(self) -> Dict[str, Any]:
        """Restore virtual network to healthy baseline state."""
        with self.lock:
            if not self.is_active:
                return {"success": True, "message": "No active failure scenario to restore."}

            scenario_id = self.active_scenario
            success = restore_failure(scenario_id)
            end_t = time.time()
            self.failure_end_time = end_t
            self.is_active = False
            self.active_scenario = None

            event_data = {
                "scenario_id": scenario_id,
                "end_time": end_t,
                "elapsed_seconds": round(end_t - (self.failure_start_time or end_t), 3)
            }

        # Dispatch FAILURE_RESTORED
        for listener in self.event_listeners:
            try:
                listener("PRIMARY_RESTORED", event_data)
            except Exception as ex:
                logger.error(f"Error invoking failure listener: {ex}")

        return {
            "success": success,
            "message": f"Scenario {scenario_id} restored.",
            "data": event_data
        }

    def get_status(self) -> Dict[str, Any]:
        """Return current status of failure simulation engine."""
        with self.lock:
            elapsed = 0.0
            if self.is_active and self.failure_start_time:
                elapsed = round(time.time() - self.failure_start_time, 2)
                
            return {
                "is_active": self.is_active,
                "active_scenario": self.active_scenario,
                "scenario_details": SCENARIOS.get(self.active_scenario) if self.active_scenario else None,
                "start_time": self.failure_start_time,
                "elapsed_seconds": elapsed,
                "duration_seconds": self.duration_seconds
            }
