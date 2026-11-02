import threading
import time

from app.extensions import socketio
from app.services.metric_service import MetricService


def metric_stream():
    while True:
        metrics = MetricService.get_metrics()
        socketio.emit(
            "metrics",
            metrics
        )
        time.sleep(2)


def start_socket_service():
    thread = threading.Thread(
        target=metric_stream,
        daemon=True
    )
    thread.start()


def emit_incident_update(incident_id):
    """
    Emit a websocket event when an incident is updated.
    """
    socketio.emit(
        "incident_update",
        {"incident_id": incident_id}
    )