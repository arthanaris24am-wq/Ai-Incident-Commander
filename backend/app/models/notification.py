from datetime import datetime

from app.extensions import db


class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    incident_id = db.Column(
        db.Integer,
        db.ForeignKey("incidents.id"),
        nullable=True,
        unique=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    severity = db.Column(
        db.String(20),
        nullable=False,
        default="WARNING"
    )

    source = db.Column(
        db.String(100),
        default="system"
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    incident = db.relationship(
        "Incident",
        backref=db.backref(
            "notification",
            uselist=False
        )
    )

    def to_dict(self):

        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "source": self.source,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }