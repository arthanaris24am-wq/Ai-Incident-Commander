import json
import datetime
import threading
from flask import current_app
from app.extensions import db
from app.models.incident import Incident
from app.models.incident_action import IncidentAction
from app.models.incident_event import IncidentEvent
from app.services.docker_control import DockerControlService
from app.services.verification_service import VerificationService
from app.services.socket_service import emit_incident_update

class ActionExecutor:
    @staticmethod
    def execute(incident_id, action_id, app=None):
        if app is None:
            app = current_app._get_current_object()

        with app.app_context():
            action = IncidentAction.query.filter_by(id=action_id, incident_id=incident_id).first()
            if not action:
                return {"success": False, "error": "Action not found"}

            if action.status not in ["APPROVED", "PENDING"]:
                return {"success": False, "error": f"Action is {action.status}, cannot execute."}

            if action.risk_level == "HIGH" and action.status != "APPROVED":
                return {"success": False, "error": "High risk actions must be approved first."}

            action.status = "EXECUTING"
            
            incident = Incident.query.get(incident_id)
            incident.status = "REMEDIATING"
            
            event = IncidentEvent(
                incident_id=incident.id,
                message=f"Executing action: {action.action_type}",
                source="system",
                level="INFO"
            )
            db.session.add(event)
            db.session.commit()
            emit_incident_update(incident.id)

            container_id = None
            for ev in incident.evidence:
                if ev.evidence_type == 'DOCKER_STOPPED':
                    try:
                        data = json.loads(ev.data)
                        container_id = data.get('container_name') or data.get('container_id')
                        if container_id: break
                    except:
                        pass
                        
            if not container_id:
                if "container" in action.description.lower():
                    words = action.description.split()
                    for w in words:
                        if w.isalnum() and len(w) > 4:
                            container_id = w
                            break

            docker_service = DockerControlService()
            try:
                if action.action_type == "restart_container" and container_id:
                    res = docker_service.restart_container(container_id)
                    action.result = res["message"]
                elif action.action_type == "start_container" and container_id:
                    res = docker_service.start_container(container_id)
                    action.result = res["message"]
                elif action.action_type == "stop_container" and container_id:
                    res = docker_service.stop_container(container_id)
                    action.result = res["message"]
                elif action.action_type == "none":
                    action.result = "No action taken."
                else:
                    action.error = "Unknown action type or missing container context."
                    action.status = "FAILED"
            except Exception as e:
                action.error = str(e)
                action.status = "FAILED"
                
            if action.status != "FAILED":
                action.status = "EXECUTED"
                action.executed_at = datetime.datetime.utcnow()
                
                # Clean up any simulation mock files so metrics reflect remediation
                import os
                import gc
                for mock_f in ["mock_cpu_high.txt", "mock_memory_high.txt", "mock_disk_high.txt"]:
                    if os.path.exists(mock_f):
                        try:
                            os.remove(mock_f)
                        except Exception:
                            pass
                gc.collect()

                incident.status = "VERIFYING"
                
                event = IncidentEvent(
                    incident_id=incident.id,
                    message=f"Remediation executed successfully ({action.action_type}). Verification started.",
                    source="system",
                    level="INFO"
                )
                db.session.add(event)
                
                threading.Thread(target=VerificationService.verify_resolution, args=(app, incident_id,)).start()
                
            db.session.commit()
            emit_incident_update(incident.id)
            return {"success": action.status == "EXECUTED", "action": action.to_dict()}
