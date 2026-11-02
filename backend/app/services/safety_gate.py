import os
import json
from pathlib import Path

class SafetyGate:
    def __init__(self):
        self.allowlist = self._load_allowlist()

    def _load_allowlist(self):
        backend_dir = Path(__file__).parent.parent.parent
        config_path = backend_dir / "remediation_allowlist.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading allowlist: {e}")
        return {
            "ALLOWED_SERVICES": [],
            "ALLOWED_APPLICATIONS": [],
            "ALLOWED_CLEANUP_PATHS": [],
            "ALLOWED_PROCESSES": [],
            "ALLOWED_ACTIONS": []
        }

    def validate_action(self, action_type: str, target: str) -> bool:
        action_type = action_type.upper()
        
        # 1. Check if action is in allowed actions
        if action_type not in self.allowlist.get("ALLOWED_ACTIONS", []):
            return False

        if action_type == "NONE":
            return True

        if not target:
            # If target is required but missing, it's unsafe (except maybe for some actions like START_DOCKER_DESKTOP)
            if action_type not in ["START_DOCKER_DESKTOP", "WAIT_FOR_DOCKER_ENGINE", "REANALYZE_INCIDENT", "VERIFY_INCIDENT"]:
                return False
            return True

        target_lower = target.lower().strip()

        # 2. Check target based on action type
        if "SERVICE" in action_type and "DATABASE" not in action_type:
            allowed_services = [s.lower() for s in self.allowlist.get("ALLOWED_SERVICES", [])]
            if not any(s in target_lower or target_lower in s for s in allowed_services):
                return False
                
        if "DATABASE" in action_type:
            allowed_services = [s.lower() for s in self.allowlist.get("ALLOWED_SERVICES", [])]
            if not any(s in target_lower or target_lower in s for s in allowed_services):
                return False

        if "APPLICATION" in action_type:
            apps = self.allowlist.get("ALLOWED_APPLICATIONS", [])
            app_names = [a.get("name", "").lower() for a in apps]
            if not any(a in target_lower or target_lower in a for a in app_names):
                return False
                
        if "PROCESS" in action_type:
            allowed_procs = [p.lower().replace(".exe", "") for p in self.allowlist.get("ALLOWED_PROCESSES", [])]
            target_proc = target_lower.replace(".exe", "")
            if not any(p in target_proc or target_proc in p for p in allowed_procs):
                return False
                
        if "CLEAN" in action_type:
            allowed_paths = [p.lower().rstrip("\\/") for p in self.allowlist.get("ALLOWED_CLEANUP_PATHS", [])]
            generic_clean = ["temp", "tmp", "cache", "logs", "log", "c:\\temp"]
            if not (any(p in target_lower for p in allowed_paths) or any(g in target_lower for g in generic_clean)):
                return False

        return True
