"""Quick launch test: start Flask, verify endpoints, then exit."""
import subprocess
import time
import sys
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

proc = subprocess.Popen(
    [sys.executable, "app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

print("Flask starting... waiting 12s for topology setup")
time.sleep(12)

# Check if process is still alive
if proc.poll() is not None:
    out, _ = proc.communicate()
    print("FLASK DIED! Output:")
    print(out.decode()[:3000])
    sys.exit(1)

# Test endpoints
import urllib.request
import urllib.error
import json

results = {}

def curl(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)

for path in ["/", "/topology", "/simulation", "/monitoring", "/analysis", "/history", "/reports", "/api/status"]:
    code, body = curl(f"http://localhost:5000{path}")
    results[path] = code
    print(f"  {code}  {path}  {body[:80] if code == 200 else body[:200]}")

# Print flask log
proc.terminate()
out, _ = proc.communicate(timeout=5)
log = out.decode()
print("\n--- Flask startup log ---")
print(log[:3000])

all_ok = all(c == 200 for c in results.values())
print("\nALL PAGES OK:", all_ok)
sys.exit(0 if all_ok else 1)
