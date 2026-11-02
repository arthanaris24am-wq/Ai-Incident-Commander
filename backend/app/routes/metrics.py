from flask import Blueprint, jsonify

from app.services.metric_service import MetricService

metrics_bp = Blueprint(
    "metrics",
    __name__,
    url_prefix="/api/metrics"
)


@metrics_bp.route("/", methods=["GET"])
def metrics():

    return jsonify(
        MetricService.get_metrics()
    )