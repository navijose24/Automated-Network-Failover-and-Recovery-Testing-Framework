"""Network Topology Manager: provisions, verifies, and manages isolated virtual network namespaces."""

import logging
from typing import Dict, Any, Tuple
from config import (
    NS_CLIENT, NS_PRIMARY, NS_BACKUP, NS_SERVER,
    ALL_NAMESPACES, IP_CONFIG
)
from network.executor import run_cmd, run_in_ns
from network.cleanup import cleanup_topology
from network.routing import get_active_route

logger = logging.getLogger("network_topology")

class TopologyManager:
    """Manages the creation, state inspection, and teardown of the dual-path network topology."""
    
    def __init__(self):
        self.ip_cfg = IP_CONFIG

    def setup_topology(self) -> Tuple[bool, str]:
        """Provisions the 4 network namespaces, veth interface pairs, IP addresses, 
        kernel forwarding, and dual-metric routes.
        
        Returns:
            Tuple[bool, str]: (Success flag, descriptive message or error)
        """
        logger.info("Initializing network topology...")
        
        # 1. Clean up any existing stale namespaces
        cleanup_topology()
        
        try:
            # 2. Create namespaces
            for ns in ALL_NAMESPACES:
                run_cmd(f"ip netns add {ns}", check=True)
                run_cmd(f"ip -n {ns} link set lo up", check=True)
                
            # 3. Create Virtual Ethernet (veth) pairs
            # Primary Path: Client <-> Primary Router
            run_cmd(f"ip link add {self.ip_cfg['client_pri_dev']} type veth peer name {self.ip_cfg['primary_cli_dev']}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['client_pri_dev']} netns {NS_CLIENT}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['primary_cli_dev']} netns {NS_PRIMARY}", check=True)
            
            # Primary Path: Primary Router <-> Server
            run_cmd(f"ip link add {self.ip_cfg['primary_srv_dev']} type veth peer name {self.ip_cfg['server_pri_dev']}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['primary_srv_dev']} netns {NS_PRIMARY}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['server_pri_dev']} netns {NS_SERVER}", check=True)
            
            # Backup Path: Client <-> Backup Router
            run_cmd(f"ip link add {self.ip_cfg['client_bak_dev']} type veth peer name {self.ip_cfg['backup_cli_dev']}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['client_bak_dev']} netns {NS_CLIENT}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['backup_cli_dev']} netns {NS_BACKUP}", check=True)
            
            # Backup Path: Backup Router <-> Server
            run_cmd(f"ip link add {self.ip_cfg['backup_srv_dev']} type veth peer name {self.ip_cfg['server_bak_dev']}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['backup_srv_dev']} netns {NS_BACKUP}", check=True)
            run_cmd(f"ip link set {self.ip_cfg['server_bak_dev']} netns {NS_SERVER}", check=True)

            # 4. Assign IP addresses and enable interfaces
            # Client
            run_cmd(f"ip -n {NS_CLIENT} addr add {self.ip_cfg['client_pri_ip']} dev {self.ip_cfg['client_pri_dev']}", check=True)
            run_cmd(f"ip -n {NS_CLIENT} addr add {self.ip_cfg['client_bak_ip']} dev {self.ip_cfg['client_bak_dev']}", check=True)
            run_cmd(f"ip -n {NS_CLIENT} link set {self.ip_cfg['client_pri_dev']} up", check=True)
            run_cmd(f"ip -n {NS_CLIENT} link set {self.ip_cfg['client_bak_dev']} up", check=True)

            # Primary Router
            run_cmd(f"ip -n {NS_PRIMARY} addr add {self.ip_cfg['primary_cli_ip']} dev {self.ip_cfg['primary_cli_dev']}", check=True)
            run_cmd(f"ip -n {NS_PRIMARY} addr add {self.ip_cfg['primary_srv_ip']} dev {self.ip_cfg['primary_srv_dev']}", check=True)
            run_cmd(f"ip -n {NS_PRIMARY} link set {self.ip_cfg['primary_cli_dev']} up", check=True)
            run_cmd(f"ip -n {NS_PRIMARY} link set {self.ip_cfg['primary_srv_dev']} up", check=True)

            # Backup Router
            run_cmd(f"ip -n {NS_BACKUP} addr add {self.ip_cfg['backup_cli_ip']} dev {self.ip_cfg['backup_cli_dev']}", check=True)
            run_cmd(f"ip -n {NS_BACKUP} addr add {self.ip_cfg['backup_srv_ip']} dev {self.ip_cfg['backup_srv_dev']}", check=True)
            run_cmd(f"ip -n {NS_BACKUP} link set {self.ip_cfg['backup_cli_dev']} up", check=True)
            run_cmd(f"ip -n {NS_BACKUP} link set {self.ip_cfg['backup_srv_dev']} up", check=True)

            # Server (Destination)
            run_cmd(f"ip -n {NS_SERVER} addr add {self.ip_cfg['server_pri_ip']} dev {self.ip_cfg['server_pri_dev']}", check=True)
            run_cmd(f"ip -n {NS_SERVER} addr add {self.ip_cfg['server_bak_ip']} dev {self.ip_cfg['server_bak_dev']}", check=True)
            run_cmd(f"ip -n {NS_SERVER} addr add {self.ip_cfg['target_cidr']} dev lo", check=True)
            run_cmd(f"ip -n {NS_SERVER} link set {self.ip_cfg['server_pri_dev']} up", check=True)
            run_cmd(f"ip -n {NS_SERVER} link set {self.ip_cfg['server_bak_dev']} up", check=True)

            # 5. Enable IP Forwarding on Intermediate Routers
            run_in_ns(NS_PRIMARY, "sysctl -w net.ipv4.ip_forward=1", check=True)
            run_in_ns(NS_BACKUP, "sysctl -w net.ipv4.ip_forward=1", check=True)

            # 6. Configure Forward and Return Routes
            # Intermediate Routers to Target Destination
            run_cmd(f"ip -n {NS_PRIMARY} route add {self.ip_cfg['target_ip']} via {self.ip_cfg['server_pri_ip'].split('/')[0]} dev {self.ip_cfg['primary_srv_dev']}", check=True)
            run_cmd(f"ip -n {NS_BACKUP} route add {self.ip_cfg['target_ip']} via {self.ip_cfg['server_bak_ip'].split('/')[0]} dev {self.ip_cfg['backup_srv_dev']}", check=True)

            # Server Return Routes to Client Subnets
            run_cmd(f"ip -n {NS_SERVER} route add 10.0.1.0/24 via {self.ip_cfg['primary_srv_ip'].split('/')[0]} dev {self.ip_cfg['server_pri_dev']}", check=True)
            run_cmd(f"ip -n {NS_SERVER} route add 10.0.2.0/24 via {self.ip_cfg['backup_srv_ip'].split('/')[0]} dev {self.ip_cfg['server_bak_dev']}", check=True)

            # Client Routes with Priorities (Metric 100 for Primary, Metric 200 for Backup)
            run_cmd(f"ip -n {NS_CLIENT} route add {self.ip_cfg['target_ip']} via {self.ip_cfg['primary_gw']} dev {self.ip_cfg['client_pri_dev']} metric {self.ip_cfg['metric_primary']}", check=True)
            run_cmd(f"ip -n {NS_CLIENT} route add {self.ip_cfg['target_ip']} via {self.ip_cfg['backup_gw']} dev {self.ip_cfg['client_bak_dev']} metric {self.ip_cfg['metric_backup']}", check=True)

            # 7. Verify Connectivity
            verified, msg = self.verify_topology()
            if not verified:
                return False, f"Topology initialized but verification failed: {msg}"

            return True, "Topology successfully created, routed, and verified."
            
        except Exception as ex:
            logger.error(f"Failed to create topology: {ex}")
            cleanup_topology()
            return False, str(ex)

    def verify_topology(self) -> Tuple[bool, str]:
        """Verify bidirectional reachability across both primary and backup paths."""
        target = self.ip_cfg['target_ip']
        
        # Test primary path
        res_pri = run_in_ns(NS_CLIENT, f"ping -c 1 -W 1 -I {self.ip_cfg['client_pri_dev']} {target}")
        if not res_pri.success:
            return False, f"Primary path ping failed from client ({self.ip_cfg['client_pri_dev']}) to {target}"
            
        # Test backup path
        res_bak = run_in_ns(NS_CLIENT, f"ping -c 1 -W 1 -I {self.ip_cfg['client_bak_dev']} {target}")
        if not res_bak.success:
            return False, f"Backup path ping failed from client ({self.ip_cfg['client_bak_dev']}) to {target}"

        return True, "Both primary and backup paths verified successfully."

    def get_topology_status(self) -> Dict[str, Any]:
        """Query current live status of all topology nodes, interfaces, and active routing path."""
        # Check active route
        route_info = get_active_route(NS_CLIENT, self.ip_cfg['target_ip'])
        
        # Check interfaces
        from network.interfaces import get_interface_info
        
        interfaces = {
            "client_pri": get_interface_info(NS_CLIENT, self.ip_cfg['client_pri_dev']),
            "client_bak": get_interface_info(NS_CLIENT, self.ip_cfg['client_bak_dev']),
            "primary_cli": get_interface_info(NS_PRIMARY, self.ip_cfg['primary_cli_dev']),
            "primary_srv": get_interface_info(NS_PRIMARY, self.ip_cfg['primary_srv_dev']),
            "backup_cli": get_interface_info(NS_BACKUP, self.ip_cfg['backup_cli_dev']),
            "backup_srv": get_interface_info(NS_BACKUP, self.ip_cfg['backup_srv_dev']),
            "server_pri": get_interface_info(NS_SERVER, self.ip_cfg['server_pri_dev']),
            "server_bak": get_interface_info(NS_SERVER, self.ip_cfg['server_bak_dev']),
        }
        
        # Path health status
        pri_healthy = (
            interfaces["client_pri"].get("operstate") == "UP" and
            interfaces["primary_cli"].get("operstate") == "UP" and
            interfaces["primary_srv"].get("operstate") == "UP" and
            interfaces["server_pri"].get("operstate") == "UP"
        )
        
        bak_healthy = (
            interfaces["client_bak"].get("operstate") == "UP" and
            interfaces["backup_cli"].get("operstate") == "UP" and
            interfaces["backup_srv"].get("operstate") == "UP" and
            interfaces["server_bak"].get("operstate") == "UP"
        )
        
        return {
            "namespaces": ALL_NAMESPACES,
            "target_ip": self.ip_cfg['target_ip'],
            "active_path": route_info.get("active_path", "UNKNOWN"),
            "active_device": route_info.get("dev"),
            "active_gateway": route_info.get("gateway"),
            "primary_path_status": "UP" if pri_healthy else "DOWN",
            "backup_path_status": "UP" if bak_healthy else "DOWN",
            "interfaces": interfaces,
            "route_info": route_info
        }

    def teardown(self) -> bool:
        """Safely destroy virtual network namespaces."""
        return cleanup_topology()
