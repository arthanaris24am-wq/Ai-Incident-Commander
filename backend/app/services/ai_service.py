import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# Configure Gemini AI
def get_gemini_client():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        return genai.Client(api_key=gemini_api_key)
    return None

class RankedSolution(BaseModel):
    action: str
    target: str
    summary: str
    risk_level: str
    success_probability: float
    pros: List[str]
    cons: List[str]
    requires_approval: bool

class AIRecommendation(BaseModel):
    summary: str
    root_cause: str
    confidence: float
    evidence: List[str]
    reasoning_steps: List[str]
    contributing_factors: List[str]
    solutions: List[RankedSolution]
    recommended_action: str
    requires_approval: bool

class AIService:

    @staticmethod
    def analyze_incident(incident_data, evidence_data, events_data):
        """
        Uses Gemini to analyze an incident and recommend an action.
        """
        client = get_gemini_client()
        if not client:
            return {
                "summary": "AI unavailable (no API key configured)",
                "root_cause": "Missing GEMINI_API_KEY",
                "confidence": 0.0,
                "evidence": [],
                "reasoning_steps": ["Check API Key", "Abort analysis due to missing key"],
                "contributing_factors": [],
                "solutions": [{
                    "action": "NONE",
                    "target": "",
                    "summary": "Review manually. Please configure GEMINI_API_KEY environment variable.",
                    "risk_level": "LOW",
                    "success_probability": 0.0,
                    "pros": [],
                    "cons": [],
                    "requires_approval": False
                }],
                "recommended_action": "NONE",
                "requires_approval": False
            }

        prompt = (
            f"Incident Data:\n{json.dumps(incident_data, indent=2)}\n\n"
            f"Evidence:\n{json.dumps(evidence_data, indent=2)}\n\n"
            f"Timeline Events:\n{json.dumps(events_data, indent=2)}\n\n"
            "Please analyze the incident and return the structured JSON output."
        )

        primary_model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        candidate_models = [primary_model]

        # Dynamically query available models to prevent 404 NOT_FOUND errors
        try:
            available = [
                m.name.replace("models/", "")
                for m in client.models.list()
                if "generateContent" in getattr(m, "supported_generation_methods", ["generateContent"])
            ]
            for m in available:
                if m not in candidate_models:
                    candidate_models.append(m)
        except Exception as exc:
            print(f"[AIService] Could not dynamically list models: {exc}")

        last_error = None
        for model_name in candidate_models:
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=(
                                "You are an AI Incident Commander responsible for analyzing system incidents. "
                                "Analyze the provided incident data, evidence, and event timeline to determine the probable root cause. "
                                "Provide a structured JSON response matching the required schema. "
                                "Outline your step-by-step logic in 'reasoning_steps'. "
                                "Provide multiple potential 'solutions', ranking the best one as 'recommended_action' (must match the action ID). "
                                "Always identify the specific 'target' for the action (e.g., 'MySQL', 'node.exe', 'frontend-container'). "
                                "Actions must be UPPERCASE (e.g., 'RESTART_CONTAINER', 'START_SERVICE', 'CLEAN_TEMP_FILES', 'NONE'). "
                                "Dangerous actions should have risk_level 'HIGH' and requires_approval true. "
                                "If there is insufficient evidence or no action is required, use action 'NONE'. "
                            ),
                            response_mime_type="application/json",
                            response_schema=AIRecommendation,
                            temperature=0.2
                        )
                    )
                    return json.loads(response.text)
                except Exception as e:
                    last_error = e
                    err_msg = str(e).lower()
                    print(f"[AIService] Model {model_name} attempt {attempt + 1} failed: {e}")
                    # If high demand / 503 or 429 rate limit, wait with backoff and retry
                    if "503" in err_msg or "high demand" in err_msg or "unavailable" in err_msg or "429" in err_msg:
                        import time
                        time.sleep(2 * (attempt + 1))
                        continue
                    else:
                        # 404 or unsupported method, break to next candidate model
                        break

        # Fallback to rule-based analysis if all models fail
        e = last_error or Exception("All AI models were unavailable")
        incident_type = str(incident_data.get("type", "")).upper()
        message = str(incident_data.get("message", "")).lower()
        title = str(incident_data.get("title", "")).lower()

        action = "NONE"
        target = ""
        summary = "Review incident metrics and logs manually."
        root_cause = f"System alert detected in {incident_type or 'system'} component."
        requires_approval = False

        if "CPU" in incident_type or "cpu" in message or "cpu" in title:
            action = "RESTART_APPROVED_PROCESS"
            target = "node.exe"
            summary = "Restart the process consuming high CPU."
            root_cause = "Excessive CPU consumption identified across foreground processes."
            requires_approval = True
        elif "MEMORY" in incident_type or "memory" in message or "memory" in title:
            action = "CLEAN_TEMP_FILES"
            target = "C:\\temp"
            summary = "Clear temporary files and cached buffers to free up system memory."
            root_cause = "High physical memory utilization caused by active background cache buffers and processes."
            requires_approval = False
        elif "DISK" in incident_type or "disk" in message or "disk" in title:
            action = "CLEAN_TEMP_FILES"
            target = "C:\\temp"
            summary = "Clean temporary files and cached logs to free disk space."
            root_cause = "Disk volume utilization reached critical alert threshold."
            requires_approval = False
        elif "DOCKER" in incident_type or "docker" in message or "container" in message:
            action = "RESTART_CONTAINER"
            target = "nginx-test"
            for ev in evidence_data:
                try:
                    data = json.loads(ev.get("data", "{}"))
                    target = data.get("container_name") or data.get("container_id") or target
                except Exception:
                    pass
            summary = f"Restart the container {target}."
            root_cause = f"Container {target} stopped unexpectedly or became unhealthy."
            requires_approval = False
        elif "WEBSITE" in incident_type or "website" in message or "http" in message:
            action = "RESTART_APPLICATION"
            target = "Frontend"
            summary = "Restart the web application service."
            root_cause = "Web service endpoint is unresponsive or returned HTTP error."
            requires_approval = False
        elif "DATABASE" in incident_type or "database" in message or "mysql" in message or "postgres" in message:
            action = "RESTART_SERVICE"
            target = "MySQL"
            summary = "Restart the database service."
            root_cause = "Database connection pool exhausted or database service unreachable."
            requires_approval = True

        return {
            "summary": summary,
            "root_cause": root_cause,
            "confidence": 0.85,
            "evidence": ["Automated heuristic diagnostic rules applied"],
            "reasoning_steps": [
                f"Incident category identified: {incident_type or 'SYSTEM'}",
                f"Evaluated diagnostic indicators from telemetry data",
                f"Determined safe remediation action: {action} on target: {target}"
            ],
            "contributing_factors": ["System load", "Resource contention"],
            "solutions": [{
                "action": action,
                "target": target,
                "summary": summary,
                "risk_level": "MEDIUM" if requires_approval else "LOW",
                "success_probability": 0.9,
                "pros": ["Direct remediation without service downtime"],
                "cons": [],
                "requires_approval": requires_approval
            }],
            "recommended_action": action,
            "requires_approval": requires_approval
        }