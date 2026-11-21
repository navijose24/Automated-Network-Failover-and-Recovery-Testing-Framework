"""Test Stage 3: Network Monitoring Engine."""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network.topology import TopologyManager
from monitoring.packet_monitor import PacketMonitor

def test_monitoring():
    print(">>> Starting Stage 3: Network Monitoring Engine Test...")
    mgr = TopologyManager()
    setup_ok, msg = mgr.setup_topology()
    assert setup_ok, f"Setup failed: {msg}"
    
    monitor = PacketMonitor(probe_interval=0.2, timeout=1.0)
    probes_captured = []
    
    def on_probe(p):
        probes_captured.append(p)
        
    monitor.register_callback(on_probe)
    monitor.start()
    
    print("Monitoring live ICMP ping probes for 2.5 seconds...")
    time.sleep(2.5)
    
    status = monitor.get_current_status()
    monitor.stop()
    mgr.teardown()
    
    print(f"Total transmitted: {status['total_transmitted']}")
    print(f"Total received: {status['total_received']}")
    print(f"Loss percent: {status['packet_loss_percent']}%")
    print(f"Avg latency: {status['avg_latency_ms']} ms")
    print(f"Active path: {status['active_path']}")
    
    assert status['total_transmitted'] >= 5, f"Expected at least 5 probes, got {status['total_transmitted']}"
    assert status['total_received'] >= 5, f"Expected at least 5 successful probes, got {status['total_received']}"
    assert status['packet_loss_percent'] == 0.0, f"Expected 0% packet loss, got {status['packet_loss_percent']}"
    assert status['avg_latency_ms'] > 0.0, f"Expected latency > 0, got {status['avg_latency_ms']}"
    assert status['active_path'] == "PRIMARY", f"Expected active path PRIMARY, got {status['active_path']}"
    assert len(probes_captured) == status['total_transmitted'], "Callback capture count mismatch"
    
    print(">>> Stage 3 Network Monitoring Test PASSED successfully!\n")

if __name__ == "__main__":
    test_monitoring()
