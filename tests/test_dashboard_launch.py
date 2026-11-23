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

print("Flask starting... polling for readiness on http://127.0.0.1:5000")

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

# Poll until Flask is ready
t_deadline = time.time() + 25.0
ready = False
while time.time() < t_deadline:
    if proc.poll() is not None:
        out, _ = proc.communicate()
        print("FLASK DIED! Output:\n", out.decode()[:3000])
        sys.exit(1)
    code, _ = curl("http://127.0.0.1:5000/api/status")
    if code == 200:
        ready = True
        break
    time.sleep(1.0)

if not ready:
    print("Flask failed to become ready within 25 seconds.")

for path in ["/", "/topology", "/simulation", "/monitoring", "/analysis", "/history", "/reports", "/api/status"]:
    code, body = curl(f"http://127.0.0.1:5000{path}")
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
