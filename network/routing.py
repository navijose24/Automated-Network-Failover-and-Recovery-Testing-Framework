"""Routing table management and path inspection."""

import json
from typing import Dict, Any, List, Optional
from network.executor import run_cmd

def get_routes(netns: str) -> List[Dict[str, Any]]:
    """List all routes configured in a network namespace.
    
    Linux equivalent:
    ip -n <netns> -j route show
    """
    cmd = f"ip -n {netns} -j route show"
    res = run_cmd(cmd)
    if not res.success or not res.stdout:
        return []
    
    try:
        data = json.loads(res.stdout)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []

def get_active_route(netns: str, target_ip: str) -> Dict[str, Any]:
    """Determine the active next-hop and interface selected by the kernel route cache.
    
    Linux equivalent:
    ip -n <netns> -j route get <target_ip>
    """
    cmd = f"ip -n {netns} -j route get {target_ip}"
    res = run_cmd(cmd)
    
    result = {
        "target": target_ip,
        "gateway": None,
        "dev": None,
        "src": None,
        "active_path": "UNKNOWN",
        "raw": res.stdout
    }
    
    if not res.success or not res.stdout:
        return result
        
    try:
        data = json.loads(res.stdout)
        if data and isinstance(data, list):
            entry = data[0]
            dev = entry.get("dev", "")
            gateway = entry.get("gateway", "")
            src = entry.get("prefsrc", "")
            
            # Identify active path name based on device
            if "c_p" in dev or "10.0.1" in gateway:
                active_path = "PRIMARY"
            elif "c_b" in dev or "10.0.2" in gateway:
                active_path = "BACKUP"
            else:
                active_path = dev.upper() or "UNKNOWN"
                
            result.update({
                "gateway": gateway,
                "dev": dev,
                "src": src,
                "active_path": active_path
            })
            return result
    except Exception:
        pass
        
    # Fallback parsing
    out = res.stdout
    if "dev" in out:
        parts = out.split()
        if "dev" in parts:
            dev_idx = parts.index("dev") + 1
            if dev_idx < len(parts):
                result["dev"] = parts[dev_idx]
                if "c_p" in result["dev"]:
                    result["active_path"] = "PRIMARY"
                elif "c_b" in result["dev"]:
                    result["active_path"] = "BACKUP"
        if "via" in parts:
            via_idx = parts.index("via") + 1
            if via_idx < len(parts):
                result["gateway"] = parts[via_idx]
                
    return result

def replace_route(netns: str, destination: str, gateway: str, dev: str, metric: int) -> bool:
    """Replace an existing route with a new gateway, interface, or metric.
    
    Linux equivalent:
    ip -n <netns> route replace <destination> via <gateway> dev <dev> metric <metric>
    """
    cmd = f"ip -n {netns} route replace {destination} via {gateway} dev {dev} metric {metric}"
    res = run_cmd(cmd)
    return res.success

def add_route(netns: str, destination: str, gateway: str, dev: str, metric: Optional[int] = None) -> bool:
    """Add a new route to the kernel routing table.
    
    Linux equivalent:
    ip -n <netns> route add <destination> via <gateway> dev <dev> [metric <metric>]
    """
    metric_clause = f"metric {metric}" if metric is not None else ""
    cmd = f"ip -n {netns} route add {destination} via {gateway} dev {dev} {metric_clause}".strip()
    res = run_cmd(cmd)
    return res.success

def delete_route(netns: str, destination: str, gateway: Optional[str] = None, dev: Optional[str] = None, metric: Optional[int] = None) -> bool:
    """Delete a specific route from the routing table.
    
    Linux equivalent:
    ip -n <netns> route del <destination> [via <gateway>] [dev <dev>] [metric <metric>]
    """
    parts = [f"ip -n {netns} route del {destination}"]
    if gateway:
        parts.append(f"via {gateway}")
    if dev:
        parts.append(f"dev {dev}")
    if metric is not None:
        parts.append(f"metric {metric}")
    cmd = " ".join(parts)
    res = run_cmd(cmd)
    return res.success
