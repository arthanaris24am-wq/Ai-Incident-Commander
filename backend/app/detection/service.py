import hashlib
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psutil

from app.extensions import db
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.models.incident_evidence import IncidentEvidence
from app.models.notification import Notification

from app.detection.rules import (
    CPU_WARNING_THRESHOLD,
    CPU_CRITICAL_THRESHOLD,
    MEMORY_WARNING_THRESHOLD,
    MEMORY_CRITICAL_THRESHOLD,
    DISK_WARNING_THRESHOLD,
    DISK_CRITICAL_THRESHOLD,
    WEBSITE_TIMEOUT_SECONDS,
    WEBSITE_SLOW_RESPONSE_SECONDS,
    UNHEALTHY_DOCKER_STATUSES,
    MAX_LOG_LINES,
    ERROR_KEYWORDS,
    DATABASE_ERROR_KEYWORDS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
)

from app.detection.state import DetectionState


try:
    import docker
except ImportError:
    docker = None


class DetectionService:
    """
    Automatic detection engine.

    Responsibilities:

    - Monitor CPU, memory and disk.
    - Monitor Docker containers.
    - Monitor the configured website.
    - Detect new application errors.
    - Prevent duplicate incidents.
    - Create notifications.
    - Maintain active detection state.
    """

    def __init__(self, app):

        self.app = app

        self.running = False

        self.thread = None

        self.last_scan = None

        self.last_findings = []

        self.scan_lock = threading.Lock()

        self.state = DetectionState()

        self.scan_interval = int(
            os.getenv(
                "DETECTION_INTERVAL_SECONDS",
                DEFAULT_SCAN_INTERVAL_SECONDS,
            )
        )

        self.monitored_url = os.getenv(
            "MONITORED_URL",
            "http://localhost:5173",
        )

        self.log_file = self._get_log_file()

        self.app.logger.info(
            "Detection service initialized"
        )

    # ========================================================
    # PATHS
    # ========================================================

    def _get_log_file(self):

        backend_root = Path(
            self.app.root_path
        ).parent

        return (
            backend_root
            / "logs"
            / "application.log"
        )

    # ========================================================
    # FINGERPRINT
    # ========================================================

    @staticmethod
    def fingerprint(finding):

        stable_data = "|".join([
            finding.get("type", ""),
            finding.get("source", ""),
            finding.get("level", ""),
            finding.get("fingerprint_key", ""),
        ])

        return hashlib.sha256(
            stable_data.encode("utf-8")
        ).hexdigest()

    # ========================================================
    # MAIN SCAN
    # ========================================================

    def scan(self):

        if not self.scan_lock.acquire(
            blocking=False
        ):

            return self.last_findings

        try:

            findings = []

            findings.extend(
                self._check_system_metrics()
            )

            findings.extend(
                self._check_docker()
            )

            findings.extend(
                self._check_website()
            )

            findings.extend(
                self._check_application_logs()
            )

            processed_findings = []
            current_fingerprints = set()

            for finding in findings:
                fingerprint = self.fingerprint(finding)
                current_fingerprints.add(fingerprint)

                result = (
                    self._process_finding(
                        finding
                    )
                )

                if result:

                    processed_findings.append(
                        result
                    )

            # Cleanup active_findings that are no longer detected
            active_keys = list(self.state.active_findings.keys())
            for fp in active_keys:
                finding = self.state.active_findings[fp]["finding"]
                if finding["type"] not in {"APPLICATION_ERROR", "DATABASE_ERROR"}:
                    if fp not in current_fingerprints:
                        self.state.deactivate(fp)
                        self._auto_resolve_incident_if_recovered(finding, fp)

            self.last_scan = datetime.utcnow()

            self.last_findings = findings

            return findings

        finally:

            self.scan_lock.release()

    def _auto_resolve_incident_if_recovered(self, finding, fingerprint):
        """
        When a system metric or monitored target returns to healthy parameters,
        automatically verify and resolve any associated active incident so that
        the incidents list stays consistent with live monitoring.
        """
        try:
            finding_type = finding.get("type", "")
            
            active_incidents = Incident.query.filter(
                Incident.status.in_(["OPEN", "INVESTIGATING", "ACTION_REQUIRED", "REMEDIATING", "VERIFYING", "FAILED"])
            ).all()

            for incident in active_incidents:
                inc_type = (incident.type or "").upper()
                msg = (incident.message or "").upper()
                evidence_types = [e.evidence_type for e in incident.evidence] if incident.evidence else []

                matches = (
                    incident.fingerprint == fingerprint or
                    incident.type == finding_type or
                    finding_type in evidence_types or
                    ("CPU" in finding_type and ("CPU" in inc_type or "CPU" in msg)) or
                    ("MEMORY" in finding_type and ("MEMORY" in inc_type or "MEMORY" in msg)) or
                    ("DISK" in finding_type and ("DISK" in inc_type or "DISK" in msg)) or
                    ("WEBSITE" in finding_type and ("WEBSITE" in inc_type or "WEBSITE" in msg))
                )

                if matches:
                    from app.services.verification_engine import VerificationEngine
                    success, v_msg = VerificationEngine.verify_resolution_sync(incident.id, is_manual=False)
                    if success:
                        self.app.logger.info(
                            f"[AUTO-RESOLVE] Incident #{incident.id} ({incident.title}) auto-resolved: {v_msg}"
                        )
                        from app.services.socket_service import emit_incident_update
                        emit_incident_update(incident.id)
        except Exception as err:
            self.app.logger.warning(f"Error during auto-resolve check: {err}")

    # ========================================================
    # SYSTEM METRICS
    # ========================================================

    def _check_system_metrics(self):

        findings = []

        try:
            from app.services.metric_service import MetricService
            metrics = MetricService.get_metrics()

            cpu = float(metrics.get("cpu", 0.0))
            memory = float(metrics.get("memory_percent", 0.0))
            disk = float(metrics.get("disk_percent", 0.0))

            # ------------------------------------------------
            # CPU
            # ------------------------------------------------

            if cpu >= CPU_CRITICAL_THRESHOLD:

                findings.append({
                    "type": "CPU_HIGH",
                    "level": "CRITICAL",
                    "title": "Critical CPU Usage",
                    "message": (
                        f"CPU usage is "
                        f"{cpu:.1f}%."
                    ),
                    "source": "system-monitor",
                    "fingerprint_key": "CPU_HIGH",
                    "recommendation": (
                        "Inspect the top CPU-consuming "
                        "processes and check for runaway "
                        "applications."
                    ),
                    "evidence": {
                        "cpu_percent": round(
                            cpu,
                            2
                        ),
                    },
                })

            elif cpu >= CPU_WARNING_THRESHOLD:

                findings.append({
                    "type": "CPU_HIGH",
                    "level": "WARNING",
                    "title": "High CPU Usage",
                    "message": (
                        f"CPU usage is "
                        f"{cpu:.1f}%."
                    ),
                    "source": "system-monitor",
                    "fingerprint_key": "CPU_HIGH",
                    "recommendation": (
                        "Inspect CPU-intensive processes "
                        "and application activity."
                    ),
                    "evidence": {
                        "cpu_percent": round(
                            cpu,
                            2
                        ),
                    },
                })

            # ------------------------------------------------
            # MEMORY
            # ------------------------------------------------

            if memory >= MEMORY_CRITICAL_THRESHOLD:

                findings.append({
                    "type": "MEMORY_HIGH",
                    "level": "CRITICAL",
                    "title": "Critical Memory Usage",
                    "message": (
                        f"Memory usage is "
                        f"{memory:.1f}%."
                    ),
                    "source": "system-monitor",
                    "fingerprint_key": "MEMORY_HIGH",
                    "recommendation": (
                        "Inspect memory-consuming "
                        "processes and possible memory leaks."
                    ),
                    "evidence": {
                        "memory_percent": round(
                            memory,
                            2
                        ),
                    },
                })

            elif memory >= MEMORY_WARNING_THRESHOLD:

                findings.append({
                    "type": "MEMORY_HIGH",
                    "level": "WARNING",
                    "title": "High Memory Usage",
                    "message": (
                        f"Memory usage is "
                        f"{memory:.1f}%."
                    ),
                    "source": "system-monitor",
                    "fingerprint_key": "MEMORY_HIGH",
                    "recommendation": (
                        "Inspect memory-heavy processes "
                        "before the system becomes critical."
                    ),
                    "evidence": {
                        "memory_percent": round(
                            memory,
                            2
                        ),
                    },
                })

            # ------------------------------------------------
            # DISK
            # ------------------------------------------------

            if disk >= DISK_CRITICAL_THRESHOLD:

                findings.append({
                    "type": "DISK_HIGH",
                    "level": "CRITICAL",
                    "title": "Critical Disk Usage",
                    "message": (
                        f"Disk usage is "
                        f"{disk:.1f}%."
                    ),
                    "source": "system-monitor",
                    "fingerprint_key": "DISK_HIGH",
                    "recommendation": (
                        "Identify large files and logs "
                        "before disk space is exhausted."
                    ),
                    "evidence": {
                        "disk_percent": round(
                            disk,
                            2
                        ),
                    },
                })

            elif disk >= DISK_WARNING_THRESHOLD:

                findings.append({
                    "type": "DISK_HIGH",
                    "level": "WARNING",
                    "title": "High Disk Usage",
                    "message": (
                        f"Disk usage is "
                        f"{disk:.1f}%."
                    ),
                    "source": "system-monitor",
                    "fingerprint_key": "DISK_HIGH",
                    "recommendation": (
                        "Review disk usage and consider "
                        "cleaning unnecessary files or logs."
                    ),
                    "evidence": {
                        "disk_percent": round(
                            disk,
                            2
                        ),
                    },
                })

        except Exception as exc:

            self.app.logger.exception(
                "System detection failed: %s",
                exc,
            )

        return findings

    # ========================================================
    # DOCKER
    # ========================================================

    def _check_docker(self):

        findings = []

        if docker is None:

            return findings

        client = None

        try:

            client = docker.from_env()

            containers = client.containers.list(
                all=True
            )

            for container in containers:

                status = (
                    container.status or ""
                ).lower()

                if (
                    status
                    not in UNHEALTHY_DOCKER_STATUSES
                ):

                    continue

                name = (
                    container.name
                    or container.short_id
                )

                findings.append({
                    "type": "DOCKER_STOPPED",
                    "level": "HIGH",
                    "title": "Docker Container Stopped",
                    "message": (
                        f"Docker container "
                        f"'{name}' is "
                        f"{status}."
                    ),
                    "source": "docker-monitor",
                    "fingerprint_key": (
                        f"DOCKER_STOPPED:{name}"
                    ),
                    "recommendation": (
                        f"Inspect the logs for "
                        f"'{name}', determine why "
                        f"it stopped, and restart it "
                        f"if safe."
                    ),
                    "evidence": {
                        "container_id":
                            container.id,
                        "container_name":
                            name,
                        "status":
                            status,
                    },
                })

        except Exception as exc:

            self.app.logger.warning(
                "Docker detection unavailable: %s",
                exc,
            )

        finally:

            if client:

                try:
                    client.close()
                except Exception:
                    pass

        return findings

    # ========================================================
    # WEBSITE
    # ========================================================

    def _check_website(self):

        findings = []

        if not self.monitored_url:

            return findings

        start_time = time.perf_counter()

        request = Request(
            self.monitored_url,
            headers={
                "User-Agent":
                    "AI-Incident-Commander-Monitor/1.0"
            },
        )

        try:

            with urlopen(
                request,
                timeout=WEBSITE_TIMEOUT_SECONDS,
            ) as response:

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                status = response.status

                if status >= 500:

                    findings.append({
                        "type": "WEBSITE_5XX",
                        "level": "CRITICAL",
                        "title": "Website Server Error",
                        "message": (
                            f"{self.monitored_url} "
                            f"returned HTTP {status}."
                        ),
                        "source": "website-monitor",
                        "fingerprint_key": (
                            "WEBSITE_5XX"
                        ),
                        "recommendation": (
                            "Inspect application logs, "
                            "backend health, and recent "
                            "deployment changes."
                        ),
                        "evidence": {
                            "url":
                                self.monitored_url,
                            "http_status":
                                status,
                            "response_time_seconds":
                                round(
                                    elapsed,
                                    3
                                ),
                        },
                    })

                elif (
                    elapsed
                    >= WEBSITE_SLOW_RESPONSE_SECONDS
                ):

                    findings.append({
                        "type": "WEBSITE_SLOW",
                        "level": "WARNING",
                        "title": "Slow Website Response",
                        "message": (
                            f"{self.monitored_url} "
                            f"responded in "
                            f"{elapsed:.2f} seconds."
                        ),
                        "source": "website-monitor",
                        "fingerprint_key": (
                            "WEBSITE_SLOW"
                        ),
                        "recommendation": (
                            "Inspect backend response "
                            "time, database queries, "
                            "CPU usage, and network "
                            "latency."
                        ),
                        "evidence": {
                            "url":
                                self.monitored_url,
                            "http_status":
                                status,
                            "response_time_seconds":
                                round(
                                    elapsed,
                                    3
                                ),
                        },
                    })

        except HTTPError as exc:

            level = (
                "CRITICAL"
                if exc.code >= 500
                else "WARNING"
            )

            findings.append({
                "type": "WEBSITE_HTTP_ERROR",
                "level": level,
                "title": "Website HTTP Error",
                "message": (
                    f"{self.monitored_url} "
                    f"returned HTTP {exc.code}."
                ),
                "source": "website-monitor",
                "fingerprint_key": (
                    f"WEBSITE_HTTP_ERROR:{exc.code}"
                ),
                "recommendation": (
                    "Inspect the website response, "
                    "backend logs, and application health."
                ),
                "evidence": {
                    "url":
                        self.monitored_url,
                    "http_status":
                        exc.code,
                },
            })

        except (
            URLError,
            TimeoutError,
            OSError,
        ):

            findings.append({
                "type": "WEBSITE_UNAVAILABLE",
                "level": "CRITICAL",
                "title": "Website Unavailable",
                "message": (
                    f"Unable to reach "
                    f"{self.monitored_url}."
                ),
                "source": "website-monitor",
                "fingerprint_key": (
                    "WEBSITE_UNAVAILABLE"
                ),
                "recommendation": (
                    "Check whether the frontend/server "
                    "is running and inspect backend "
                    "connectivity."
                ),
                "evidence": {
                    "url":
                        self.monitored_url,
                },
            })

        except Exception as exc:

            self.app.logger.warning(
                "Website detection failed: %s",
                exc,
            )

        return findings

    # ========================================================
    # APPLICATION LOGS
    # ========================================================

    def _check_application_logs(self):

        findings = []

        if not self.log_file.exists():

            return findings

        try:

            with self.log_file.open(
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:

                lines = file.readlines()

            recent_lines = lines[
                -MAX_LOG_LINES:
            ]

            for line in reversed(
                recent_lines
            ):

                line = line.strip()

                if not line:

                    continue

                upper_line = (
                    f" {line.upper()} "
                )

                lower_line = line.lower()

                # --------------------------------------------
                # DATABASE ERROR
                # --------------------------------------------

                if any(
                    keyword in lower_line
                    for keyword
                    in DATABASE_ERROR_KEYWORDS
                ):

                    fingerprint_key = (
                        f"DATABASE_ERROR:{line}"
                    )

                    if self.state.has_processed_log(
                        fingerprint_key
                    ):

                        continue

                    findings.append({
                        "type": "DATABASE_ERROR",
                        "level": "CRITICAL",
                        "title":
                            "Database Connection Failure",
                        "message": line,
                        "source":
                            "application.log",
                        "fingerprint_key":
                            fingerprint_key,
                        "recommendation": (
                            "Check MySQL/database "
                            "availability, credentials, "
                            "network connectivity, and "
                            "connection pool health."
                        ),
                        "evidence": {
                            "log_line": line,
                        },
                    })

                    break

                # --------------------------------------------
                # GENERAL ERROR
                # --------------------------------------------

                # Ignore non-error log levels (WARNING, INFO, DEBUG)
                if " WARNING " in upper_line or " INFO " in upper_line or " DEBUG " in upper_line:
                    continue

                if any(
                    keyword in upper_line
                    for keyword in ERROR_KEYWORDS
                ):

                    fingerprint_key = (
                        f"APPLICATION_ERROR:{line}"
                    )

                    if self.state.has_processed_log(
                        fingerprint_key
                    ):

                        continue

                    findings.append({
                        "type":
                            "APPLICATION_ERROR",
                        "level":
                            "CRITICAL",
                        "title":
                            "Application Error Detected",
                        "message":
                            line,
                        "source":
                            "application.log",
                        "fingerprint_key":
                            fingerprint_key,
                        "recommendation": (
                            "Inspect the surrounding "
                            "application logs and "
                            "identify the failing service "
                            "or operation."
                        ),
                        "evidence": {
                            "log_line": line,
                        },
                    })

                    break

        except Exception as exc:

            self.app.logger.warning(
                "Log detection failed: %s",
                exc,
            )

        return findings

    # ========================================================
    # PROCESS FINDING
    # ========================================================

    def _process_finding(self, finding):
        fingerprint = self.fingerprint(finding)
        
        if finding["type"] in {"APPLICATION_ERROR", "DATABASE_ERROR"}:
            log_key = finding["fingerprint_key"]
            if self.state.has_processed_log(log_key):
                return None
            self.state.mark_log_processed(log_key)
            
        if self.state.is_active(fingerprint):
            self.state.update(fingerprint, finding)
            return None
            
        # Try to find an OPEN incident to correlate with
        from datetime import datetime, timedelta
        recent_time = datetime.utcnow() - timedelta(minutes=15)
        existing_incident = Incident.query.filter(
            Incident.status.in_(["OPEN", "ACTION_REQUIRED", "INVESTIGATING", "VERIFYING", "REMEDIATING", "FAILED"]),
            Incident.last_seen >= recent_time
        ).order_by(Incident.id.desc()).first()
        
        if existing_incident:
            # Correlate as event
            event = IncidentEvent(
                incident_id=existing_incident.id,
                message=finding["message"],
                source=finding["source"],
                level=finding["level"]
            )
            db.session.add(event)
            
            # Save evidence
            import json
            evidence = IncidentEvidence(
                incident_id=existing_incident.id,
                evidence_type=finding["type"],
                data=json.dumps(finding.get("evidence", {}))
            )
            db.session.add(evidence)
            
            existing_incident.last_seen = datetime.utcnow()
            
            # Update title and message to indicate correlation if it's not already
            if "Correlated" not in str(existing_incident.title):
                existing_incident.title = "Correlated System Degradation"
                existing_incident.type = "CORRELATED_INCIDENT"
            
            if finding["message"] not in str(existing_incident.message):
                existing_incident.message = f"{existing_incident.message} | {finding['message']}"
                
            db.session.commit()
            
            self.state.activate(fingerprint, finding)
            
            # Trigger AI again if new evidence arrives? Let's not spam Gemini.
            # But we could trigger it if it hasn't been triggered yet.
            
            from app.services.socket_service import emit_incident_update
            emit_incident_update(existing_incident.id)
            return existing_incident
            
        incident = self._create_incident(finding, fingerprint)
        if incident:
            self.state.activate(fingerprint, finding)
            
            # Trigger AI
            from app.services.incident_manager import IncidentManager
            IncidentManager.analyze_incident(incident.id)
            
            return incident
            
        return None

    # ========================================================
    # INCIDENT MATCHING
    # ========================================================

    def _incident_matches(
        self,
        incident,
        finding,
    ):

        source_match = (
            incident.source
            == finding["source"]
        )

        if not source_match:

            return False

        message = (
            incident.message
            or ""
        )

        finding_type = (
            finding["type"]
        )

        if finding_type == "CPU_HIGH":

            return (
                "CPU usage is"
                in message
            )

        if finding_type == "MEMORY_HIGH":

            return (
                "Memory usage is"
                in message
            )

        if finding_type == "DISK_HIGH":

            return (
                "Disk usage is"
                in message
            )

        if finding_type == "WEBSITE_UNAVAILABLE":

            return (
                "Unable to reach"
                in message
            )

        if finding_type == "WEBSITE_SLOW":

            return (
                "responded in"
                in message
            )

        if finding_type == "DOCKER_STOPPED":

            return (
                finding.get(
                    "container_name",
                    ""
                )
                in message
            )

        if finding_type in {
            "APPLICATION_ERROR",
            "DATABASE_ERROR",
        }:

            return (
                incident.message
                == finding["message"]
            )

        return False

    # ========================================================
    # CREATE INCIDENT
    # ========================================================

    def _create_incident(self, finding, fingerprint):
        try:
            incident = Incident(
                level=finding["level"],
                severity=finding.get("level", "WARNING"),
                type=finding["type"],
                title=finding["title"],
                message=finding["message"],
                source=finding["source"],
                fingerprint=fingerprint,
                status="OPEN",
            )
            db.session.add(incident)
            db.session.flush()
            
            event = IncidentEvent(
                incident_id=incident.id,
                message=finding["message"],
                source=finding["source"],
                level=finding["level"]
            )
            db.session.add(event)
            
            import json
            evidence = IncidentEvidence(
                incident_id=incident.id,
                evidence_type=finding["type"],
                data=json.dumps(finding.get("evidence", {}))
            )
            db.session.add(evidence)

            notification = Notification(
                incident_id=incident.id,
                title=finding["title"],
                message=finding["message"],
                severity=finding["level"],
                source=finding["source"],
                is_read=False,
            )
            db.session.add(notification)
            db.session.commit()
            
            from app.services.socket_service import emit_incident_update
            emit_incident_update(incident.id)

            self.app.logger.warning("Automatic incident created: %s", finding["message"])
            return incident
        except Exception as exc:
            db.session.rollback()
            self.app.logger.exception("Failed to create automatic incident: %s", exc)
            return None

    # ========================================================
    # BACKGROUND LOOP
    # ========================================================

    def start(self):

        if self.running:

            return

        self.running = True

        self.thread = threading.Thread(
            target=self._run_loop,
            name="incident-detection-engine",
            daemon=True,
        )

        self.thread.start()

        self.app.logger.info(
            "Automatic detection engine started "
            "(interval=%ss, url=%s)",
            self.scan_interval,
            self.monitored_url,
        )

    def stop(self):

        self.running = False

    def _run_loop(self):

        time.sleep(3)

        while self.running:

            try:

                with self.app.app_context():

                    self.scan()

            except Exception as exc:

                self.app.logger.exception(
                    "Detection engine scan failed: %s",
                    exc,
                )

            time.sleep(
                self.scan_interval
            )


def get_detection_service(app):

    service = app.extensions.get(
        "detection_service"
    )

    if service is None:

        service = DetectionService(
            app
        )

        app.extensions[
            "detection_service"
        ] = service

    return service


def start_detection_service(app):

    service = get_detection_service(
        app
    )

    service.start()

    return service