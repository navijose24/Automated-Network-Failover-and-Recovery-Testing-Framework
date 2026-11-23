"""Connectivity probe executor using native Linux ICMP ping."""

import re
import time
from dataclasses import dataclass
from typing import Optional
from config import NS_CLIENT, IP_CONFIG
from network.executor import run_in_ns
from network.routing import get_active_route

@dataclass
class ProbeResult:
    timestamp: float
    sequence_num: int
    target_ip: str
    success: bool
    rtt_ms: Optional[float]
    active_interface: str
    active_path: str
    raw_output: str

# Regex to capture ping RTT: e.g. "time=0.045 ms"
PING_TIME_REGEX = re.compile(r"time[=<]([0-9.]+)\s*ms", re.IGNORECASE)

def send_probe(sequence_num: int = 1, target_ip: Optional[str] = None, timeout: float = 1.0) -> ProbeResult:
    """Send an individual ICMP echo request from ns_client to the target IP.
    
    Linux equivalent:
    ip netns exec ns_client ping -c 1 -W <timeout> <target_ip>
    """
    target = target_ip or IP_CONFIG["target_ip"]
    now = time.time()
    
    # Check current active route before/with probe
    route_info = get_active_route(NS_CLIENT, target)
    dev = route_info.get("dev") or "unknown"
    path = route_info.get("active_path") or "UNKNOWN"

    w_sec = max(1, int(round(timeout)))
    cmd = f"ping -c 1 -W {w_sec} {target}"
    res = run_in_ns(NS_CLIENT, cmd, timeout=timeout + 1.0)
    
    success = False
    rtt = None
    
    if res.success:
        match = PING_TIME_REGEX.search(res.stdout)
        if match:
            try:
                rtt = float(match.group(1))
                success = True
            except ValueError:
                pass
        else:
            # If ping succeeded but time regex failed, treat as 0.1 ms fallback
            success = True
            rtt = 0.1
            
    return ProbeResult(
        timestamp=now,
        sequence_num=sequence_num,
        target_ip=target,
        success=success,
        rtt_ms=rtt,
        active_interface=dev,
        active_path=path,
        raw_output=res.stdout if res.success else res.stderr or res.stdout
    )

def test_interface_probe(dev: str, target_ip: Optional[str] = None, timeout: float = 1.0) -> bool:
    """Send an ICMP probe bound specifically to an interface to test that path specifically.
    
    Linux equivalent:
    ip netns exec ns_client ping -c 1 -W <timeout> -I <dev> <target_ip>
    """
    target = target_ip or IP_CONFIG["target_ip"]
    w_sec = max(1, int(round(timeout)))
    cmd = f"ping -c 1 -W {w_sec} -I {dev} {target}"
    res = run_in_ns(NS_CLIENT, cmd, timeout=timeout + 1.0)
    return res.success and ("1 packets transmitted, 1 received" in res.stdout or "time=" in res.stdout)
