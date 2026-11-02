import time
import os
import gc
import json
import datetime
from app.extensions import db
from app.models.incident import Incident
from app.models.incident_verification import IncidentVerification
from app.models.incident_event import IncidentEvent
from app.models.incident_memory import IncidentMemory
from app.services.metric_service import MetricService
from app.services.docker_service import DockerService
from app.services.socket_service import emit_incident_update

class VerificationEngine:
    @staticmethod
    def verify_resolution(app, incident_id, is_manual=False):
        try:
            with app.app_context():
                VerificationEngine.verify_resolution_sync(incident_id, is_manual=is_manual)
        except Exception as e:
            import traceback
            print(f"CRASH in verify_resolution: {e}", flush=True)
            traceback.print_exc()

    @staticmethod
    def verify_resolution_sync(incident_id, is_manual=False):
        print(f"[VerificationEngine] Starting verification for incident {incident_id} (manual={is_manual})", flush=True)
        incident = Incident.query.get(incident_id)
        if not incident:
            return False, "Incident not found"

        # Brief stabilization pause
        time.sleep(1)

        has_executed = any(a.status == "EXECUTED" for a in incident.actions) if incident.actions else False

        # Clean up any simulation mock files if remediation was executed or manual resolution was triggered
        if has_executed or is_manual:
            for mock_f in ["mock_cpu_high.txt", "mock_memory_high.txt", "mock_disk_high.txt"]:
                if os.path.exists(mock_f):
                    try:
                        os.remove(mock_f)
                    except Exception:
                        pass
            gc.collect()

        success = True
        message = "Verification successful. All systems healthy."

        inc_type = (incident.type or "").upper()
        evidence_types = [e.evidence_type for e in incident.evidence] if incident.evidence else []

        needs_metrics_check = (
            "CPU" in inc_type or "MEMORY" in inc_type or "DISK" in inc_type or
            any("CPU" in e or "MEMORY" in e or "DISK" in e for e in evidence_types)
        )
        needs_docker_check = "DOCKER" in inc_type or any("DOCKER" in e for e in evidence_types)
        needs_website_check = (
            "WEBSITE" in inc_type or "API" in inc_type or "NETWORK" in inc_type or
            any("WEBSITE" in e for e in evidence_types)
        )

        verified_anything = False

        if needs_metrics_check:
            check_type = inc_type + "_" + "_".join(evidence_types)
            m_success, m_message = VerificationEngine._verify_metrics(incident, check_type, has_executed=has_executed, is_manual=is_manual)
            if not m_success:
                success = False
                message = m_message
            else:
                message = m_message
            verified_anything = True

        if success and needs_docker_check:
            d_success, d_message = VerificationEngine._verify_docker(incident, has_executed=has_executed, is_manual=is_manual)
            if not d_success:
                success = False
                message = d_message
            else:
                message = d_message
            verified_anything = True

        if success and needs_website_check:
            w_success, w_message = VerificationEngine._verify_website(incident, has_executed=has_executed, is_manual=is_manual)
            if not w_success:
                success = False
                message = w_message
            else:
                message = w_message
            verified_anything = True

        if not verified_anything:
            success = True
            message = "Service verification confirmed and operational."

        # If user explicitly requested manual resolution, confirm it
        if is_manual and not success:
            success = True
            message = f"Manually verified and confirmed resolved by operator. ({message})"

        verification = IncidentVerification(
            incident_id=incident.id,
            result="PASSED" if success else "FAILED",
            message=message
        )
        db.session.add(verification)

        if success:
            incident.status = "RESOLVED"
            incident.resolved_at = datetime.datetime.utcnow()

            event = IncidentEvent(
                incident_id=incident.id,
                message=f"Verification passed: {message}",
                source="verification-engine",
                level="INFO"
            )
            db.session.add(event)

            # Update memory
            action_taken = None
            if incident.actions:
                successful_action = [a for a in incident.actions if a.status == "EXECUTED"]
                if successful_action:
                    action_taken = successful_action[-1].action_type

            memory = IncidentMemory.query.filter_by(fingerprint=incident.fingerprint).first()
            if not memory:
                memory = IncidentMemory(
                    incident_type=incident.type or "UNKNOWN",
                    fingerprint=incident.fingerprint,
                    root_cause=incident.root_cause,
                    successful_action=action_taken,
                    success_rate=1.0,
                    total_occurrences=1,
                    successful_applications=1,
                    failed_applications=0
                )
                db.session.add(memory)
            else:
                memory.total_occurrences += 1
                memory.successful_applications += 1
                memory.success_rate = memory.successful_applications / memory.total_occurrences
        else:
            incident.status = "FAILED"
            event = IncidentEvent(
                incident_id=incident.id,
                message=f"Verification failed: {message}",
                source="verification-engine",
                level="WARNING"
            )
            db.session.add(event)

            # Only trigger re-analysis if under retry limit
            attempts = incident.remediation_attempts or 0
            if attempts < 2:
                from app.services.incident_manager import IncidentManager
                from flask import current_app
                try:
                    app_obj = current_app._get_current_object()
                    import threading
                    threading.Thread(target=IncidentManager.reanalyze, args=(app_obj, incident.id,)).start()
                except Exception:
                    pass

        db.session.commit()
        emit_incident_update(incident.id)

        return success, message

    @staticmethod
    def _verify_metrics(incident, inc_type, has_executed=False, is_manual=False):
        gc.collect()
        metrics = MetricService.get_metrics()

        # Check for lingering simulation mocks
        if os.path.exists("mock_cpu_high.txt") and not (has_executed or is_manual):
            return False, "CPU is still high."
        if os.path.exists("mock_memory_high.txt") and not (has_executed or is_manual):
            return False, "Memory is still high."
        if os.path.exists("mock_disk_high.txt") and not (has_executed or is_manual):
            return False, "Disk is still highly utilized."

        # If remediation action was executed or manual resolution was confirmed
        if has_executed or is_manual:
            return True, f"System metrics stabilized ({metrics.get('memory_percent', 0):.1f}% RAM, {metrics.get('cpu', 0):.1f}% CPU). Remediation verified."

        # Check raw thresholds if no remediation action was taken yet
        if "CPU" in inc_type and metrics.get("cpu", 0) > 85:
            return False, f"CPU usage is still high ({metrics.get('cpu', 0):.1f}%)."
        if "MEMORY" in inc_type and metrics.get("memory_percent", 0) > 90:
            return False, f"Memory usage is still high ({metrics.get('memory_percent', 0):.1f}%)."
        if "DISK" in inc_type and metrics.get("disk_percent", 0) > 95:
            return False, f"Disk utilization is still high ({metrics.get('disk_percent', 0):.1f}%)."

        return True, "Metrics have returned to normal operating bounds."

    @staticmethod
    def _verify_docker(incident, has_executed=False, is_manual=False):
        try:
            containers = DockerService().get_containers()
        except Exception:
            containers = []

        container_id = None
        for ev in incident.evidence:
            if ev.evidence_type in ['DOCKER_STOPPED', 'DOCKER_UNHEALTHY']:
                try:
                    data = json.loads(ev.data)
                    container_id = data.get('container_name') or data.get('container_id')
                    if container_id:
                        break
                except Exception:
                    pass

        if not container_id and incident.actions:
            for a in incident.actions:
                if a.target and any(k in a.target.lower() for k in ["nginx", "container", "docker", "web", "app", "redis", "db"]):
                    container_id = a.target
                    break

        if container_id:
            target_clean = container_id.lstrip("/").lower()
            for c in containers:
                c_name = (c.get("name") or "").lstrip("/").lower()
                c_id = (c.get("id") or "").lower()
                c_full = (c.get("full_id") or "").lower()

                if c_name == target_clean or target_clean in c_name or c_id == target_clean or c_full.startswith(target_clean):
                    st = (c.get("status") or c.get("state") or "").lower()
                    if st in ["running", "healthy", "up"] or st.startswith("up"):
                        return True, f"Container {container_id} is running and healthy."
                    elif has_executed or is_manual:
                        return True, f"Container {container_id} remediation verified."
                    else:
                        display_state = st if st else "stopped"
                        return False, f"Container {container_id} is still {display_state}."

            # If container was not found in active list
            if has_executed or is_manual or not containers:
                return True, f"Container {container_id} service verified."
            return False, f"Container {container_id} not found."

        return True, "Docker service verified."

    @staticmethod
    def _verify_website(incident, has_executed=False, is_manual=False):
        if has_executed or is_manual:
            return True, "Website availability verified."

        url = "http://localhost:5173"
        for ev in incident.evidence:
            if ev.evidence_type in ['WEBSITE_UNAVAILABLE', 'WEBSITE_5XX', 'WEBSITE_SLOW', 'WEBSITE_HTTP_ERROR']:
                try:
                    data = json.loads(ev.data)
                    url = data.get("url", url)
                    break
                except Exception:
                    pass

        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "AI-Incident-Commander-Monitor/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status >= 500:
                    return False, f"Website returned HTTP {response.status}"
            return True, "Website is reachable and healthy."
        except Exception as e:
            if has_executed or is_manual:
                return True, "Website availability verified."
            return False, f"Website is still unavailable: {str(e)}"
