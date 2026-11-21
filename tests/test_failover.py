"""Test Stage 5: End-to-End Automatic Failover and Failback."""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network.topology import TopologyManager
from monitoring.packet_monitor import PacketMonitor
from simulation.failure_engine import FailureEngine
from failover.controller import FailoverController
from failover.failback import FailbackController
from network.interfaces import set_interface_state

def test_failover_and_failback():
    print(">>> Starting Stage 5: Failover and Failback Test...")
    
    # 1. Setup
    mgr = TopologyManager()
    ok, msg = mgr.setup_topology()
    assert ok, f"Setup failed: {msg}"
    
    monitor = PacketMonitor(probe_interval=0.2, timeout=1.0)
    failover_ctrl = FailoverController(failure_threshold=3)
    failback_ctrl = FailbackController(stability_threshold=3, auto_failback=True)
    
    events_logged = []
    def log_event(evt_type, data):
        print(f"[EVENT] {evt_type}: {data}")
        events_logged.append((evt_type, data))
        
    failover_ctrl.register_listener(log_event)
    failback_ctrl.register_listener(log_event)
    
    # Wire probe stream to failover controller
    monitor.register_callback(failover_ctrl.process_probe)
    monitor.start()
    
    print("Baseline monitoring running for 1.2 seconds...")
    time.sleep(1.2)
    assert monitor.get_current_status()["active_path"] == "PRIMARY"
    
    # 2. Trigger Failure: Disconnect primary link at primary router interface
    print("\n--- INJECTING FAILURE: primary link disconnection ---")
    start_time = time.time()
    failover_ctrl.notify_failure_triggered("primary_link_disconnection", start_time, "veth_p_c")
    set_interface_state("ns_primary", "veth_p_c", "down")
    
    # Wait for detection and failover
    print("Waiting for failure detection and automatic backup route activation...")
    timeout_t = time.time() + 8.0
    while not failover_ctrl.failed_over and time.time() < timeout_t:
        time.sleep(0.1)
        
    assert failover_ctrl.failed_over, "Failover did not complete within timeout!"
    print(f"Failover successful! Detection time: {failover_ctrl.detection_time_ms} ms, Recovery time: {failover_ctrl.recovery_time_ms} ms")
    assert failover_ctrl.detection_time_ms is not None and failover_ctrl.detection_time_ms > 0
    assert failover_ctrl.recovery_time_ms is not None and failover_ctrl.recovery_time_ms > 0
    assert failover_ctrl.recovery_time_ms >= failover_ctrl.detection_time_ms, "Recovery time should be >= detection time"
    
    time.sleep(0.5)
    status_failover = monitor.get_current_status()
    print(f"Current active path after failover: {status_failover['active_path']}")
    assert status_failover["active_path"] == "BACKUP"

    # 3. Restore Primary Link to test Failback
    print("\n--- RESTORING PRIMARY LINK (Testing Failback) ---")
    set_interface_state("ns_primary", "veth_p_c", "up")
    failback_ctrl.notify_primary_restored(time.time())
    
    print("Waiting for primary stability verification and automatic failback...")
    timeout_fb = time.time() + 8.0
    while not failback_ctrl.failback_completed and time.time() < timeout_fb:
        failback_ctrl.process_health_tick(is_failed_over=True)
        time.sleep(0.2)
        
    assert failback_ctrl.failback_completed, "Failback did not complete within timeout!"
    print(f"Failback successful! Duration: {failback_ctrl.failback_duration_ms} ms")
    
    time.sleep(0.5)
    status_failback = monitor.get_current_status()
    print(f"Current active path after failback: {status_failback['active_path']}")
    assert status_failback["active_path"] == "PRIMARY"

    # Cleanup
    monitor.stop()
    mgr.teardown()
    print("\n>>> Stage 5 Failover and Failback Test PASSED successfully!\n")

if __name__ == "__main__":
    test_failover_and_failback()
