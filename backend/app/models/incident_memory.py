from datetime import datetime
from app.extensions import db

class IncidentMemory(db.Model):
    __tablename__ = "incident_memory"

    id = db.Column(db.Integer, primary_key=True)
    
    incident_type = db.Column(db.String(100), nullable=False, index=True)
    fingerprint = db.Column(db.String(100), nullable=True, index=True)
    
    root_cause = db.Column(db.Text, nullable=True)
    
    successful_action = db.Column(db.String(100), nullable=True)
    success_rate = db.Column(db.Float, default=0.0)
    
    total_occurrences = db.Column(db.Integer, default=1)
    successful_applications = db.Column(db.Integer, default=0)
    failed_applications = db.Column(db.Integer, default=0)
    
    last_occurrence = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_type": self.incident_type,
            "fingerprint": self.fingerprint,
            "root_cause": self.root_cause,
            "successful_action": self.successful_action,
            "success_rate": self.success_rate,
            "total_occurrences": self.total_occurrences,
            "successful_applications": self.successful_applications,
            "failed_applications": self.failed_applications,
            "last_occurrence": self.last_occurrence.strftime("%Y-%m-%d %H:%M:%S") if self.last_occurrence else None
        }
