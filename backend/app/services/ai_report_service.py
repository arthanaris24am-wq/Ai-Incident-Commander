from app.models.incident import Incident

class AIReportService:

    @staticmethod
    def generate_report():
        # Fetch actual incidents from the database
        active_incidents = Incident.query.filter(Incident.status != "RESOLVED").all()
        active_count = len(active_incidents)
        critical_count = len([inc for inc in active_incidents if inc.severity == "CRITICAL"])
        
        # Populate automated actions from the database
        from app.models.incident_action import IncidentAction
        from app.models.incident_verification import IncidentVerification
        
        automated_actions = [
            a.to_dict() for a in IncidentAction.query.filter(
                IncidentAction.status.in_(["EXECUTING", "EXECUTED", "APPROVED", "PENDING"])
            ).limit(10).all()
        ]
        
        recent_verifications = IncidentVerification.query.order_by(IncidentVerification.timestamp.desc()).limit(1).all()
        verification_status = recent_verifications[0].result if recent_verifications else "Unknown"

        
        overall_health = "HEALTHY"
        if critical_count > 0:
            overall_health = "CRITICAL"
        elif active_count > 0:
            overall_health = "WARNING"

        detected_problems = [inc.title or inc.message for inc in active_incidents]
        root_causes = [inc.root_cause for inc in active_incidents if inc.root_cause]
        recommended_actions = [inc.recommendation for inc in active_incidents if inc.recommendation]
        
        # Calculate a mock confidence based on how many have root causes vs total
        confidence = 100
        if active_count > 0:
            confidence = int((len(root_causes) / active_count) * 100) if active_count else 0
            if confidence == 0:
                confidence = 50 # Base confidence if we have active incidents but no RCA yet
        
        return {
            "overall_health": overall_health,
            "confidence": confidence,
            "active_incidents": active_count,
            "critical_incidents": critical_count,
            "detected_problems": detected_problems,
            "root_causes": root_causes,
            "recommended_actions": recommended_actions,
            "automated_actions": automated_actions,
            "verification_status": verification_status,
            "system_summary": f"System is currently {overall_health.lower()} with {active_count} active incidents."
        }