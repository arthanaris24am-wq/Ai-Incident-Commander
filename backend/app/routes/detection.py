from flask import Blueprint, current_app, jsonify

from app.detection.service import (
    get_detection_service,
)


detection_bp = Blueprint(
    "detection",
    __name__,
    url_prefix="/api/detection",
)


@detection_bp.route(
    "/scan",
    methods=["POST"],
)
def run_detection_scan():

    service = get_detection_service(
        current_app
    )

    findings = service.scan()

    return jsonify({
        "success": True,
        "findings": findings,
        "count": len(findings),
    })


@detection_bp.route(
    "/status",
    methods=["GET"],
)
def detection_status():

    service = get_detection_service(
        current_app
    )

    last_scan = None

    if service.last_scan:

        last_scan = (
            service.last_scan.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    return jsonify({
        "running": service.running,
        "scan_interval_seconds":
            service.scan_interval,
        "monitored_url":
            service.monitored_url,
        "last_scan":
            last_scan,
        "last_findings":
            service.last_findings,
        "finding_count":
            len(service.last_findings),
    })