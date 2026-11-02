import json
from app.extensions import db

class IncidentEvidence(db.Model):
    __tablename__ = "incident_evidence"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    evidence_type = db.Column(db.String(50), nullable=False) # e.g. 'system_metrics', 'docker_status', 'application_logs'
    data = db.Column(db.Text, nullable=False) # JSON representation of the evidence

    def to_dict(self):
        try:
            parsed_data = json.loads(self.data)
        except:
            parsed_data = self.data

        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "type": self.evidence_type,
            "data": parsed_data
        }
