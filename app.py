"""Automated Network Failover and Recovery Testing Framework - Flask Web Application."""

import os
import time
import logging
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, Response, send_file

from config import (
    HOST, PORT, DEBUG, NS_CLIENT, IP_CONFIG,
    FAILURE_THRESHOLD, FAILBACK_STABILITY_THRESHOLD, AUTO_FAILBACK_DEFAULT
)
from network.topology import TopologyManager
from network.cleanup import cleanup_topology
from monitoring.packet_monitor import PacketMonitor
from simulation.failure_engine import FailureEngine
from simulation.scenarios import SCENARIOS
from failover.controller import FailoverController
from failover.failback import FailbackController
from analysis.recovery_analyzer import RecoveryAnalyzer
from reporting.report_generator import ReportGenerator
from database.db import init_db
import database.models as db_models

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
)
logger = logging.getLogger("failover_app")

app = Flask(__name__)
app.config["SECRET_KEY"] = "academic-network-failover-secret-2026"

# Initialize Database Schema
init_db()

# Core Framework Components
topology_mgr = TopologyManager()
monitor = PacketMonitor(probe_interval=0.5, timeout=1.0)
failover_ctrl = FailoverController(failure_threshold=FAILURE_THRESHOLD)
failback_ctrl = FailbackController(
    stability_threshold=FAILBACK_STABILITY_THRESHOLD,
    auto_failback=AUTO_FAILBACK_DEFAULT
)
failure_engine = FailureEngine()

# Active Session State
current_session_id: Optional[int] = None
session_lock = False

# ----------------- EVENT WIRING -----------------

def handle_probe(probe):
    """Callback on every ICMP probe."""
    global current_session_id
    
    # 1. Forward probe to failover controller
    failover_ctrl.process_probe(probe)
    
    # 2. Forward health tick to failback controller if in failover
    if failover_ctrl.failed_over and not failback_ctrl.failback_completed:
        failback_ctrl.process_health_tick(is_failed_over=True)
        
    # 3. Log probe to database if session is active
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
        except Exception as ex:
            logger.error(f"Error logging probe: {ex}")

monitor.register_callback(handle_probe)

def handle_framework_event(event_type: str, data: Dict[str, Any]):
    """Unified handler for network lifecycle events."""
    global current_session_id
    logger.info(f"Framework Event: {event_type} -> {data}")
    
    if current_session_id is not None:
        try:
            db_models.log_event(
                session_id=current_session_id,
                event_type=event_type,
                scenario=data.get("scenario") or data.get("scenario_id") or failover_ctrl.active_scenario,
                affected_interface=data.get("failed_interface") or data.get("affected_component") or data.get("active_device"),
                details=data,
                timestamp=data.get("timestamp") or time.time()
            )
        except Exception as ex:
            logger.error(f"Error logging event: {ex}")

# Register event listeners
failover_ctrl.register_listener(handle_framework_event)
failback_ctrl.register_listener(handle_framework_event)
failure_engine.register_listener(handle_framework_event)

# ----------------- HTML PAGE ROUTES -----------------

@app.route("/")
def page_dashboard():
    stats = db_models.get_aggregate_stats()
    return render_template("dashboard.html", stats=stats)

@app.route("/topology")
def page_topology():
    return render_template("topology.html", ip_cfg=IP_CONFIG)

@app.route("/simulation")
def page_simulation():
    return render_template("simulation.html", scenarios=SCENARIOS)

@app.route("/monitoring")
def page_monitoring():
    return render_template("monitoring.html")

@app.route("/analysis")
def page_analysis():
    sessions = db_models.get_all_sessions(limit=50)
    comparison = ReportGenerator.get_scenario_comparison_summary()
    return render_template("analysis.html", sessions=sessions, comparison=comparison)

@app.route("/history")
def page_history():
    sessions = db_models.get_all_sessions(limit=100)
    return render_template("history.html", sessions=sessions)

@app.route("/reports")
def page_reports():
    sessions = db_models.get_all_sessions(limit=100)
    comparison = ReportGenerator.get_scenario_comparison_summary()
    return render_template("reports.html", sessions=sessions, comparison=comparison)

# ----------------- REST API ENDPOINTS -----------------

@app.route("/api/status", methods=["GET"])
def api_status():
    """Consolidated live system status across all modules."""
    top_status = topology_mgr.get_topology_status()
    mon_status = monitor.get_current_status()
    fo_status = failover_ctrl.get_status()
    fb_status = failback_ctrl.get_status()
    sim_status = failure_engine.get_status()

    return jsonify({
        "session_id": current_session_id,
        "is_session_active": current_session_id is not None,
        "topology": top_status,
        "monitor": mon_status,
        "failover": fo_status,
        "failback": fb_status,
        "simulation": sim_status
    })

@app.route("/api/topology/setup", methods=["POST"])
def api_topology_setup():
    """Provision and verify virtual network namespaces."""
    success, msg = topology_mgr.setup_topology()
    if success:
        # If monitor is not running, start it
        if not monitor.running:
            monitor.start()
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg}), 500

@app.route("/api/topology/teardown", methods=["POST"])
def api_topology_teardown():
    """Safely destroy virtual network namespaces."""
    monitor.stop()
    success = topology_mgr.teardown()
    return jsonify({"success": success, "message": "Topology torn down cleanly."})

@app.route("/api/session/start", methods=["POST"])
def api_session_start():
    """Start a new experiment session."""
    global current_session_id
    data = request.json or {}
    session_name = data.get("session_name", f"Session_{int(time.time())}")
    scenario_name = data.get("scenario_name", "normal_operation")
    failback_enabled = bool(data.get("failback_enabled", False))

    # Ensure topology is up
    status = topology_mgr.get_topology_status()
    if status["primary_path_status"] != "UP" and status["backup_path_status"] != "UP":
        ok, msg = topology_mgr.setup_topology()
        if not ok:
            return jsonify({"success": False, "error": f"Failed to initialize topology: {msg}"}), 500

    # Reset controller states
    monitor.reset_stats()
    failover_ctrl.reset_state()
    failback_ctrl.reset_state()
    failback_ctrl.set_auto_failback(failback_enabled)

    # Start monitor if stopped
    if not monitor.running:
        monitor.start()

    session_id = db_models.create_session(
        session_name=session_name,
        scenario_name=scenario_name,
        failback_enabled=failback_enabled,
        config_dict=data
    )
    current_session_id = session_id

    # Log START event
    db_models.log_event(
        session_id=session_id,
        event_type="SESSION_STARTED",
        scenario=scenario_name,
        details={"session_name": session_name, "failback_enabled": failback_enabled}
    )

    return jsonify({
        "success": True,
        "session_id": session_id,
        "message": f"Session {session_name} started."
    })

@app.route("/api/session/stop", methods=["POST"])
def api_session_stop():
    """Stop active experiment session and compute final metrics."""
    global current_session_id
    if current_session_id is None:
        return jsonify({"success": False, "error": "No active session to stop."}), 400

    session_id = current_session_id
    db_models.log_event(session_id=session_id, event_type="SESSION_STOPPED")
    db_models.end_session(session_id=session_id, status="COMPLETED")

    # Fetch recorded session probes and events
    probes = db_models.get_session_probes(session_id)
    events = db_models.get_session_events(session_id)

    # Analyze metrics
    metrics = RecoveryAnalyzer.analyze_session(
        probes=probes,
        events=events,
        failover_success=failover_ctrl.failover_success
    )
    db_models.save_metrics(session_id=session_id, metrics=metrics)

    current_session_id = None
    return jsonify({
        "success": True,
        "session_id": session_id,
        "metrics": metrics
    })

@app.route("/api/failure/trigger", methods=["POST"])
def api_failure_trigger():
    """Inject a failure scenario."""
    data = request.json or {}
    scenario_id = data.get("scenario_id")
    duration = float(data.get("duration", 0.0))

    if not scenario_id or scenario_id not in SCENARIOS:
        return jsonify({"success": False, "error": f"Invalid scenario: {scenario_id}"}), 400

    # Notify failover controller of ground-truth start
    t0 = time.time()
    t0_mono = time.monotonic()
    affected = SCENARIOS[scenario_id]["affected_component"]
    failover_ctrl.notify_failure_triggered(scenario_id, t0, affected, start_mono=t0_mono)

    result = failure_engine.trigger_failure(scenario_id, duration_seconds=duration)
    return jsonify(result)

@app.route("/api/failure/restore", methods=["POST"])
def api_failure_restore():
    """Manually restore active failure."""
    res = failure_engine.restore_failure()
    if res.get("success"):
        failback_ctrl.notify_primary_restored(time.time())
    return jsonify(res)

@app.route("/api/failover/manual", methods=["POST"])
def api_failover_manual():
    """Manually trigger failover to backup route."""
    res = failover_ctrl.manual_failover()
    return jsonify(res)

@app.route("/api/failback/manual", methods=["POST"])
def api_failback_manual():
    """Manually trigger failback to primary route."""
    res = failback_ctrl.execute_failback()
    return jsonify(res)

@app.route("/api/failback/config", methods=["POST"])
def api_failback_config():
    """Update auto-failback setting."""
    data = request.json or {}
    enabled = bool(data.get("enabled", False))
    failback_ctrl.set_auto_failback(enabled)
    return jsonify({"success": True, "auto_failback": enabled})

@app.route("/api/probes/live", methods=["GET"])
def api_probes_live():
    """Return recent probes for live Chart.js rendering."""
    status = monitor.get_current_status()
    return jsonify({
        "probes": status["recent_probes"],
        "active_path": status["active_path"],
        "packet_loss_percent": status["packet_loss_percent"],
        "avg_latency_ms": status["avg_latency_ms"]
    })

@app.route("/api/history", methods=["GET"])
def api_history():
    """Return historical experiment sessions."""
    sessions = db_models.get_all_sessions(limit=50)
    return jsonify({"sessions": sessions})

@app.route("/api/session/<int:session_id>", methods=["GET"])
def api_session_detail(session_id: int):
    """Return full details, probes, and metrics for a specific session."""
    session = db_models.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    metrics = db_models.get_session_metrics(session_id)
    events = db_models.get_session_events(session_id)
    probes = db_models.get_session_probes(session_id)
    
    return jsonify({
        "session": session,
        "metrics": metrics,
        "events": events,
        "probes": probes
    })

# ----------------- CSV DOWNLOAD ROUTES -----------------

@app.route("/download/session/<int:session_id>/probes.csv")
def download_session_probes_csv(session_id: int):
    csv_data = ReportGenerator.generate_session_probes_csv(session_id)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=session_{session_id}_probes.csv"}
    )

@app.route("/download/session/<int:session_id>/summary.csv")
def download_session_summary_csv(session_id: int):
    csv_data = ReportGenerator.generate_session_summary_csv(session_id)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=session_{session_id}_summary.csv"}
    )

@app.route("/download/all_sessions.csv")
def download_all_sessions_csv():
    csv_data = ReportGenerator.generate_all_sessions_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=network_failover_all_sessions.csv"}
    )

# ----------------- APP INITIALIZATION -----------------

def initialize_app():
    """Provision topology and start monitor on application startup."""
    logger.info("Initializing virtual network topology on server startup...")
    success, msg = topology_mgr.setup_topology()
    if success:
        logger.info("Topology initialized successfully.")
        monitor.start()
    else:
        logger.warning(f"Initial topology setup warning: {msg}. Can be initialized via dashboard.")

if __name__ == "__main__":
    initialize_app()
    logger.info(f"Starting Network Failover Framework dashboard on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
