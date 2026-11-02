import os
from dotenv import load_dotenv

# Ensure env vars are loaded before any other modules are imported
load_dotenv()

from flask import Flask
from flask_cors import CORS

from app.routes import (
    auth_bp,
    metrics_bp,
    incident_bp,
    docker_bp,
    ai_bp,
    log_ai_bp,
    incident_ai_bp,
    notification_bp,
    detection_bp,
    logs_bp,
)

from .config import Config
from .extensions import db, jwt, socketio
from .database import init_db
from .logging_config import setup_logging

from app.services.log_watcher import watch_logs
from app.services.socket_service import start_socket_service

from app.detection.service import start_detection_service


def create_app():

    app = Flask(__name__)

    # --------------------------------------------------------
    # Logging Configuration
    # --------------------------------------------------------
    setup_logging(app)

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    app.config.from_object(Config)

    # --------------------------------------------------------
    # Extensions
    # --------------------------------------------------------

    CORS(app)

    db.init_app(app)

    jwt.init_app(app)

    socketio.init_app(app)

    # --------------------------------------------------------
    # Routes
    # --------------------------------------------------------

    app.register_blueprint(auth_bp)

    app.register_blueprint(metrics_bp)

    app.register_blueprint(incident_bp)

    app.register_blueprint(notification_bp)

    app.register_blueprint(docker_bp)

    app.register_blueprint(ai_bp)

    app.register_blueprint(log_ai_bp)

    app.register_blueprint(incident_ai_bp)

    app.register_blueprint(detection_bp)

    app.register_blueprint(logs_bp)

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    init_db(app)

    # --------------------------------------------------------
    # Background Services
    # --------------------------------------------------------

    if (
        not app.debug
        or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    ):

        start_socket_service()

        watch_logs(app)

        start_detection_service(app)

    # --------------------------------------------------------
    # Home
    # --------------------------------------------------------

    @app.route("/")
    def home():

        return {
            "project": "AI Incident Commander",
            "version": "1.0",
            "status": "Running"
        }

    return app