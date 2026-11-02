from flask import current_app
from app.extensions import db
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.services.ai_service import AIService
from app.services.correlation_engine import CorrelationEngine
from app.services.solution_engine import SolutionEngine
from app.services.socket_service import emit_incident_update
from app.models.incident_evidence import IncidentEvidence
from app.models.incident_action import IncidentAction
from app.services.remediation_engine import RemediationEngine
import json
import threading

class IncidentManager:
    @staticmethod
    def _execute_async(app, incident_id):
        with app.app_context():
            IncidentManager.analyze_incident_sync(incident_id)
            
    @staticmethod
    def _reanalyze_async(app, incident_id):
        with app.app_context():
            IncidentManager.analyze_incident_sync(incident_id, is_reanalysis=True)

    @staticmethod
    def analyze_incident(incident_id):
        app = current_app._get_current_object()
        threading.Thread(target=IncidentManager._execute_async, args=(app, incident_id)).start()
        
    @staticmethod
    def reanalyze(app, incident_id):
        threading.Thread(target=IncidentManager._reanalyze_async, args=(app, incident_id)).start()

    @staticmethod
    def analyze_incident_sync(incident_id, is_reanalysis=False):
        incident = Incident.query.get(incident_id)
        if not incident:
            return None

        # Check attempt limits
        if is_reanalysis:
            MAX_ATTEMPTS = 2
            attempts = incident.remediation_attempts or 0
            if attempts >= MAX_ATTEMPTS:
                incident.status = "FAILED"
                event = IncidentEvent(
                    incident_id=incident.id,
                    message="Max remediation attempts reached. Manual intervention required.",
                    source="incident-manager",
                    level="ERROR"
                )
                db.session.add(event)
                db.session.commit()
                emit_incident_update(incident.id)
                return
            incident.remediation_attempts = attempts + 1
            db.session.commit()

        # 1. Start Investigation
        incident.status = "INVESTIGATING"
        msg = "AI re-investigation started." if is_reanalysis else "AI investigation started."
        event_inv = IncidentEvent(
            incident_id=incident.id,
            message=msg,
            source="incident-manager",
            level="INFO"
        )
        db.session.add(event_inv)
        db.session.commit()
        emit_incident_update(incident.id)

        # 2. Correlate / Gather Context
        context = CorrelationEngine.gather_context(incident)
        for c_type, c_data in context.items():
            if c_data:
                new_ev = IncidentEvidence(
                    incident_id=incident.id,
                    evidence_type=f"CONTEXT_{c_type.upper()}",
                    data=json.dumps(c_data)
                )
                db.session.add(new_ev)
        db.session.commit()

        # 3. Analyze with AI
        incident_data = incident.to_dict()
        evidence_data = [e.to_dict() for e in incident.evidence]
        events_data = [e.to_dict() for e in incident.events]

        ai_response = AIService.analyze_incident(incident_data, evidence_data, events_data)

        # Update Incident
        incident.root_cause = ai_response.get("root_cause")
        incident.confidence = ai_response.get("confidence")
        
        # Save AI Reasoning
        ai_evidence = IncidentEvidence(
            incident_id=incident.id,
            evidence_type="AI_REASONING",
            data=json.dumps({
                "reasoning_steps": ai_response.get("reasoning_steps", []),
                "solutions": ai_response.get("solutions", [])
            })
        )
        db.session.add(ai_evidence)

        # 4. Generate & Select Safe Fix
        solution_engine = SolutionEngine()
        best_solution = solution_engine.select_best_solution(ai_response)
        
        has_action = False
        action = None
        
        if best_solution:
            incident.recommendation = f"{best_solution.get('summary')} (Prob: {best_solution.get('success_probability') * 100}%)"
            
            action_type = best_solution.get("action")
            if action_type and action_type.upper() != "NONE":
                has_action = True
                
                # Check for auto remediation
                auto_exec = solution_engine.check_automation_allowance(best_solution, incident.confidence)
                
                action = IncidentAction(
                    incident_id=incident.id,
                    action_type=action_type.upper(),
                    target=best_solution.get("target"),
                    description=best_solution.get("summary"),
                    risk_level=best_solution.get("risk_level", "HIGH").upper(),
                    confidence=best_solution.get("success_probability"),
                    automation_allowed=auto_exec,
                    status="APPROVED" if auto_exec else "PENDING"
                )
                db.session.add(action)
        else:
            incident.recommendation = "Review manually"

        incident.status = "ACTION_REQUIRED" if has_action else "OPEN"
        
        event_comp = IncidentEvent(
            incident_id=incident.id,
            message="AI investigation completed. Safe fix determined.",
            source="incident-manager",
            level="INFO"
        )
        db.session.add(event_comp)
        db.session.commit()
        
        emit_incident_update(incident.id)

        # 5. Automatic Remediation (if allowed)
        if has_action and action and action.status == "APPROVED":
            remediation_engine = RemediationEngine()
            app = current_app._get_current_object()
            threading.Thread(target=remediation_engine.execute, args=(incident.id, action.id, app)).start()
