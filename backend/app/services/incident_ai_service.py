from app.extensions import db
from app.models.incident import Incident
from app.models.incident_action import IncidentAction
from app.services.ai_service import AIService
from app.services.socket_service import emit_incident_update

class IncidentAIService:
    @staticmethod
    def analyze_incident(incident_id):
        incident = Incident.query.get(incident_id)
        if not incident:
            return None

        # Transition to INVESTIGATING
        from app.models.incident_event import IncidentEvent
        incident.status = "INVESTIGATING"
        event_inv = IncidentEvent(
            incident_id=incident.id,
            message="AI investigation started.",
            source="ai-service",
            level="INFO"
        )
        db.session.add(event_inv)
        db.session.commit()
        emit_incident_update(incident.id)

        # Fetch fresh evidence before passing to AI
        from app.services.metric_service import MetricService
        from app.services.docker_service import DockerService
        
        fresh_evidence = []
        try:
            metrics = MetricService.get_metrics()
            fresh_evidence.append({
                "type": "SYSTEM_METRICS",
                "data": metrics
            })
        except Exception as e:
            print(f"Error getting metrics: {e}")
        
        try:
            containers = DockerService().get_containers()
            fresh_evidence.append({
                "type": "DOCKER_CONTAINERS",
                "data": containers
            })
        except Exception as e:
            print(f"Error getting docker containers: {e}")
        
        # Also grab some recent logs
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_file = os.path.join(backend_dir, "logs", "application.log")
        
        recent_logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as file:
                    lines = file.readlines()
                    recent_logs = [l.strip() for l in lines[-50:] if l.strip()]
            except:
                pass
        
        if recent_logs:
            fresh_evidence.append({
                "type": "RECENT_LOGS",
                "data": recent_logs
            })
            
        # Add fresh evidence as new DB records so UI sees it
        from app.models.incident_evidence import IncidentEvidence
        import json
        for ev in fresh_evidence:
            new_ev = IncidentEvidence(
                incident_id=incident.id,
                evidence_type="FRESH_" + ev["type"],
                data=json.dumps(ev["data"])
            )
            db.session.add(new_ev)
        
        db.session.commit()

        # Gather data
        incident_data = incident.to_dict()
        evidence_data = [e.to_dict() for e in incident.evidence]
        events_data = [e.to_dict() for e in incident.events]

        # Call AI Service
        ai_response = AIService.analyze_incident(incident_data, evidence_data, events_data)

        # Update Incident
        incident.root_cause = ai_response.get("root_cause")
        incident.confidence = ai_response.get("confidence")
        
        # Save AI detailed reasoning as evidence
        import json
        from app.models.incident_evidence import IncidentEvidence
        ai_evidence = IncidentEvidence(
            incident_id=incident.id,
            evidence_type="AI_REASONING",
            data=json.dumps({
                "reasoning_steps": ai_response.get("reasoning_steps", []),
                "solutions": ai_response.get("solutions", [])
            })
        )
        db.session.add(ai_evidence)

        # Get best solution
        recommended_action = ai_response.get("recommended_action")
        best_solution = next((s for s in ai_response.get("solutions", []) if s.get("action") == recommended_action), None)
        
        if best_solution:
            incident.recommendation = f"{best_solution.get('summary')} (Success prob: {best_solution.get('success_probability') * 100}%)"
            risk_level = best_solution.get("risk_level", "LOW").upper()
        else:
            incident.recommendation = "Review manually"
            risk_level = "LOW"
            
        has_action = bool(recommended_action and recommended_action.lower() != "none")
        incident.status = "ACTION_REQUIRED" if has_action else "OPEN"
        
        event_comp = IncidentEvent(
            incident_id=incident.id,
            message="AI investigation completed. Root cause identified.",
            source="ai-service",
            level="INFO"
        )
        db.session.add(event_comp)
        
        # Save Action if one is recommended
        if has_action:
            action = IncidentAction(
                incident_id=incident.id,
                action_type=recommended_action,
                description=best_solution.get("summary") if best_solution else ai_response.get("summary"),
                risk_level=risk_level,
                status="PENDING"
            )
            
            # Phase 10: Automatic Remediation (Confidence-based execution)
            auto_execute = False
            if best_solution:
                if not best_solution.get("requires_approval") and risk_level == "LOW" and best_solution.get("success_probability", 0) >= 0.8:
                    auto_execute = True
                    action.status = "APPROVED"
                    
            db.session.add(action)
            db.session.commit()
            
            if auto_execute:
                from app.services.action_executor import ActionExecutor
                from flask import current_app
                # Need app context because we might be in a background thread
                app = current_app._get_current_object()
                import threading
                threading.Thread(target=ActionExecutor.execute, args=(incident.id, action.id, app)).start()
        else:
            db.session.commit()
        
        # Notify clients
        emit_incident_update(incident.id)

        return incident