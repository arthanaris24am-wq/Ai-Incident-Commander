"""
Runtime state for the detection engine.
"""

from datetime import datetime


class DetectionState:

    def __init__(self):

        self.processed_log_events = set()

        self.active_findings = {}

        self.last_values = {}

        self.started_at = datetime.utcnow()

    # ========================================================
    # LOG EVENTS
    # ========================================================

    def has_processed_log(self, fingerprint):

        return fingerprint in self.processed_log_events

    def mark_log_processed(self, fingerprint):

        self.processed_log_events.add(
            fingerprint
        )

    # ========================================================
    # ACTIVE FINDINGS
    # ========================================================

    def is_active(self, fingerprint):

        return (
            fingerprint
            in self.active_findings
        )

    def activate(
        self,
        fingerprint,
        finding,
    ):

        self.active_findings[
            fingerprint
        ] = {
            "finding": finding,
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
        }

    def update(
        self,
        fingerprint,
        finding,
    ):

        if fingerprint in self.active_findings:

            self.active_findings[
                fingerprint
            ]["finding"] = finding

            self.active_findings[
                fingerprint
            ]["last_seen"] = datetime.utcnow()

    def deactivate(self, fingerprint):

        self.active_findings.pop(
            fingerprint,
            None,
        )

    # ========================================================
    # METRICS
    # ========================================================

    def set_value(
        self,
        key,
        value,
    ):

        self.last_values[key] = value

    def get_value(self, key):

        return self.last_values.get(key)

    # ========================================================
    # RESET
    # ========================================================

    def clear(self):

        self.processed_log_events.clear()

        self.active_findings.clear()

        self.last_values.clear()