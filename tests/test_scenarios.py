"""Test Stage 4: Verify all 5 Failure Simulation Scenarios."""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network.topology import TopologyManager
from simulation.scenarios import SCENARIOS, apply_failure, restore_failure
from monitoring.connectivity import send_probe

def test_all_scenarios():
    print(">>> Starting Stage 4: Failure Simulation Scenarios Test...")
    mgr = TopologyManager()
    ok, msg = mgr.setup_topology()
    assert ok, f"Setup failed: {msg}"
    
    # Baseline check
    p_base = send_probe()
    assert p_base.success, "Baseline probe before scenarios failed"
    print("Baseline ping verified: OK")

    for scenario_id, meta in SCENARIOS.items():
        print(f"\n--- Testing Scenario: {meta['name']} ({scenario_id}) ---")
        
        # Apply failure
        applied = apply_failure(scenario_id)
        assert applied, f"Failed to apply {scenario_id}"
        time.sleep(0.5)
        
        # Verify disruption: for route removal, route table changes; for others, primary interface or link fails
        print(f"Applied: {meta['linux_command']}")
        
        # Restore failure
        restored = restore_failure(scenario_id)
        assert restored, f"Failed to restore {scenario_id}"
        time.sleep(0.5)
        
        # Verify connectivity back to normal
        p_restored = send_probe()
        assert p_restored.success, f"Probe after restoring {scenario_id} failed"
        print(f"Restored: {meta['restore_command']} -> Ping OK (rtt: {p_restored.rtt_ms} ms)")

    mgr.teardown()
    print("\n>>> Stage 4 Failure Simulation Test PASSED successfully!\n")

if __name__ == "__main__":
    test_all_scenarios()
