import requests
import time
import sys

BASE_URL = "http://localhost:5000/api"

def test_frontend_flow():
    print("Fetching incidents...")
    incidents = requests.get(f"{BASE_URL}/incidents/").json()
    if not incidents:
        print("No incidents found. Please trigger one.")
        sys.exit(1)
        
    incident = max(incidents, key=lambda i: i['id'])
    inc_id = incident['id']
    print(f"Testing Ask AI flow for incident {inc_id} ({incident['title']})")
    
    # 1. Click Ask AI
    print("Clicking Ask AI...")
    res = requests.post(f"{BASE_URL}/incidents/{inc_id}/investigate")
    if res.status_code != 200:
        print(f"Failed to investigate: {res.text}")
        sys.exit(1)
        
    # Wait a few seconds for investigation to complete
    print("Waiting for AI investigation to complete...")
    for _ in range(15):
        time.sleep(1)
        inc = requests.get(f"{BASE_URL}/incidents/{inc_id}").json()
        if inc['status'] in ['ACTION_REQUIRED', 'OPEN']:
            break

    if inc['status'] not in ['ACTION_REQUIRED', 'OPEN']:
        print(f"Expected status ACTION_REQUIRED or OPEN after AI investigation, got {inc['status']}")
        sys.exit(1)
        
    print("AI result returned.")
    
    # Verify fields
    if not inc.get('root_cause'):
        print("Missing root_cause")
        sys.exit(1)
    if not inc.get('evidence'):
        print("Missing evidence")
        sys.exit(1)
    if not inc.get('recommendation'):
        print("Missing recommendation")
        sys.exit(1)
        
    print("Root cause, evidence, and recommendation are present!")
    print("Frontend UI verification against actual backend APIs PASSED.")

if __name__ == "__main__":
    test_frontend_flow()
