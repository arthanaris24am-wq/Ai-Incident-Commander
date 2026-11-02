from .base_provider import BaseProvider

class ProcessProvider(BaseProvider):
    @property
    def supported_actions(self) -> list:
        return [
            "START_APPLICATION",
            "RESTART_APPLICATION",
            "RESTART_APPROVED_PROCESS"
        ]

    def execute(self, action_type: str, target: str, **kwargs) -> dict:
        action_type = action_type.upper()
        
        try:
            if action_type in ["START_APPLICATION", "RESTART_APPLICATION", "RESTART_APPROVED_PROCESS"]:
                # Simulated for safety.
                return {"success": True, "message": f"Process/Application {target} {action_type.split('_')[0].lower()}ed successfully."}
            else:
                return {"success": False, "message": f"Unsupported action {action_type} for ProcessProvider."}
        except Exception as e:
            return {"success": False, "message": str(e)}
