# AI Incident Commander

## Testing and Development Workarounds

To successfully run the end-to-end tests (`test_phase1.py`, `test_phase2.py`, and `test_frontend.py`), the following configurations and workarounds were applied:

### 1. Database State
The testing scripts assume a clean database state to check for duplicate incident creations. To ensure tests do not fail with "Duplicate active incidents", the existing `backend/instance/incident_commander.db` was either removed or backed up before running tests.

### 2. Frontend Requirement for Backend Tests
The backend's `VerificationEngine` requires the frontend to be reachable (defaulting to `http://localhost:5173`) to verify the resolution of incidents containing `WEBSITE_UNAVAILABLE` evidence. Therefore, the Vite frontend must be running (`npm run dev` in `frontend/`) **before** executing `test_phase1.py` or `test_phase2.py`.

### 3. Asynchronous AI Investigation Wait Loop
The script `test_frontend.py` was updated. Previously, it triggered `POST /api/incidents/{id}/investigate` and immediately checked the incident status, expecting it to be `ACTION_REQUIRED`. Because the investigation is asynchronous, the backend correctly sets the status to `INVESTIGATING` first. A wait loop with a timeout was added to `test_frontend.py` to allow the AI to complete its investigation and transition the incident to `ACTION_REQUIRED`.

### 4. AI Model Fallback
The Gemini API configuration uses `gemini-3.8-flash`. Due to occasional `503 UNAVAILABLE` errors from the AI service under high demand, the system utilizes its robust rule-based fallback mechanism. This correctly handles the AI outage without causing application crashes, keeping the incident investigation and remediation flow intact.

### How to Run Tests
1. Start the frontend: `cd frontend && npm install && npm run dev`
2. Start the backend: `cd backend && python run.py` (ensure `.env` has a valid `GEMINI_API_KEY`)
3. Run tests in separate terminal from backend directory:
   - `python test_phase1.py`
   - `python test_phase2.py`
   - `python test_frontend.py`
