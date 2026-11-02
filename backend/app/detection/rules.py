"""
Detection rules for AI Incident Commander.
"""


# ============================================================
# SYSTEM THRESHOLDS
# ============================================================

import os

CPU_WARNING_THRESHOLD = float(os.getenv("CPU_WARNING_THRESHOLD", "80.0"))
CPU_CRITICAL_THRESHOLD = float(os.getenv("CPU_CRITICAL_THRESHOLD", "90.0"))

MEMORY_WARNING_THRESHOLD = float(os.getenv("MEMORY_WARNING_THRESHOLD", "85.0"))
MEMORY_CRITICAL_THRESHOLD = float(os.getenv("MEMORY_CRITICAL_THRESHOLD", "92.0"))

DISK_WARNING_THRESHOLD = float(os.getenv("DISK_WARNING_THRESHOLD", "85.0"))
DISK_CRITICAL_THRESHOLD = float(os.getenv("DISK_CRITICAL_THRESHOLD", "92.0"))


# ============================================================
# WEBSITE
# ============================================================

WEBSITE_TIMEOUT_SECONDS = 5

WEBSITE_SLOW_RESPONSE_SECONDS = 3.0


# ============================================================
# DOCKER
# ============================================================

UNHEALTHY_DOCKER_STATUSES = {
    "exited",
    "dead",
    "created",
}


# ============================================================
# LOGS
# ============================================================

MAX_LOG_LINES = 100

ERROR_KEYWORDS = (
    " ERROR ",
    " CRITICAL ",
    " FATAL ",
)

DATABASE_ERROR_KEYWORDS = (
    "mysql connection lost",
    "mysql connection failed",
    "mysql connection refused",
    "mysql server has gone away",
    "database connection lost",
    "database connection failed",
    "database connection refused",
)

# Ignore log events older than this many hours.
LOG_EVENT_MAX_AGE_HOURS = 1


# ============================================================
# DETECTION
# ============================================================

DEFAULT_SCAN_INTERVAL_SECONDS = 15