import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.extensions import db, socketio
from app.models.incident import Incident
from app.logging_config import get_log_file_path

LOG_FILE = str(get_log_file_path())


class LogHandler(FileSystemEventHandler):

    def __init__(self, app):
        self.app = app
        self.last_position = 0

        if os.path.exists(LOG_FILE):
            self.last_position = os.path.getsize(LOG_FILE)

    def _process_file(self):
        if not os.path.exists(LOG_FILE):
            return

        with self.app.app_context():
            current_size = os.path.getsize(LOG_FILE)
            if current_size < self.last_position:
                # File was truncated/cleared
                self.last_position = 0

            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue

                    level = "INFO"
                    line_upper = line.upper()
                    if "] CRITICAL" in line_upper or " CRITICAL in " in line_upper or "] CRITICAL: " in line_upper:
                        level = "CRITICAL"
                    elif "] ERROR" in line_upper or " ERROR in " in line_upper or "] ERROR: " in line_upper:
                        level = "ERROR"
                    elif "] WARNING" in line_upper or " WARNING in " in line_upper or "] WARNING: " in line_upper:
                        level = "WARNING"
                    elif "] INFO" in line_upper or " INFO in " in line_upper or "] INFO: " in line_upper:
                        level = "INFO"
                    elif "] DEBUG" in line_upper or " DEBUG in " in line_upper:
                        level = "DEBUG"

                    component = "application"
                    lower_line = line.lower()
                    if any(kw in lower_line for kw in ["mysql", "db", "database", "postgres", "sqlite"]):
                        component = "database"
                    elif any(kw in lower_line for kw in ["api", "http", "request", "werkzeug"]):
                        component = "api"
                    elif "docker" in lower_line:
                        component = "docker"

                    from app.models.log_event import LogEvent
                    
                    log_event = LogEvent(
                        level=level,
                        source="application.log",
                        component=component,
                        message=line
                    )
                    
                    # Only trigger incident creation for external crash/error lines, not internal incident logs
                    if "[INCIDENT #" not in line and level in ["ERROR", "CRITICAL"]:
                        from datetime import datetime, timedelta
                        
                        recent_time = datetime.utcnow() - timedelta(minutes=15)
                        recent_incident = Incident.query.filter(
                            Incident.status.in_(["OPEN", "ACTION_REQUIRED", "INVESTIGATING", "VERIFYING", "REMEDIATING", "FAILED"]),
                            Incident.last_seen >= recent_time
                        ).order_by(Incident.id.desc()).first()
                        
                        if recent_incident:
                            log_event.incident_id = recent_incident.id
                            recent_incident.last_seen = datetime.utcnow()
                            recent_incident.title = "Correlated System Degradation"
                            from app.models.incident_event import IncidentEvent
                            event = IncidentEvent(
                                incident_id=recent_incident.id,
                                message=f"Correlated Log: {line}",
                                source="application.log",
                                level=level
                            )
                            db.session.add(event)
                        else:
                            new_incident = Incident(
                                level=level,
                                severity=level,
                                type="APPLICATION_ERROR",
                                title=f"Application Error in {component}",
                                message=line,
                                source="application.log",
                                status="OPEN"
                            )
                            db.session.add(new_incident)
                            db.session.flush()
                            log_event.incident_id = new_incident.id
                            
                            from app.services.socket_service import emit_incident_update
                            emit_incident_update(new_incident.id)

                    db.session.add(log_event)
                    db.session.commit()

                    if level in ["ERROR", "CRITICAL"]:
                        if 'new_incident' in locals():
                            socketio.emit("new_incident", new_incident.to_dict())
                        print("PROCESSED ERROR LOG:", line)
                        print("PROCESSED ERROR LOG:", line)

    def on_modified(self, event):
        if os.path.normcase(os.path.abspath(event.src_path)) == os.path.normcase(LOG_FILE):
            self._process_file()

    def on_created(self, event):
        if os.path.normcase(os.path.abspath(event.src_path)) == os.path.normcase(LOG_FILE):
            self._process_file()


def watch_logs(app):
    print("Watching:", LOG_FILE)

    observer = Observer()
    observer.schedule(
        LogHandler(app),
        path=os.path.dirname(LOG_FILE),
        recursive=False
    )
    observer.daemon = True
    observer.start()