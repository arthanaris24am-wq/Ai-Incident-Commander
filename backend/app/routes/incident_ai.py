from flask import Blueprint, jsonify
from app.services.incident_ai_service import IncidentAIService

incident_ai_bp = Blueprint(
    "incident_ai",
    __name__,
    url_prefix="/api/incident-ai"
)


@incident_ai_bp.route("/report", methods=["GET"])
def report():

    return jsonify(
        IncidentAIService.analyze()
    )