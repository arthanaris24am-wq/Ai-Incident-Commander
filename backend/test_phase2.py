import requests
import time
import sys
import os

BASE_URL = "http://localhost:5000/api"

def trigger_cpu_incident():
    print("Mocking high CPU usage...")
    with open("mock_cpu_high.txt", "w") as f:
        f.write("mock")
    return None

def get_incidents():
    r = requests.get(f"{BASE_URL}/incidents")
    if r.status_code != 200:
        return []
    return r.json()

def wait_for_incident(min_id, status_filter=None, timeout=30):
    print(f"Waiting up to {timeout}s for an incident (id > {min_id}) to appear/change...")
    for _ in range(timeout):
        incidents = get_incidents()
        if incidents:
            if status_filter:
                for inc in incidents:
                    if inc.get("id") > min_id and inc.get("status") in status_filter and inc.get("title") in ["Critical CPU Usage", "Correlated System Degradation"]:
                        return inc
            else:
                for inc in incidents:
                    if inc.get("id") > min_id and inc.get("title") in ["Critical CPU Usage", "Correlated System Degradation"]:
                        return inc
        time.sleep(1)
    return None

def test_phase2():
    print("--- Phase 2 E2E Test (Detection -> AI RCA -> Remediation -> Verification -> Resolved) ---")
    
    # 0. Get max id
    existing = get_incidents()
    max_id = max([i["id"] for i in existing], default=0) if existing else 0
    print(f"Current max incident ID: {max_id}")
    
    # 1. Trigger incident
    trigger_cpu_incident()
    
    try:
        # Wait for the AI to complete and incident to become ACTION_REQUIRED
        incident = wait_for_incident(max_id, ["ACTION_REQUIRED", "REMEDIATING", "VERIFYING", "RESOLVED"], 60)
        
        if not incident:
            # Let's see if it's stuck in OPEN or INVESTIGATING
            active = wait_for_incident(max_id, ["OPEN", "INVESTIGATING"], 5)
            if active:
                print(f"[FAIL] Incident stuck in {active['status']}. AI analysis probably failed.")
            else:
                print("[FAIL] Test failed: Incident was not detected.")
            sys.exit(1)
            
        print(f"[PASS] Incident {incident['id']} reached status {incident['status']}")
        inc_id = incident['id']
        
        # 2. Check Explainable RCA (root_cause, recommendation, reasoning_steps)
        r = requests.get(f"{BASE_URL}/incidents/{inc_id}")
        details = r.json()
        
        if not details.get("root_cause"):
            print("[WARN] No root cause found. Did AI analysis run?")
        else:
            print(f"[PASS] AI Root Cause identified: {details['root_cause']}")
            
        if not details.get("recommendation"):
            print("[WARN] No recommendation found.")
        else:
            print(f"[PASS] AI Recommendation provided: {details['recommendation']}")

        # 3. Get pending actions
        actions = details.get("actions", [])
        pending_action = next((a for a in actions if a["status"] in ["PENDING", "APPROVED"]), None)
        
        if not pending_action:
            print("[FAIL] No pending or approved actions found for remediation.")
            sys.exit(1)
            
        print(f"[PASS] Found action to execute: {pending_action['action_type']} (Status: {pending_action['status']})")
        
        # 4. If PENDING, approve it
        if pending_action["status"] == "PENDING":
            print(f"Approving action {pending_action['id']}...")
            r = requests.post(f"{BASE_URL}/incidents/{inc_id}/actions/{pending_action['id']}/approve")
            if r.status_code != 200:
                print(f"[FAIL] Failed to approve action: {r.text}")
                sys.exit(1)
            print("[PASS] Action approved.")
            
        # Before executing the action, we manually remove the mock to simulate that the action "fixed" the CPU
        print("Simulating that the action fixes the CPU problem by removing mock...")
        if os.path.exists("mock_cpu_high.txt"):
            os.remove("mock_cpu_high.txt")
            
        # 5. Execute Action
        print(f"Executing action {pending_action['id']}...")
        r = requests.post(f"{BASE_URL}/incidents/{inc_id}/actions/{pending_action['id']}/execute")
        if r.status_code != 200:
            print(f"[FAIL] Failed to execute action: {r.text}")
            sys.exit(1)
            
        print("[PASS] Action executed successfully.")
        
        # 6. Wait for verification to complete -> RESOLVED
        print("Waiting for verification to complete and incident to resolve...")
        resolved = False
        for _ in range(20):
            time.sleep(2)
            r = requests.get(f"{BASE_URL}/incidents/{inc_id}")
            final_inc = r.json()
            if final_inc["status"] == "RESOLVED":
                resolved = True
                break
                
        if not resolved:
            print(f"[FAIL] Test failed: Incident did not become RESOLVED. Status: {final_inc['status']}")
            sys.exit(1)
            
        print(f"[PASS] Incident {inc_id} verified and RESOLVED!")
        print("\nAll Phase 2 lifecycle tests passed!")
        
    except Exception as e:
        if os.path.exists("mock_cpu_high.txt"):
            os.remove("mock_cpu_high.txt")
        print(f"[FAIL] Exception during test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_phase2()
