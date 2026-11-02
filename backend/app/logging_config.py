import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_log_file_path(app=None):
    if app:
        backend_dir = Path(app.root_path).parent
    else:
        backend_dir = Path(__file__).resolve().parent.parent
    log_dir = backend_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "application.log"


def log_incident_line(incident_id, stage, message, level="INFO"):
    """
    Dedicated logger for incident events and resolutions.
    Outputs to backend/logs/application.log and console.
    """
    logger = logging.getLogger("incident")
    level_upper = (level or "INFO").upper()
    prefix = f"[INCIDENT #{incident_id}] [{stage.upper()}]" if incident_id else f"[{stage.upper()}]"
    formatted_msg = f"{prefix} {message}"
    
    log_method = getattr(logger, level_upper.lower(), logger.info)
    log_method(formatted_msg)


def setup_logging(app):
    """
    Configures logging specifically for Incident Lifecycle, Actions, and Resolutions.
    Does NOT log routine HTTP GET requests or polling spam.
    """
    log_file = get_log_file_path(app)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rotating file handler specifically for incident & application logs
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console stream handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # 1. Configure Flask app logger
    app.logger.setLevel(logging.INFO)
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    # 2. Configure dedicated "incident" logger
    incident_logger = logging.getLogger("incident")
    incident_logger.setLevel(logging.INFO)
    incident_logger.handlers.clear()
    incident_logger.addHandler(file_handler)
    incident_logger.addHandler(console_handler)
    incident_logger.propagate = False

    # 3. Silence noisy HTTP request polling from Werkzeug, EngineIO, SocketIO
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("engineio").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.WARNING)

    # 4. Attach SQLAlchemy listeners to automatically capture incident events & resolutions
    with app.app_context():
        try:
            from sqlalchemy import event
            from app.models.incident_event import IncidentEvent
            from app.models.incident import Incident

            @event.listens_for(IncidentEvent, 'after_insert')
            def on_incident_event_inserted(mapper, connection, target):
                # Avoid logging if source is log file itself to prevent loops
                if getattr(target, 'source', '') == "application.log":
                    return

                stage = getattr(target, 'source', 'EVENT') or 'EVENT'
                level = getattr(target, 'level', 'INFO') or 'INFO'
                msg = getattr(target, 'message', '')
                inc_id = getattr(target, 'incident_id', None)
                
                log_incident_line(inc_id, stage, msg, level=level)

            @event.listens_for(Incident, 'after_update')
            def on_incident_updated(mapper, connection, target):
                # When an incident is resolved, ensure a clear resolution log is recorded
                status = getattr(target, 'status', '')
                if status == "RESOLVED":
                    title = getattr(target, 'title', 'Incident')
                    inc_id = getattr(target, 'id', None)
                    log_incident_line(
                        inc_id,
                        "RESOLVED",
                        f"Incident '{title}' has been successfully RESOLVED and verified.",
                        level="INFO"
                    )

        except Exception as e:
            app.logger.warning("Could not attach SQLAlchemy incident logging listener: %s", e)

    log_incident_line(None, "SYSTEM", "AI Incident Commander logging active. Recording incident detections, lifecycle events, and resolutions.")


def write_log_line(level: str, message: str, component: str = "incident"):
    """
    Directly writes a formatted log line to application.log.
    """
    log_incident_line(None, component, message, level=level)
