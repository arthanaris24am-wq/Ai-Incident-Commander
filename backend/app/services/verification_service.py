from app.services.verification_engine import VerificationEngine

class VerificationService:
    @staticmethod
    def verify_resolution(app, incident_id, is_manual=False):
        return VerificationEngine.verify_resolution(app, incident_id, is_manual=is_manual)

    @staticmethod
    def verify_resolution_sync(incident_id, is_manual=False):
        return VerificationEngine.verify_resolution_sync(incident_id, is_manual=is_manual)
