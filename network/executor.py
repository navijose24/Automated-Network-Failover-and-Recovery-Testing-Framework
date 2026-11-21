"""Command execution utility for Linux networking commands.
Supports direct native execution in Linux/WSL and automatic WSL wrapping when run from Windows.
"""

import sys
import subprocess
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("network_executor")

@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    command: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

def run_cmd(cmd: str, check: bool = False, timeout: Optional[float] = 10.0) -> CommandResult:
    """Execute a Linux networking command.
    
    If running natively on Linux (or inside WSL), runs directly via bash.
    If running on Windows, delegates execution into the Ubuntu WSL environment as root.
    """
    logger.debug(f"[EXEC] {cmd}")
    
    if sys.platform.startswith("linux"):
        # Running directly in Linux / WSL container
        exec_args = ["bash", "-c", cmd]
    elif sys.platform == "win32":
        # Running on Windows host: invoke WSL Ubuntu as root
        exec_args = ["wsl", "-u", "root", "-d", "Ubuntu", "bash", "-c", cmd]
    else:
        raise OSError(f"Unsupported operating system: {sys.platform}")

    try:
        proc = subprocess.run(
            exec_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        res = CommandResult(
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            command=cmd
        )
    except subprocess.TimeoutExpired as te:
        logger.error(f"Command timed out ({timeout}s): {cmd}")
        res = CommandResult(
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            command=cmd
        )
    except Exception as ex:
        logger.error(f"Command execution error: {ex}")
        res = CommandResult(
            returncode=-1,
            stdout="",
            stderr=str(ex),
            command=cmd
        )

    if check and not res.success:
        raise RuntimeError(f"Command failed (exit {res.returncode}): {cmd}\nStderr: {res.stderr}\nStdout: {res.stdout}")

    return res

def run_in_ns(netns: str, cmd: str, check: bool = False, timeout: Optional[float] = 10.0) -> CommandResult:
    """Execute a command inside a specific network namespace."""
    full_cmd = f"ip netns exec {netns} {cmd}"
    return run_cmd(full_cmd, check=check, timeout=timeout)
