"""Failure scenario definitions and execution routines."""

import logging
from typing import Dict, Any, Callable
from config import NS_CLIENT, NS_PRIMARY, NS_SERVER, IP_CONFIG
from network.executor import run_cmd, run_in_ns
from network.interfaces import set_interface_state
from network.routing import delete_route, add_route

logger = logging.getLogger("failure_scenarios")

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "primary_link_disconnection": {
        "name": "Primary Link Disconnection",
        "description": "Simulates physical/logical cable disconnection on the client's primary veth interface.",
        "affected_component": "Client Primary Interface (veth_c_p)",
        "affected_ns": NS_CLIENT,
        "linux_command": f"ip -n {NS_CLIENT} link set dev {IP_CONFIG['client_pri_dev']} down",
        "restore_command": f"ip -n {NS_CLIENT} link set dev {IP_CONFIG['client_pri_dev']} up"
    },
    "primary_gateway_unavailability": {
        "name": "Primary Gateway Unavailability",
        "description": "Disables IP forwarding on the primary router (ns_primary), simulating gateway crash/freeze.",
        "affected_component": "Primary Router Gateway (sysctl net.ipv4.ip_forward=0)",
        "affected_ns": NS_PRIMARY,
        "linux_command": f"ip netns exec {NS_PRIMARY} sysctl -w net.ipv4.ip_forward=0",
        "restore_command": f"ip netns exec {NS_PRIMARY} sysctl -w net.ipv4.ip_forward=1"
    },
    "primary_interface_shutdown": {
        "name": "Primary Interface Shutdown",
        "description": "Disables the primary router's egress interface toward the destination server (veth_p_s).",
        "affected_component": "Primary Router Egress (veth_p_s)",
        "affected_ns": NS_PRIMARY,
        "linux_command": f"ip -n {NS_PRIMARY} link set dev {IP_CONFIG['primary_srv_dev']} down",
        "restore_command": f"ip -n {NS_PRIMARY} link set dev {IP_CONFIG['primary_srv_dev']} up"
    },
    "primary_route_removal": {
        "name": "Primary Route Removal",
        "description": "Removes the primary destination route from client's routing table (simulating routing table corruption or withdrawal).",
        "affected_component": "Client Routing Table Route",
        "affected_ns": NS_CLIENT,
        "linux_command": f"ip -n {NS_CLIENT} route del {IP_CONFIG['target_ip']} via {IP_CONFIG['primary_gw']} dev {IP_CONFIG['client_pri_dev']}",
        "restore_command": f"ip -n {NS_CLIENT} route add {IP_CONFIG['target_ip']} via {IP_CONFIG['primary_gw']} dev {IP_CONFIG['client_pri_dev']} metric {IP_CONFIG['metric_primary']}"
    },
    "temporary_interruption": {
        "name": "Temporary Network Interruption",
        "description": "Introduces a transient network outage on the primary link that automatically recovers after the specified duration.",
        "affected_component": "Client Primary Link Flap (veth_c_p)",
        "affected_ns": NS_CLIENT,
        "linux_command": f"ip -n {NS_CLIENT} link set dev {IP_CONFIG['client_pri_dev']} down (for duration)",
        "restore_command": f"ip -n {NS_CLIENT} link set dev {IP_CONFIG['client_pri_dev']} up"
    }
}

def apply_failure(scenario_id: str) -> bool:
    """Apply the specified failure scenario to the virtual environment."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}")
        
    logger.info(f"Applying failure scenario: {scenario_id}")
    
    if scenario_id == "primary_link_disconnection" or scenario_id == "temporary_interruption":
        return set_interface_state(NS_CLIENT, IP_CONFIG["client_pri_dev"], "down")
        
    elif scenario_id == "primary_gateway_unavailability":
        res = run_in_ns(NS_PRIMARY, "sysctl -w net.ipv4.ip_forward=0")
        return res.success
        
    elif scenario_id == "primary_interface_shutdown":
        return set_interface_state(NS_PRIMARY, IP_CONFIG["primary_srv_dev"], "down")
        
    elif scenario_id == "primary_route_removal":
        # Remove primary route with metric 100
        return delete_route(
            NS_CLIENT,
            IP_CONFIG["target_ip"],
            gateway=IP_CONFIG["primary_gw"],
            dev=IP_CONFIG["client_pri_dev"],
            metric=IP_CONFIG["metric_primary"]
        )
        
    return False

def restore_failure(scenario_id: str) -> bool:
    """Restore normal network operations after a failure scenario."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}")
        
    logger.info(f"Restoring from failure scenario: {scenario_id}")
    
    if scenario_id == "primary_link_disconnection" or scenario_id == "temporary_interruption":
        up_ok = set_interface_state(NS_CLIENT, IP_CONFIG["client_pri_dev"], "up")
        # In Linux, setting interface down flushes associated routes; restore primary route
        route_ok = run_cmd(
            f"ip -n {NS_CLIENT} route replace {IP_CONFIG['target_ip']} via {IP_CONFIG['primary_gw']} dev {IP_CONFIG['client_pri_dev']} metric {IP_CONFIG['metric_primary']}"
        ).success
        return up_ok and route_ok
        
    elif scenario_id == "primary_gateway_unavailability":
        res = run_in_ns(NS_PRIMARY, "sysctl -w net.ipv4.ip_forward=1")
        return res.success
        
    elif scenario_id == "primary_interface_shutdown":
        up_ok = set_interface_state(NS_PRIMARY, IP_CONFIG["primary_srv_dev"], "up")
        route_ok = run_cmd(
            f"ip -n {NS_PRIMARY} route replace {IP_CONFIG['target_ip']} via {IP_CONFIG['server_pri_ip'].split('/')[0]} dev {IP_CONFIG['primary_srv_dev']}"
        ).success
        return up_ok and route_ok
        
    elif scenario_id == "primary_route_removal":
        # Re-add route with metric 100
        return run_cmd(
            f"ip -n {NS_CLIENT} route replace {IP_CONFIG['target_ip']} via {IP_CONFIG['primary_gw']} dev {IP_CONFIG['client_pri_dev']} metric {IP_CONFIG['metric_primary']}"
        ).success
        
    return False
