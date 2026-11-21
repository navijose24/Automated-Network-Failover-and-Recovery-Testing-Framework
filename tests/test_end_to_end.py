"""Complete End-to-End Test Suite for all 6 Specified Network Experiments."""

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

def run_experiment_1_normal(mgr, monitor):
    print("\n=======================================================")
    print(" EXPERIMENT 1: Normal Network Operation")
    print("=======================================================")
    session_id = db_models.create_session("Exp1_Normal_Operation", "normal_operation")
    monitor.reset_stats()
    
    # Send probes for 2 seconds
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

    db_models.end_session(session_id, "COMPLETED")
    metrics = RecoveryAnalyzer.analyze_session(st['recent_probes'], [], failover_success=True)
    db_models.save_metrics(session_id, metrics)
    print(">>> Experiment 1 PASSED!")

def run_experiment_2_link_failure(mgr, monitor, failover_ctrl):
    print("\n=======================================================")
    print(" EXPERIMENT 2: Primary Link Failure")
    print("=======================================================")
    session_id = db_models.create_session("Exp2_Primary_Link_Failure", "primary_link_disconnection")
    monitor.reset_stats()
    failover_ctrl.reset_state()
    
    time.sleep(0.5)
    t0 = time.time()
    failover_ctrl.notify_failure_triggered("primary_link_disconnection", t0, "veth_p_c")
    set_interface_state("ns_primary", "veth_p_c", "down")
    
    # Wait for detection and failover
    t_end = time.time() + 6.0
    while not failover_ctrl.failed_over and time.time() < t_end:
        time.sleep(0.1)
        
    assert failover_ctrl.failed_over, "Failover did not complete"
    time.sleep(0.5)
    
    st = monitor.get_current_status()
    print(f"Failure Detection Time: {failover_ctrl.detection_time_ms} ms")
    print(f"Failover Recovery Time: {failover_ctrl.recovery_time_ms} ms")
    print(f"Active Path after Failover: {st['active_path']}")
    assert st['active_path'] == "BACKUP", "Traffic did not switch to BACKUP path"
    
    # Restore link
    set_interface_state("ns_primary", "veth_p_c", "up")
    
    db_models.end_session(session_id, "COMPLETED")
    metrics = RecoveryAnalyzer.analyze_session(st['recent_probes'], [], failover_success=True)
    metrics["failure_detection_time_ms"] = failover_ctrl.detection_time_ms
    metrics["failover_recovery_time_ms"] = failover_ctrl.recovery_time_ms
    db_models.save_metrics(session_id, metrics)
    print(">>> Experiment 2 PASSED!")

def run_experiment_3_gateway_failure(mgr, monitor, failover_ctrl, failback_ctrl):
    print("\n=======================================================")
    print(" EXPERIMENT 3: Gateway Failure")
    print("=======================================================")
    # First ensure failback to primary
    failback_ctrl.execute_failback()
    time.sleep(0.5)
    
    session_id = db_models.create_session("Exp3_Gateway_Failure", "primary_gateway_unavailability")
    monitor.reset_stats()
    failover_ctrl.reset_state()
    
    t0 = time.time()
    failover_ctrl.notify_failure_triggered("primary_gateway_unavailability", t0, "ns_primary_gateway")
    apply_failure("primary_gateway_unavailability")
    
    t_end = time.time() + 6.0
    while not failover_ctrl.failed_over and time.time() < t_end:
        time.sleep(0.1)
        
    assert failover_ctrl.failed_over, "Gateway failover did not complete"
    time.sleep(0.5)
    
    st = monitor.get_current_status()
    print(f"Gateway Failure Detection Time: {failover_ctrl.detection_time_ms} ms")
    print(f"Gateway Failover Recovery Time: {failover_ctrl.recovery_time_ms} ms")
    print(f"Active Path: {st['active_path']}")
    assert st['active_path'] == "BACKUP"

    # Restore gateway
    restore_failure("primary_gateway_unavailability")
    
    db_models.end_session(session_id, "COMPLETED")
    metrics = RecoveryAnalyzer.analyze_session(st['recent_probes'], [], failover_success=True)
    metrics["failure_detection_time_ms"] = failover_ctrl.detection_time_ms
    metrics["failover_recovery_time_ms"] = failover_ctrl.recovery_time_ms
    db_models.save_metrics(session_id, metrics)
    print(">>> Experiment 3 PASSED!")

def run_experiment_4_interface_failure(mgr, monitor, failover_ctrl, failback_ctrl):
    print("\n=======================================================")
    print(" EXPERIMENT 4: Primary Interface Failure")
    print("=======================================================")
    failback_ctrl.execute_failback()
    time.sleep(0.5)
    
    session_id = db_models.create_session("Exp4_Interface_Failure", "primary_interface_shutdown")
    monitor.reset_stats()
    failover_ctrl.reset_state()
    
    t0 = time.time()
    failover_ctrl.notify_failure_triggered("primary_interface_shutdown", t0, "veth_p_s")
    apply_failure("primary_interface_shutdown")
    
    t_end = time.time() + 6.0
    while not failover_ctrl.failed_over and time.time() < t_end:
        time.sleep(0.1)
        
    assert failover_ctrl.failed_over, "Interface failover did not complete"
    time.sleep(0.5)
    
    st = monitor.get_current_status()
    print(f"Interface Detection Time: {failover_ctrl.detection_time_ms} ms")
    print(f"Interface Recovery Time:  {failover_ctrl.recovery_time_ms} ms")
    print(f"Active Path: {st['active_path']}")
    assert st['active_path'] == "BACKUP"

    # Restore interface
    restore_failure("primary_interface_shutdown")
    
    db_models.end_session(session_id, "COMPLETED")
    metrics = RecoveryAnalyzer.analyze_session(st['recent_probes'], [], failover_success=True)
    metrics["failure_detection_time_ms"] = failover_ctrl.detection_time_ms
    metrics["failover_recovery_time_ms"] = failover_ctrl.recovery_time_ms
    db_models.save_metrics(session_id, metrics)
    print(">>> Experiment 4 PASSED!")

def run_experiment_5_restoration_failback(mgr, monitor, failover_ctrl, failback_ctrl):
    print("\n=======================================================")
    print(" EXPERIMENT 5: Primary Path Restoration & Failback")
    print("=======================================================")
    session_id = db_models.create_session("Exp5_Restoration_Failback", "primary_path_restoration", failback_enabled=True)
    
    # Currently on BACKUP from Exp 4
    # Execute verified failback to primary
    res = failback_ctrl.execute_failback()
    assert res['success'], f"Failback execution failed: {res}"
    time.sleep(0.5)
    
    st = monitor.get_current_status()
    print(f"Failback Duration: {failback_ctrl.failback_duration_ms} ms")
    print(f"Restored Active Path: {st['active_path']}")
    assert st['active_path'] == "PRIMARY", "Traffic not restored to PRIMARY after failback"

    db_models.end_session(session_id, "COMPLETED")
    metrics = RecoveryAnalyzer.analyze_session(st['recent_probes'], [], failover_success=True)
    metrics["failback_recovery_time_ms"] = failback_ctrl.failback_duration_ms
    db_models.save_metrics(session_id, metrics)
    print(">>> Experiment 5 PASSED!")

def run_experiment_6_repeated_cycles(mgr, monitor, failover_ctrl, failback_ctrl):
    print("\n=======================================================")
    print(" EXPERIMENT 6: Repeated Failure Testing (3 Consecutive Cycles)")
    print("=======================================================")
    cycle_metrics = []
    
    for cycle in range(1, 4):
        print(f"\n--- Cycle {cycle}/3 ---")
        failover_ctrl.reset_state()
        failback_ctrl.reset_state()
        time.sleep(0.5)
        
        # Inject failure
        t0 = time.time()
        failover_ctrl.notify_failure_triggered("primary_gateway_unavailability", t0, "gateway")
        apply_failure("primary_gateway_unavailability")
        
        t_end = time.time() + 9.0
        while not failover_ctrl.failed_over and time.time() < t_end:
            time.sleep(0.1)
            
        assert failover_ctrl.failed_over, f"Cycle {cycle} failover failed"
        time.sleep(0.4)
        
        # Restore and failback
        restore_failure("primary_gateway_unavailability")
        time.sleep(0.3)
        fb_res = failback_ctrl.execute_failback()
        assert fb_res['success'], f"Cycle {cycle} failback failed"
        time.sleep(0.5)
        
        cycle_metrics.append({
            "cycle": cycle,
            "detection_ms": failover_ctrl.detection_time_ms,
            "recovery_ms": failover_ctrl.recovery_time_ms,
            "failback_ms": failback_ctrl.failback_duration_ms
        })
        print(f"Cycle {cycle} Result: Detection={failover_ctrl.detection_time_ms} ms, Recovery={failover_ctrl.recovery_time_ms} ms, Failback={failback_ctrl.failback_duration_ms} ms")

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
    
    monitor.register_callback(failover_ctrl.process_probe)
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
