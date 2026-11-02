from flask import Blueprint, jsonify

from app.extensions import db
from app.models.incident import Incident
from app.models.notification import Notification


notification_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/notifications"
)


def get_severity(level, message):

    level = (level or "").upper()
    message = (message or "").lower()

    if level in ["CRITICAL", "FATAL"]:
        return "CRITICAL"

    if level == "ERROR":
        return "CRITICAL"

    if "container stopped" in message:
        return "HIGH"

    if level in ["WARNING", "WARN"]:
        return "WARNING"

    if level == "INFO":
        return "WARNING"

    return "WARNING"


def sync_incident_notifications():

    incidents = (
        Incident.query
        .filter_by(status="OPEN")
        .order_by(Incident.timestamp.desc())
        .all()
    )

    for incident in incidents:

        existing = Notification.query.filter_by(
            incident_id=incident.id
        ).first()

        if existing:
            continue

        severity = get_severity(
            incident.level,
            incident.message
        )

        notification = Notification(
            incident_id=incident.id,
            title=f"{severity} Incident",
            message=incident.message,
            severity=severity,
            source=incident.source or "application.log",
            is_read=False
        )

        db.session.add(notification)

    db.session.commit()


@notification_bp.route("/", methods=["GET"])
def get_notifications():

    sync_incident_notifications()

    notifications = (
        Notification.query
        .order_by(Notification.created_at.desc())
        .all()
    )

    return jsonify([
        notification.to_dict()
        for notification in notifications
    ])


@notification_bp.route("/unread-count", methods=["GET"])
def get_unread_count():

    sync_incident_notifications()

    count = (
        Notification.query
        .filter_by(is_read=False)
        .count()
    )

    return jsonify({
        "count": count
    })


@notification_bp.route(
    "/<int:notification_id>/read",
    methods=["PATCH"]
)
def mark_as_read(notification_id):

    notification = Notification.query.get(
        notification_id
    )

    if not notification:

        return jsonify({
            "error": "Notification not found"
        }), 404

    notification.is_read = True

    db.session.commit()

    return jsonify({
        "success": True,
        "notification": notification.to_dict()
    })


@notification_bp.route(
    "/read-all",
    methods=["PATCH"]
)
def mark_all_as_read():

    Notification.query.filter_by(
        is_read=False
    ).update({
        "is_read": True
    })

    db.session.commit()

    return jsonify({
        "success": True
    })


@notification_bp.route(
    "/<int:notification_id>",
    methods=["DELETE"]
)
def delete_notification(notification_id):

    notification = Notification.query.get(
        notification_id
    )

    if not notification:

        return jsonify({
            "error": "Notification not found"
        }), 404

    db.session.delete(notification)

    db.session.commit()

    return jsonify({
        "success": True
    })


@notification_bp.route(
    "/clear-read",
    methods=["DELETE"]
)
def clear_read_notifications():

    Notification.query.filter_by(
        is_read=True
    ).delete()

    db.session.commit()

    return jsonify({
        "success": True
    })