import os
import json
from app.services.metric_service import MetricService
from app.services.docker_service import DockerService
from pathlib import Path

class CorrelationEngine:
    @staticmethod
    def gather_context(incident) -> dict:
        """
        Gathers system metrics, logs, and docker context for the incident RCA.
        """
        context = {
            "metrics": None,
            "docker_containers": None,
            "recent_logs": None
        }
        
        try:
            context["metrics"] = MetricService.get_metrics()
        except Exception as e:
            print(f"Error gathering metrics context: {e}")
            
        try:
            context["docker_containers"] = DockerService().get_containers()
        except Exception as e:
            print(f"Error gathering docker context: {e}")
            
        try:
            backend_dir = Path(__file__).parent.parent.parent
            log_file = backend_dir / "logs" / "application.log"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8", errors="ignore") as file:
                    lines = file.readlines()
                    context["recent_logs"] = [l.strip() for l in lines[-100:] if l.strip()]
        except Exception as e:
            print(f"Error gathering log context: {e}")
            
        return context
