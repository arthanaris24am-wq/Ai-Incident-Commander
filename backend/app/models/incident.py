from datetime import datetime
from app.extensions import db


class Incident(db.Model):

    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    level = db.Column(
        db.String(20),
        nullable=False
    )

    severity = db.Column(
        db.String(20),
        default="WARNING"
    )

    type = db.Column(
        db.String(50),
        nullable=True
    )

    title = db.Column(
        db.String(200),
        nullable=True
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    source = db.Column(
        db.String(100),
        default="application.log"
    )

    status = db.Column(
        db.String(20),
        default="OPEN"
    )

    first_seen = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    last_seen = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    fingerprint = db.Column(
        db.String(64),
        nullable=True,
        index=True
    )

    root_cause = db.Column(
        db.Text,
        nullable=True
    )

    confidence = db.Column(
        db.Float,
        nullable=True
    )

    recommendation = db.Column(
        db.Text,
        nullable=True
    )

    resolution = db.Column(
        db.Text,
        nullable=True
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True
    )

    remediation_attempts = db.Column(
        db.Integer,
        default=0
    )

    events = db.relationship(
        "IncidentEvent",
        backref="incident",
        cascade="all, delete-orphan",
        order_by="desc(IncidentEvent.timestamp)"
    )

    evidence = db.relationship(
        "IncidentEvidence",
        backref="incident",
        cascade="all, delete-orphan"
    )

    actions = db.relationship(
        "IncidentAction",
        backref="incident",
        cascade="all, delete-orphan",
        order_by="desc(IncidentAction.created_at)"
    )

    verifications = db.relationship(
        "IncidentVerification",
        backref="incident",
        cascade="all, delete-orphan",
        order_by="desc(IncidentVerification.timestamp)"
    )

    logs = db.relationship(
        "LogEvent",
        backref="incident_ref",
        cascade="all, delete-orphan",
        order_by="desc(LogEvent.timestamp)"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "level": self.level,
            "severity": self.severity,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "status": self.status,
            "first_seen": self.first_seen.strftime("%Y-%m-%d %H:%M:%S") if self.first_seen else None,
            "last_seen": self.last_seen.strftime("%Y-%m-%d %H:%M:%S") if self.last_seen else None,
            "fingerprint": self.fingerprint,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if self.resolved_at else None
        }