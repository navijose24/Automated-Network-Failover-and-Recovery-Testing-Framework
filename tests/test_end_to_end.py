"""Complete End-to-End Test Suite for all 6 Specified Network Experiments.
Validates real topology, failure detection, automatic failover, failback,
database probe/event logging, recovery analysis, and CSV reporting.
"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network.topology import TopologyManager
from monitoring.packet_monitor import PacketMonitor
from simulation.failure_engine import FailureEngine
from simulation.scenarios import apply_failure, restore_failure
from failover.controller import FailoverController
from failover.failback import FailbackController
from analysis.recovery_analyzer import RecoveryAnalyzer
from reporting.report_generator import ReportGenerator
import database.models as db_models
from database.db import init_db
from network.interfaces import set_interface_state

# Active session tracker for callbacks
current_session_id = None

def setup_callbacks(monitor, failover_ctrl, failback_ctrl):
    """Register synchronized telemetry and event logging callbacks."""
    def on_probe(probe):
        failover_ctrl.process_probe(probe)
        if failover_ctrl.failed_over and not failback_ctrl.failback_completed:
            failback_ctrl.process_health_tick(is_failed_over=True)
            
        global current_session_id
        if current_session_id is not None:
            try:
                db_models.log_probe(current_session_id, {
                    "timestamp": probe.timestamp,
                    "sequence_num": probe.sequence_num,
                    "target_ip": probe.target_ip,
                    "success": probe.success,
                    "rtt_ms": probe.rtt_ms,
                    "active_interface": probe.active_interface,
                    "active_path": probe.active_path
                })
            except Exception as e:
                print(f"[ERR] log_probe: {e}")

    def on_event(event_type, data):
        global current_session_id
        if current_session_id is not None:
            try:
                db_models.log_event(
                    session_id=current_session_id,
                    event_type=event_type,
                    scenario=data.get("scenario") or failover_ctrl.active_scenario,
                    affected_interface=data.get("failed_interface") or data.get("active_device"),
                    details=data,
                    timestamp=data.get("timestamp") or time.time()
                )
            except Exception as e:
                print(f"[ERR] log_event: {e}")

    monitor.register_callback(on_probe)
    failover_ctrl.register_listener(on_event)
    failback_ctrl.register_listener(on_event)

def finalize_session(session_id, failover_ctrl=None, failback_ctrl=None):
    """End session, analyze recorded probes and events, and commit verified metrics."""
    global current_session_id
    db_models.end_session(session_id, "COMPLETED")
    
    probes = db_models.get_session_probes(session_id)
    events = db_models.get_session_events(session_id)
    
    metrics = RecoveryAnalyzer.analyze_session(probes, events, failover_success=True)
    if failover_ctrl and failover_ctrl.detection_time_ms is not None:
        metrics["failure_detection_time_ms"] = failover_ctrl.detection_time_ms
    if failover_ctrl and failover_ctrl.recovery_time_ms is not None:
        metrics["failover_recovery_time_ms"] = failover_ctrl.recovery_time_ms
    if failback_ctrl and failback_ctrl.failback_duration_ms is not None:
        metrics["failback_recovery_time_ms"] = failback_ctrl.failback_duration_ms
        
    db_models.save_metrics(session_id, metrics)
    current_session_id = None
    return metrics, probes

def run_experiment_1_normal(mgr, monitor):
    global current_session_id
    print("\n=======================================================")
    print(" EXPERIMENT 1: Normal Network Operation")
    print("=======================================================")
    session_id = db_models.create_session("Exp1_Normal_Operation", "normal_operation")
    current_session_id = session_id
    monitor.reset_stats()
    
    # Collect baseline telemetry for 2.0 seconds
    time.sleep(2.0)
    
    st = monitor.get_current_status()
    print(f"Total Probes Transmitted: {st['total_transmitted']}")
    print(f"Total Received:            {st['total_received']}")
    print(f"Packet Loss:               {st['packet_loss_percent']}%")
    print(f"Average Latency:           {st['avg_latency_ms']} ms")
    print(f"Active Path:               {st['active_path']}")

    assert st['total_received'] >= 4, "Too few probes received"
    assert st['packet_loss_percent'] == 0.0, "Expected 0% packet loss in normal baseline"
    assert st['active_path'] == "PRIMARY", f"Expected PRIMARY, got {st['active_path']}"

    metrics, probes = finalize_session(session_id)
    assert len(probes) >= 4, f"Expected recorded probes in DB, found {len(probes)}"
    print(f">>> Experiment 1 PASSED! Logged {len(probes)} probes.")

def run_experiment_2_link_failure(mgr, monitor, failover_ctrl):
    global current_session_id
    print("\n=======================================================")
    print(" EXPERIMENT 2: Primary Link Failure")
    print("=======================================================")
    session_id = db_models.create_session("Exp2_Primary_Link_Failure", "primary_link_disconnection")
    current_session_id = session_id
    monitor.reset_stats()
    failover_ctrl.reset_state()
    
    time.sleep(0.5)
    t0 = time.time()
    t0_mono = time.monotonic()
    failover_ctrl.notify_failure_triggered("primary_link_disconnection", t0, "veth_p_c", start_mono=t0_mono)
    set_interface_state("ns_primary", "veth_p_c", "down")
    
    # Wait for detection and failover
    t_end = time.time() + 10.0
    while not failover_ctrl.failed_over and time.time() < t_end:
        time.sleep(0.1)
        
    assert failover_ctrl.failed_over, "Failover did not complete"
    
    # Wait for monitor to confirm active path on BACKUP
    t_wait = time.time() + 4.0
    while monitor.get_current_status()["active_path"] != "BACKUP" and time.time() < t_wait:
        time.sleep(0.1)
    
    st = monitor.get_current_status()
    print(f"Failure Detection Time: {failover_ctrl.detection_time_ms} ms")
    print(f"Failover Recovery Time: {failover_ctrl.recovery_time_ms} ms")
    print(f"Active Path after Failover: {st['active_path']}")
    assert st['active_path'] == "BACKUP", "Traffic did not switch to BACKUP path"
    
    # Restore link
    set_interface_state("ns_primary", "veth_p_c", "up")
    
    metrics, probes = finalize_session(session_id, failover_ctrl=failover_ctrl)
    assert len(probes) > 0, "No probes recorded in DB for Exp 2"
    print(f">>> Experiment 2 PASSED! Logged {len(probes)} probes.")

def run_experiment_3_gateway_failure(mgr, monitor, failover_ctrl, failback_ctrl):
    global current_session_id
    print("\n=======================================================")
    print(" EXPERIMENT 3: Gateway Failure")
    print("=======================================================")
    # First ensure failback to primary
    failback_ctrl.execute_failback()
    time.sleep(0.5)
    
    session_id = db_models.create_session("Exp3_Gateway_Failure", "primary_gateway_unavailability")
    current_session_id = session_id
    monitor.reset_stats()
    failover_ctrl.reset_state()
    
    t0 = time.time()
    t0_mono = time.monotonic()
    failover_ctrl.notify_failure_triggered("primary_gateway_unavailability", t0, "ns_primary_gateway", start_mono=t0_mono)
    apply_failure("primary_gateway_unavailability")
    
    t_end = time.time() + 10.0
    while not failover_ctrl.failed_over and time.time() < t_end:
        time.sleep(0.1)
        
    assert failover_ctrl.failed_over, "Gateway failover did not complete"
    
    t_wait = time.time() + 4.0
    while monitor.get_current_status()["active_path"] != "BACKUP" and time.time() < t_wait:
        time.sleep(0.1)
    
    st = monitor.get_current_status()
    print(f"Gateway Failure Detection Time: {failover_ctrl.detection_time_ms} ms")
    print(f"Gateway Failover Recovery Time: {failover_ctrl.recovery_time_ms} ms")
    print(f"Active Path: {st['active_path']}")
    assert st['active_path'] == "BACKUP"

    # Restore gateway
    restore_failure("primary_gateway_unavailability")
    
    metrics, probes = finalize_session(session_id, failover_ctrl=failover_ctrl)
    assert len(probes) > 0, "No probes recorded in DB for Exp 3"
    print(f">>> Experiment 3 PASSED! Logged {len(probes)} probes.")

def run_experiment_4_interface_failure(mgr, monitor, failover_ctrl, failback_ctrl):
    global current_session_id
    print("\n=======================================================")
    print(" EXPERIMENT 4: Primary Interface Failure")
    print("=======================================================")
    failback_ctrl.execute_failback()
    time.sleep(0.5)
    
    session_id = db_models.create_session("Exp4_Interface_Failure", "primary_interface_shutdown")
    current_session_id = session_id
    monitor.reset_stats()
    failover_ctrl.reset_state()
    
    t0 = time.time()
    t0_mono = time.monotonic()
    failover_ctrl.notify_failure_triggered("primary_interface_shutdown", t0, "veth_p_s", start_mono=t0_mono)
    apply_failure("primary_interface_shutdown")
    
    t_end = time.time() + 10.0
    while not failover_ctrl.failed_over and time.time() < t_end:
        time.sleep(0.1)
        
    assert failover_ctrl.failed_over, "Interface failover did not complete"
    
    t_wait = time.time() + 4.0
    while monitor.get_current_status()["active_path"] != "BACKUP" and time.time() < t_wait:
        time.sleep(0.1)
    
    st = monitor.get_current_status()
    print(f"Interface Detection Time: {failover_ctrl.detection_time_ms} ms")
    print(f"Interface Recovery Time:  {failover_ctrl.recovery_time_ms} ms")
    print(f"Active Path: {st['active_path']}")
    assert st['active_path'] == "BACKUP"

    # Restore interface
    restore_failure("primary_interface_shutdown")
    
    metrics, probes = finalize_session(session_id, failover_ctrl=failover_ctrl)
    assert len(probes) > 0, "No probes recorded in DB for Exp 4"
    print(f">>> Experiment 4 PASSED! Logged {len(probes)} probes.")

def run_experiment_5_restoration_failback(mgr, monitor, failover_ctrl, failback_ctrl):
    global current_session_id
    print("\n=======================================================")
    print(" EXPERIMENT 5: Primary Path Restoration & Failback")
    print("=======================================================")
    session_id = db_models.create_session("Exp5_Restoration_Failback", "primary_path_restoration", failback_enabled=True)
    current_session_id = session_id
    
    # Currently on BACKUP from Exp 4
    # Execute verified failback to primary
    res = failback_ctrl.execute_failback()
    assert res['success'], f"Failback execution failed: {res}"
    
    t_wait = time.time() + 4.0
    while monitor.get_current_status()["active_path"] != "PRIMARY" and time.time() < t_wait:
        time.sleep(0.1)
    
    st = monitor.get_current_status()
    print(f"Failback Duration: {failback_ctrl.failback_duration_ms} ms")
    print(f"Restored Active Path: {st['active_path']}")
    assert st['active_path'] == "PRIMARY", "Traffic not restored to PRIMARY after failback"

    metrics, probes = finalize_session(session_id, failback_ctrl=failback_ctrl)
    assert len(probes) > 0, "No probes recorded in DB for Exp 5"
    print(f">>> Experiment 5 PASSED! Logged {len(probes)} probes.")

def run_experiment_6_repeated_cycles(mgr, monitor, failover_ctrl, failback_ctrl):
    print("\n=======================================================")
    print(" EXPERIMENT 6: Repeated Failure Testing (3 Consecutive Cycles)")
    print("=======================================================")
    global current_session_id
    cycle_metrics = []
    
    for cycle in range(1, 4):
        print(f"\n--- Cycle {cycle}/3 ---")
        session_id = db_models.create_session(f"Exp6_Repeated_Cycle_{cycle}", "primary_gateway_unavailability", failback_enabled=True)
        current_session_id = session_id
        failover_ctrl.reset_state()
        failback_ctrl.reset_state()
        time.sleep(0.5)
        
        # Inject failure
        t0 = time.time()
        t0_mono = time.monotonic()
        failover_ctrl.notify_failure_triggered("primary_gateway_unavailability", t0, "gateway", start_mono=t0_mono)
        apply_failure("primary_gateway_unavailability")
        
        t_end = time.time() + 10.0
        while not failover_ctrl.failed_over and time.time() < t_end:
            time.sleep(0.1)
            
        assert failover_ctrl.failed_over, f"Cycle {cycle} failover failed"
        
        t_wait = time.time() + 4.0
        while monitor.get_current_status()["active_path"] != "BACKUP" and time.time() < t_wait:
            time.sleep(0.1)
        
        # Restore and failback
        restore_failure("primary_gateway_unavailability")
        time.sleep(0.3)
        fb_res = failback_ctrl.execute_failback()
        assert fb_res['success'], f"Cycle {cycle} failback failed"
        
        t_wait_fb = time.time() + 4.0
        while monitor.get_current_status()["active_path"] != "PRIMARY" and time.time() < t_wait_fb:
            time.sleep(0.1)
        
        metrics, probes = finalize_session(session_id, failover_ctrl=failover_ctrl, failback_ctrl=failback_ctrl)
        
        cycle_metrics.append({
            "cycle": cycle,
            "detection_ms": failover_ctrl.detection_time_ms,
            "recovery_ms": failover_ctrl.recovery_time_ms,
            "failback_ms": failback_ctrl.failback_duration_ms,
            "probes_count": len(probes)
        })
        print(f"Cycle {cycle} Result: Detection={failover_ctrl.detection_time_ms} ms, Recovery={failover_ctrl.recovery_time_ms} ms, Failback={failback_ctrl.failback_duration_ms} ms, Probes={len(probes)}")

    assert len(cycle_metrics) == 3
    print(">>> Experiment 6 Repeated Cycles PASSED successfully!")

def main():
    print("#######################################################")
    print(" STARTING COMPLETE END-TO-END NETWORK EXPERIMENT SUITE")
    print("#######################################################")
    
    init_db()
    mgr = TopologyManager()
    ok, msg = mgr.setup_topology()
    assert ok, f"Initial topology setup failed: {msg}"
    
    monitor = PacketMonitor(probe_interval=0.2, timeout=1.0)
    failover_ctrl = FailoverController(failure_threshold=3)
    failback_ctrl = FailbackController(stability_threshold=3, auto_failback=True)
    
    setup_callbacks(monitor, failover_ctrl, failback_ctrl)
    monitor.start()
    
    try:
        run_experiment_1_normal(mgr, monitor)
        run_experiment_2_link_failure(mgr, monitor, failover_ctrl)
        run_experiment_3_gateway_failure(mgr, monitor, failover_ctrl, failback_ctrl)
        run_experiment_4_interface_failure(mgr, monitor, failover_ctrl, failback_ctrl)
        run_experiment_5_restoration_failback(mgr, monitor, failover_ctrl, failback_ctrl)
        run_experiment_6_repeated_cycles(mgr, monitor, failover_ctrl, failback_ctrl)
        
        # Check Report Generation & Pandas Analytics
        print("\n=======================================================")
        print(" TESTING REPORT GENERATION & PANDAS ANALYTICS")
        print("=======================================================")
        csv_all = ReportGenerator.generate_all_sessions_csv()
        assert "session_id" in csv_all, "All sessions CSV header missing"
        print("Master CSV Generated: Length =", len(csv_all), "bytes")
        
        # Verify single session probe CSV export has real rows
        latest_sessions = db_models.get_all_sessions(limit=1)
        if latest_sessions:
            s_id = latest_sessions[0]["id"]
            probe_csv = ReportGenerator.generate_session_probes_csv(s_id)
            lines = [l for l in probe_csv.strip().split("\n") if l]
            print(f"Session {s_id} Probe CSV Generated: {len(lines)} lines (header + {len(lines)-1} probes)")
            assert len(lines) > 1, f"Expected data rows in session probe CSV, got {len(lines)}"

        comparison = ReportGenerator.get_scenario_comparison_summary()
        print("Pandas Aggregation Summary:")
        for r in comparison:
            print(f" - {r['scenario_name']}: {r['session_count']} runs, Avg Detection={r['failure_detection_time_ms']} ms, Avg Recovery={r['failover_recovery_time_ms']} ms, Avg Loss={r['packet_loss_percent']}%")
            
        assert len(comparison) >= 3, "Expected at least 3 distinct scenario groups in Pandas aggregation"
        print(">>> Report Generation & Pandas Analytics PASSED!")

    finally:
        monitor.stop()
        mgr.teardown()
        
    print("\n#######################################################")
    print(" ALL 6 SPECIFIED EXPERIMENTS PASSED WITH 100% SUCCESS!")
    print("#######################################################\n")

if __name__ == "__main__":
    main()
