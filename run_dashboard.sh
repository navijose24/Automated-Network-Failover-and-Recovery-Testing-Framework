#!/usr/bin/env bash
# Automated Network Failover and Recovery Testing Framework
# Runner Script for Linux / WSL

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo " Starting Automated Network Failover & Recovery Framework"
echo "=========================================================="

# Check root privileges (required for ip netns)
if [ "$EUID" -ne 0 ]; then
    echo "[!] Error: Root privileges required for Linux network namespace configuration."
    echo "    Please run with sudo or as root: sudo ./run_dashboard.sh"
    exit 1
fi

# Activate virtual environment if present
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "[*] Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
fi

echo "[*] Launching Flask Dashboard on http://0.0.0.0:5000..."
echo "[*] Access the dashboard from your browser at: http://localhost:5000"
echo "=========================================================="

python3 app.py
