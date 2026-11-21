"""Configuration settings for Automated Network Failover and Recovery Testing Framework."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_PATH = str(BASE_DIR / "failover_framework.db")

# Network Namespaces
NS_CLIENT = "ns_client"
NS_PRIMARY = "ns_primary"
NS_BACKUP = "ns_backup"
NS_SERVER = "ns_server"

ALL_NAMESPACES = [NS_CLIENT, NS_PRIMARY, NS_BACKUP, NS_SERVER]

# Interface and IP configuration
IP_CONFIG = {
    # Client interfaces
    "client_pri_ip": "10.0.1.2/24",
    "client_bak_ip": "10.0.2.2/24",
    "client_pri_dev": "veth_c_p",
    "client_bak_dev": "veth_c_b",
    
    # Primary Router interfaces
    "primary_cli_ip": "10.0.1.1/24",
    "primary_srv_ip": "10.0.3.1/24",
    "primary_cli_dev": "veth_p_c",
    "primary_srv_dev": "veth_p_s",
    
    # Backup Router interfaces
    "backup_cli_ip": "10.0.2.1/24",
    "backup_srv_ip": "10.0.4.1/24",
    "backup_cli_dev": "veth_b_c",
    "backup_srv_dev": "veth_b_s",
    
    # Server / Destination interfaces
    "server_pri_ip": "10.0.3.2/24",
    "server_bak_ip": "10.0.4.2/24",
    "server_pri_dev": "veth_s_p",
    "server_bak_dev": "veth_s_b",
    
    # Destination Target IP (bound on server loopback)
    "target_ip": "10.50.0.1",
    "target_cidr": "10.50.0.1/32",
    
    # Gateways from client perspective
    "primary_gw": "10.0.1.1",
    "backup_gw": "10.0.2.1",
    
    # Routing metrics
    "metric_primary": 100,
    "metric_backup": 200,
    "metric_active_failover": 50,  # Lower metric given to backup during failover
}

# Monitoring and Detection defaults
PROBE_INTERVAL = 0.5            # Seconds between ICMP probes
PROBE_TIMEOUT = 1.0             # Seconds before probe timeout
FAILURE_THRESHOLD = 3           # Consecutive failed probes to confirm failure
FAILBACK_STABILITY_THRESHOLD = 3 # Consecutive successful probes on primary to confirm stability
AUTO_FAILBACK_DEFAULT = False

# Web Application
HOST = "0.0.0.0"
PORT = 5000
DEBUG = False
