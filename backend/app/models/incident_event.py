from datetime import datetime
from app.extensions import db

class IncidentEvent(db.Model):
    __tablename__ = "incident_events"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100), nullable=True)
    level = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "message": self.message,
            "source": self.source,
            "level": self.level
        }
