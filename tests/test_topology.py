"""Test Network Topology Manager setup, reachability, and teardown."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network.topology import TopologyManager
from network.cleanup import cleanup_topology

def test_topology():
    print(">>> Starting Stage 2: Network Topology Test...")
    mgr = TopologyManager()
    
    # 1. Setup topology
    success, msg = mgr.setup_topology()
    print(f"Setup result: {success} ({msg})")
    assert success, f"Topology setup failed: {msg}"
    
    # 2. Inspect status
    status = mgr.get_topology_status()
    print(f"Active path: {status['active_path']}")
    print(f"Primary path: {status['primary_path_status']}")
    print(f"Backup path: {status['backup_path_status']}")
    assert status['active_path'] == "PRIMARY", f"Expected active path PRIMARY, got {status['active_path']}"
    assert status['primary_path_status'] == "UP", "Primary path should be UP"
    assert status['backup_path_status'] == "UP", "Backup path should be UP"
    
    # 3. Teardown
    cleanup_success = mgr.teardown()
    print(f"Teardown result: {cleanup_success}")
    assert cleanup_success, "Cleanup failed"
    print(">>> Stage 2 Topology Test PASSED successfully!\n")

if __name__ == "__main__":
    test_topology()
