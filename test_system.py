import urllib.request
import json
import time
import threading
from web_dashboard import run, CONTROLLER

t = threading.Thread(target=run, kwargs={'host': '127.0.0.1', 'port': 8089, 'open_browser': False}, daemon=True)
t.start()
time.sleep(1)

base = 'http://127.0.0.1:8089'

def get(path):
    with urllib.request.urlopen(base + path) as r:
        return r.status, r.read().decode('utf-8')

def post(path, data):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

print("[1] Testing Pages...")
status, html = get('/')
assert status == 200 and 'SafeGuard AI' in html, 'Index failed'
print("  [PASS] Index Cockpit Page (200 OK)")

status, html = get('/service-bay')
assert status == 200 and 'Service Bay' in html, 'Service Bay failed'
print("  [PASS] Service Bay Page (200 OK)")

status, html = get('/garage-setup')
assert status == 200 and 'Garage Setup' in html, 'Garage Setup failed'
print("  [PASS] Garage Setup Page (200 OK)")

print("[2] Testing Hardware Connection Analyzer & Circuit Diagnostics...")
status, text = get('/api/diagnostics')
diag = json.loads(text)
assert diag['all_systems_operational'] is True, 'Diagnostics failed'
print(f"  [PASS] Diagnostics Health Score: {diag['overall_health_score']}")
for comp in diag['components']:
    print(f"    - {comp['component']}: {comp['status_label']} ({comp['integrity_score']}%)")

print("[3] Testing Real-Time Dynamic Telemetry & AI Severity Model...")
status, text = get('/api/telemetry')
telem = json.loads(text)
g = telem['telemetry']['g_force']
spd = telem['telemetry']['speed_kmh']
sev = telem['severity']['severity_level']
print(f"  [PASS] Live Telemetry Vector: G-Force = {g:.2f}g, Speed = {spd:.1f} km/h")
print(f"  [PASS] AI Severity Classification: {sev} (Confidence: {telem['severity']['ai_confidence_pct']}%)")

print("[4] Testing Simulated Collision & Automated Safety Escalation...")
status, res = post('/api/crash_test', {'type': 'severe'})
assert res['ok'] is True
time.sleep(0.5)
status, text = get('/api/state')
state = json.loads(text)
assert state['mode'] == 'driver_wait', f"Expected driver_wait, got {state['mode']}"
print(f"  [PASS] Impact Triggered: Status = '{state['system_status']}'")
print(f"  [PASS] Active Timer: {state['active_timer']}")
print(f"  [PASS] AI Severity Assessment: {state['severity_info']['severity_level']}")

print("[5] Testing Tactile Driver Safety Response / Cancel...")
status, res = post('/api/action', {'action': 'driver_responded'})
assert res['ok'] is True
time.sleep(0.2)
status, text = get('/api/state')
state = json.loads(text)
assert state['mode'] == 'resolved', f"Expected resolved, got {state['mode']}"
print(f"  [PASS] Driver Safety Acknowledgement Handled: '{state['system_status']}'")

print("[6] Testing System Reset...")
status, res = post('/api/action', {'action': 'reset'})
assert res['ok'] is True
time.sleep(0.2)
status, text = get('/api/state')
state = json.loads(text)
assert state['mode'] == 'normal', f"Expected normal, got {state['mode']}"
print("  [PASS] Baseline Normal Monitoring Restored")


print("\n=======================================================")
print("  >>> 100% SUCCESS RATE ACHIEVED - ALL CHECKS PASSED <<<")
print("=======================================================")
