"""Interface management and statistics inspection."""

from typing import Dict, Any, List
import json
from network.executor import run_cmd, run_in_ns

def set_interface_state(netns: str, dev: str, state: str) -> bool:
    """Set the state of an interface inside a namespace (up or down).
    
    Linux equivalent:
    ip -n <netns> link set dev <dev> <state>
    """
    state = state.lower()
    if state not in ("up", "down"):
        raise ValueError("State must be 'up' or 'down'")
    cmd = f"ip -n {netns} link set dev {dev} {state}"
    res = run_cmd(cmd)
    return res.success

def get_interface_info(netns: str, dev: str) -> Dict[str, Any]:
    """Retrieve detailed interface information including operational state and MTU.
    
    Linux equivalent:
    ip -n <netns> -j link show dev <dev>
    """
    cmd = f"ip -n {netns} -j link show dev {dev}"
    res = run_cmd(cmd)
    if not res.success or not res.stdout:
        return {"device": dev, "state": "DOWN", "operstate": "DOWN", "exists": False}
    
    try:
        data = json.loads(res.stdout)
        if data and isinstance(data, list):
            entry = data[0]
            return {
                "device": dev,
                "flags": entry.get("flags", []),
                "mtu": entry.get("mtu", 1500),
                "operstate": entry.get("operstate", "UNKNOWN").upper(),
                "address": entry.get("address", ""),
                "exists": True
            }
    except Exception:
        pass
    
    # Fallback to plain text inspection
    state = "UP" if "UP" in res.stdout else "DOWN"
    return {"device": dev, "state": state, "operstate": state, "exists": True}

def get_interface_stats(netns: str, dev: str) -> Dict[str, int]:
    """Retrieve packet and byte counters for an interface.
    
    Linux equivalent:
    ip -n <netns> -s -j link show dev <dev>
    """
    cmd = f"ip -n {netns} -s -j link show dev {dev}"
    res = run_cmd(cmd)
    stats = {
        "rx_bytes": 0, "rx_packets": 0, "rx_errors": 0, "rx_dropped": 0,
        "tx_bytes": 0, "tx_packets": 0, "tx_errors": 0, "tx_dropped": 0
    }
    
    if not res.success or not res.stdout:
        return stats
        
    try:
        data = json.loads(res.stdout)
        if data and isinstance(data, list):
            entry = data[0].get("stats64", {}) or data[0].get("stats", {})
            rx = entry.get("rx", {})
            tx = entry.get("tx", {})
            stats["rx_bytes"] = rx.get("bytes", 0)
            stats["rx_packets"] = rx.get("packets", 0)
            stats["rx_errors"] = rx.get("errors", 0)
            stats["rx_dropped"] = rx.get("dropped", 0)
            stats["tx_bytes"] = tx.get("bytes", 0)
            stats["tx_packets"] = tx.get("packets", 0)
            stats["tx_errors"] = tx.get("errors", 0)
            stats["tx_dropped"] = tx.get("dropped", 0)
    except Exception:
        pass
        
    return stats
