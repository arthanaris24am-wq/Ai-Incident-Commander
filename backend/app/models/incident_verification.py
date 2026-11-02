from datetime import datetime
from app.extensions import db

class IncidentVerification(db.Model):
    __tablename__ = "incident_verifications"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.String(20), nullable=False) # e.g. 'PASSED', 'FAILED'
    message = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "result": self.result,
            "message": self.message
        }
