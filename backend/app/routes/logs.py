import os
from flask import Blueprint, jsonify, request
from app.logging_config import get_log_file_path, write_log_line
from app.models.log_event import LogEvent
from app.extensions import db

logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")


@logs_bp.route("/application", methods=["GET"])
def get_application_logs():
    """
    Returns recent lines from logs/application.log.
    """
    log_file = get_log_file_path()
    lines_count = int(request.args.get("lines", 200))

    if not os.path.exists(log_file):
        return jsonify({
            "logs": "Log file not created yet.",
            "lines": []
        })

    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            recent_lines = [line.rstrip() for line in all_lines[-lines_count:]]
            return jsonify({
                "logs": "\n".join(recent_lines),
                "lines": recent_lines,
                "total_lines": len(all_lines)
            })
    except Exception as e:
        return jsonify({
            "error": f"Failed to read application.log: {str(e)}",
            "logs": ""
        }), 500


@logs_bp.route("/events", methods=["GET"])
def get_log_events():
    """
    Returns structured log events stored in the database.
    """
    limit = int(request.args.get("limit", 100))
    events = LogEvent.query.order_by(LogEvent.id.desc()).limit(limit).all()
    return jsonify({
        "events": [event.to_dict() for event in events]
    })


@logs_bp.route("/inject", methods=["POST"])
def inject_log():
    """
    Simulates / injects a log entry into application.log.
    Useful for testing the log watcher, incident detection, and live logs.
    """
    data = request.get_json(silent=True) or {}
    level = data.get("level", "INFO").upper()
    message = data.get("message", "Simulated test log entry.")
    component = data.get("component", "application")

    write_log_line(level=level, message=message, component=component)

    return jsonify({
        "status": "success",
        "message": f"Injected [{level}] log under component '{component}'."
    })


@logs_bp.route("/clear", methods=["DELETE", "POST"])
def clear_application_logs():
    """
    Clears the application.log file.
    """
    log_file = get_log_file_path()
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")
        return jsonify({
            "status": "success",
            "message": "application.log cleared."
        })
    except Exception as e:
        return jsonify({
            "error": f"Failed to clear log file: {str(e)}"
        }), 500
