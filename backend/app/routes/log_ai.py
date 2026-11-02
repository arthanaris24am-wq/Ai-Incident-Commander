from flask import Blueprint, request, jsonify
from app.services.log_ai_service import LogAIService

log_ai_bp = Blueprint(
    "log_ai",
    __name__,
    url_prefix="/api/log-ai"
)


@log_ai_bp.route("/analyze", methods=["POST"])
def analyze():

    print("Content-Type:", request.content_type)
    print("Raw Body:", request.data)

    data = request.get_json(silent=True)

    print("JSON:", data)

    if data is None:
        return jsonify({
            "error": "Invalid JSON received"
        }), 400

    message = data.get("message", "")

    return jsonify(
        LogAIService.analyze_log(message)
    )