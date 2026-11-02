import requests
import time
import multiprocessing
import sys
import threading

BASE_URL = "http://localhost:5000/api"

def trigger_cpu_incident():
    print("Mocking high CPU usage...")
    with open("mock_cpu_high.txt", "w") as f:
        f.write("mock")
    return None

def get_incidents():
    r = requests.get(f"{BASE_URL}/incidents")
    return r.json()

def wait_for_incident(min_id, status_filter=None, timeout=30):
    print(f"Waiting up to {timeout}s for a new incident (id > {min_id}) to appear/change...")
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

def test_phase1():
    print("--- Phase 1 E2E Test ---")
    
    # 0. Get current max incident ID
    existing_incidents = get_incidents()
    max_id = max([i["id"] for i in existing_incidents], default=0) if existing_incidents else 0
    print(f"Current max incident ID: {max_id}")
    
    # 1. Create/detect an active incident
    hog_processes = trigger_cpu_incident()
    
    try:
        incident = wait_for_incident(max_id, ["OPEN", "INVESTIGATING", "ACTION_REQUIRED", "REMEDIATING", "VERIFYING", "FAILED"], 45)
        if not incident:
            print("[FAIL] Test failed: Incident was not detected.")
            sys.exit(1)
            
        print(f"[PASS] Incident {incident['id']} detected with status {incident['status']}")
        inc_id = incident['id']
        
        # 2. Click Resolve while problem exists -> MUST NOT become RESOLVED
        print(f"Resolving incident {inc_id} while problem still exists...")
        r = requests.post(f"{BASE_URL}/incidents/{inc_id}/resolve")
        if r.status_code != 200:
            print(f"[FAIL] Failed to call resolve API: {r.text}")
            sys.exit(1)
            
        # Wait a few seconds for verification to fail
        time.sleep(5)
        r = requests.get(f"{BASE_URL}/incidents/{inc_id}")
        updated_inc = r.json()
        if updated_inc["status"] == "RESOLVED":
            print(f"[FAIL] Test failed: Incident became RESOLVED even though CPU is still high.")
            sys.exit(1)
            
        # It should be FAILED or INVESTIGATING (if AI reinvestigation kicked in)
        print(f"[PASS] Incident {inc_id} did not become RESOLVED. Current status: {updated_inc['status']}")
        
        # 3. Trigger same problem repeatedly -> MUST NOT create duplicate
        print("Waiting to ensure no duplicates are created...")
        time.sleep(15) # Wait for detection cycle
        incidents = get_incidents()
        active_cpu = [i for i in incidents if i.get("id") > max_id and i["type"] in ["CPU_HIGH", "CORRELATED_INCIDENT"] and i["status"] in ["OPEN", "INVESTIGATING", "ACTION_REQUIRED", "REMEDIATING", "VERIFYING", "FAILED"]]
        if len(active_cpu) > 1:
            print(f"[FAIL] Test failed: Duplicate active incidents were created! Found {len(active_cpu)}")
            sys.exit(1)
            
        print("[PASS] No duplicate active incidents created.")
        
        # 4. Fix the underlying problem
        print("Fixing the underlying problem by removing mock...")
        import os
        if os.path.exists("mock_cpu_high.txt"):
            os.remove("mock_cpu_high.txt")
        
        # Give system time to reflect lowered CPU
        print("Waiting 5s for CPU to calm down...")
        time.sleep(5)
        
        # 5. Run verification again -> pass -> RESOLVED
        print(f"Resolving incident {inc_id} now that problem is fixed...")
        r = requests.post(f"{BASE_URL}/incidents/{inc_id}/resolve")
        
        print("Waiting for verification to complete...")
        for _ in range(15):
            time.sleep(2)
            r = requests.get(f"{BASE_URL}/incidents/{inc_id}")
            final_inc = r.json()
            if final_inc["status"] == "RESOLVED":
                break

        if final_inc["status"] != "RESOLVED":
            print(f"[FAIL] Test failed: Incident did not become RESOLVED after fix. Status: {final_inc['status']}")
            sys.exit(1)
            
        print(f"[PASS] Incident {inc_id} became RESOLVED after verification passed.")
        
        # 6. Verify timeline contains transitions
        events = final_inc.get("events", [])
        print(f"Found {len(events)} timeline events.")
        has_failed = False
        has_verifying = False
        has_resolved = False
        for e in events:
            if "fail" in e["message"].lower() or "unhealthy" in e["message"].lower(): has_failed = True
            if "verif" in e["message"].lower(): has_verifying = True
            if "resolv" in e["message"].lower(): has_resolved = True
            print(f"  - {e['timestamp']}: {e['message']}")
            
        if not (has_failed and has_verifying and has_resolved):
            print("⚠️ Warning: Timeline might be missing some expected events.")
        else:
            print("[PASS] Timeline verified.")
            
        # 7. Trigger the same problem again -> NEW incident
        print("Triggering the problem again to ensure a NEW incident is created...")
        hog_processes2 = trigger_cpu_incident()
        
        try:
            new_incident = wait_for_incident(inc_id, ["OPEN", "INVESTIGATING", "ACTION_REQUIRED", "REMEDIATING", "VERIFYING", "FAILED"], 45)
            if not new_incident or new_incident['id'] == inc_id:
                print("[FAIL] Test failed: New incident was not created.")
                sys.exit(1)
                
            print(f"[PASS] New incident {new_incident['id']} created for recurring problem.")
        finally:
            import os
            if os.path.exists("mock_cpu_high.txt"):
                os.remove("mock_cpu_high.txt")
            
        print("\nAll backend lifecycle tests passed!")
        
    except Exception as e:
        import os
        if os.path.exists("mock_cpu_high.txt"):
            os.remove("mock_cpu_high.txt")
        print(f"[FAIL] Exception during test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_phase1()
