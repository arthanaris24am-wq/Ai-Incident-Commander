import json
from datetime import datetime
from app.extensions import db

class IncidentAction(db.Model):
    __tablename__ = "incident_actions"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(20), nullable=False, default="SAFE")
    confidence = db.Column(db.Float, nullable=True)
    automation_allowed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime, nullable=True)
    executed_by = db.Column(db.String(100), nullable=True)
    result = db.Column(db.Text, nullable=True)
    error = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "action_type": self.action_type,
            "target": self.target,
            "description": self.description,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "automation_allowed": self.automation_allowed,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "executed_at": self.executed_at.strftime("%Y-%m-%d %H:%M:%S") if self.executed_at else None,
            "executed_by": self.executed_by,
            "result": self.result,
            "error": self.error,
            "duration": self.duration
        }
