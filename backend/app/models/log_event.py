from datetime import datetime
from app.extensions import db

class LogEvent(db.Model):
    __tablename__ = "log_events"

    id = db.Column(db.Integer, primary_key=True)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    level = db.Column(db.String(20), nullable=False, index=True)
    
    source = db.Column(db.String(100), nullable=True, index=True)
    
    component = db.Column(db.String(100), nullable=True, index=True)
    
    message = db.Column(db.Text, nullable=False)
    
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "level": self.level,
            "source": self.source,
            "component": self.component,
            "message": self.message,
            "incident_id": self.incident_id
        }
