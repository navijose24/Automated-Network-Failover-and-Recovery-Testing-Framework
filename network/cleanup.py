"""Safe teardown and cleanup of virtual network namespaces and interfaces."""

import logging
from config import ALL_NAMESPACES
from network.executor import run_cmd

logger = logging.getLogger("network_cleanup")

def cleanup_topology() -> bool:
    """Tear down all namespaces and veth pairs created by the framework.
    
    Linux equivalent:
    ip netns del ns_client
    ip netns del ns_primary
    ip netns del ns_backup
    ip netns del ns_server
    """
    logger.info("Cleaning up network namespaces...")
    all_success = True
    
    # Delete each namespace (which automatically removes inside interfaces and routes)
    for ns in ALL_NAMESPACES:
        cmd = f"ip netns del {ns}"
        res = run_cmd(cmd)
        if not res.success and "No such file or directory" not in res.stderr:
            logger.warning(f"Could not delete namespace {ns}: {res.stderr}")
            all_success = False

    # Cleanup any orphan veth pairs in root namespace if they exist
    for dev in ["veth_c_p", "veth_p_c", "veth_p_s", "veth_s_p", "veth_c_b", "veth_b_c", "veth_b_s", "veth_s_b"]:
        run_cmd(f"ip link del {dev} 2>/dev/null")

    return all_success

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = cleanup_topology()
    print(f"Cleanup finished. Success: {success}")
