import datetime
import threading
from flask import current_app
from app.extensions import db
from app.models.incident import Incident
from app.models.incident_action import IncidentAction
from app.models.incident_event import IncidentEvent
from app.services.verification_engine import VerificationEngine
from app.services.socket_service import emit_incident_update
from app.services.providers.docker_provider import DockerProvider
from app.services.providers.windows_service_provider import WindowsServiceProvider
from app.services.providers.process_provider import ProcessProvider
from app.services.providers.database_provider import DatabaseProvider
from app.services.providers.disk_cleanup_provider import DiskCleanupProvider
from app.services.providers.network_provider import NetworkProvider

class RemediationEngine:
    def __init__(self):
        self.providers = [
            DockerProvider(),
            WindowsServiceProvider(),
            ProcessProvider(),
            DatabaseProvider(),
            DiskCleanupProvider(),
            NetworkProvider()
        ]

    def get_provider_for_action(self, action_type: str):
        for provider in self.providers:
            if action_type.upper() in provider.supported_actions:
                return provider
        return None

    def execute(self, incident_id, action_id, app=None):
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
                message=f"Executing safe action: {action.action_type} on target: {action.target}",
                source="remediation-engine",
                level="INFO"
            )
            db.session.add(event)
            db.session.commit()
            emit_incident_update(incident.id)

            provider = self.get_provider_for_action(action.action_type)
            if action.action_type == "NONE":
                action.result = "No action required."
                action.status = "EXECUTED"
            elif provider:
                try:
                    res = provider.execute(action.action_type, action.target)
                    action.result = res.get("message", "")
                    if not res.get("success"):
                        action.error = action.result
                        action.status = "FAILED"
                    else:
                        action.status = "EXECUTED"
                except Exception as e:
                    action.error = str(e)
                    action.status = "FAILED"
            else:
                action.error = f"No provider found for action {action.action_type}."
                action.status = "FAILED"
                
            if action.status == "EXECUTED":
                action.executed_at = datetime.datetime.utcnow()
                incident.status = "VERIFYING"
                
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

                event = IncidentEvent(
                    incident_id=incident.id,
                    message=f"Remediation executed successfully ({action.action_type}). Verification started.",
                    source="remediation-engine",
                    level="INFO"
                )
                db.session.add(event)
                
                # Start Verification
                threading.Thread(target=VerificationEngine.verify_resolution, args=(app, incident_id,)).start()
            else:
                incident.status = "FAILED"
                event = IncidentEvent(
                    incident_id=incident.id,
                    message=f"Remediation failed: {action.error}",
                    source="remediation-engine",
                    level="WARNING"
                )
                db.session.add(event)
                
                # Trigger re-analysis on failure
                from app.services.incident_manager import IncidentManager
                threading.Thread(target=IncidentManager.reanalyze, args=(app, incident.id,)).start()

            db.session.commit()
            emit_incident_update(incident.id)
            return {"success": action.status == "EXECUTED", "action": action.to_dict()}
