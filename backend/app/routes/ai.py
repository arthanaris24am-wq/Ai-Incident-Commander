from flask import Blueprint, jsonify

from app.services.ai_report_service import AIReportService
from app.services.gemini_service import gemini_service

ai_bp = Blueprint(
    "ai",
    __name__,
    url_prefix="/api/ai"
)

@ai_bp.route("/health", methods=["GET"])
def health():
    return jsonify(gemini_service.health_check()), 200

@ai_bp.route("/models", methods=["GET"])
def models():
    try:
        client = gemini_service.client
        if not client:
            return jsonify({"error": "No client"}), 500
        model_list = [m.name for m in client.models.list()]
        return jsonify({"models": model_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_bp.route("/report", methods=["GET"])
def report():

    try:
        result = AIReportService.generate_report()

        return jsonify(result), 200

    except Exception as e:

        print("AI REPORT ERROR:", e)

        return jsonify({
            "confidence": 0,
            "overall_health": "UNKNOWN",
            "detected_problems": [
                "AI report generation failed."
            ],
            "recommended_actions": [
                "Check backend logs."
            ],
            "error": str(e)
        }), 500