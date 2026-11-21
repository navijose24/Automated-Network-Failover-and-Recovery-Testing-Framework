@echo off
REM Automated Network Failover and Recovery Testing Framework
REM Windows Launcher via WSL2 Ubuntu

echo ==========================================================
echo  Launching Network Failover Testing Framework in WSL2
echo ==========================================================
echo Starting Flask Backend with Root privileges inside Ubuntu...
echo.

wsl -u root -d Ubuntu bash -c "cd '/mnt/d/git/Network Eng/s1/acn/project/Automated-Network-Failover-and-Recovery-Testing-Framework' && ./run_dashboard.sh"

pause
