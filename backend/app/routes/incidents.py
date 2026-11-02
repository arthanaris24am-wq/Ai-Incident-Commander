from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.incident import Incident
from app.models.incident_action import IncidentAction
from app.services.incident_manager import IncidentManager
from app.services.docker_control import DockerControlService
import datetime

incident_bp = Blueprint(
    "incidents",
    __name__,
    url_prefix="/api/incidents"
)


@incident_bp.route("/", methods=["GET"], strict_slashes=False)
def get_incidents():
    incidents = Incident.query.order_by(Incident.last_seen.desc()).all()
    return jsonify([incident.to_dict() for incident in incidents])


@incident_bp.route("/<int:incident_id>", methods=["GET"])
def get_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    data = incident.to_dict()
    data["events"] = [e.to_dict() for e in incident.events]
    data["evidence"] = [e.to_dict() for e in incident.evidence]
    data["actions"] = [a.to_dict() for a in incident.actions]
    data["verifications"] = [v.to_dict() for v in incident.verifications]
    return jsonify(data)


@incident_bp.route("/<int:incident_id>/investigate", methods=["GET", "POST"])
def investigate_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    IncidentManager.analyze_incident(incident.id)
    return jsonify({"message": "Analysis started"})


@incident_bp.route("/<int:incident_id>/actions/<int:action_id>/approve", methods=["POST"])
def approve_action(incident_id, action_id):
    action = IncidentAction.query.filter_by(id=action_id, incident_id=incident_id).first_or_404()
    
    if action.status != "PENDING":
        return jsonify({"error": f"Action is {action.status}, cannot approve."}), 400
        
    action.status = "APPROVED"
    db.session.commit()
    return jsonify(action.to_dict())


@incident_bp.route("/<int:incident_id>/actions/<int:action_id>/execute", methods=["POST"])
def execute_action(incident_id, action_id):
    from app.services.remediation_engine import RemediationEngine
    engine = RemediationEngine()
    result = engine.execute(incident_id, action_id)
    
    if not result.get("success") and "error" in result:
        # Check if it was a validation error vs execution error
        if "cannot execute" in result["error"] or "approved first" in result["error"]:
            return jsonify({"error": result["error"]}), 400
        
    return jsonify(result.get("action", {"error": result.get("error")}))

@incident_bp.route("/<int:incident_id>/resolve", methods=["POST"])
def resolve_incident(incident_id):
    from app.models.incident_event import IncidentEvent
    from app.services.verification_engine import VerificationEngine
    import threading
    
    incident = Incident.query.get_or_404(incident_id)
    incident.status = "VERIFYING"
    
    event = IncidentEvent(
        incident_id=incident.id,
        message="Manual resolution requested by operator. Verification started.",
        source="operator",
        level="INFO"
    )
    db.session.add(event)
    db.session.commit()
    
    from flask import current_app
    app = current_app._get_current_object()
    threading.Thread(target=VerificationEngine.verify_resolution, args=(app, incident_id, True)).start()
    
    return jsonify(incident.to_dict())

@incident_bp.route("/resolve-all", methods=["POST"])
def resolve_all_incidents():
    from app.models.incident import Incident
    from app.services.verification_engine import VerificationEngine
    
    active_incidents = Incident.query.filter(Incident.status != "RESOLVED").all()
    resolved_count = 0
    
    for inc in active_incidents:
        VerificationEngine.verify_resolution_sync(inc.id, is_manual=True)
        resolved_count += 1
        
    return jsonify({
        "message": f"Successfully resolved and verified {resolved_count} incident(s).",
        "resolved_count": resolved_count
    })


@incident_bp.route("/<int:incident_id>/timeline", methods=["GET"])
def get_incident_timeline(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return jsonify([e.to_dict() for e in incident.events])

@incident_bp.route("/<int:incident_id>/solutions", methods=["GET"])
def get_incident_solutions(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return jsonify([a.to_dict() for a in incident.actions])

@incident_bp.route("/<int:incident_id>/verification", methods=["GET"])
def get_incident_verification(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return jsonify([v.to_dict() for v in incident.verifications])

@incident_bp.route("/<int:incident_id>/solve", methods=["POST"])
def solve_incident_alias(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    IncidentManager.analyze_incident(incident.id)
    return jsonify({"message": "Analysis started"})

@incident_bp.route("/<int:incident_id>/reanalyze", methods=["GET", "POST"])
def reanalyze_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    from flask import current_app
    app_obj = current_app._get_current_object()
    import threading
    threading.Thread(target=IncidentManager.reanalyze, args=(app_obj, incident.id,)).start()
    return jsonify({"message": "Re-analysis started"})

@incident_bp.route("/<int:incident_id>/approve-remediation", methods=["POST"])
def approve_remediation_alias(incident_id):
    data = request.get_json(silent=True) or {}
    action_id = data.get("action_id")
    if not action_id:
        return jsonify({"error": "action_id required"}), 400
    
    action = IncidentAction.query.filter_by(id=action_id, incident_id=incident_id).first_or_404()
    if action.status == "PENDING":
        action.status = "APPROVED"
        db.session.commit()
    return jsonify(action.to_dict())