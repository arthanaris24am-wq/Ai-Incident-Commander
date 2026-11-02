import psutil
import socket
import platform
import time
from datetime import datetime


class MetricService:

    @staticmethod
    def get_metrics():

        memory = psutil.virtual_memory()

        disk = psutil.disk_usage("/")

        network = psutil.net_io_counters()

        cpu = psutil.cpu_percent(interval=1)

        boot = datetime.fromtimestamp(psutil.boot_time())

        # Initialize CPU counters
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc.cpu_percent(None)
            except Exception:
                pass

        time.sleep(0.2)

        processes = []

        # Collect process CPU usage
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info["name"] or "Unknown"

                # Skip idle process
                if name == "System Idle Process":
                    continue

                processes.append({
                    "pid": proc.info["pid"],
                    "name": name,
                    "cpu_percent": proc.cpu_percent(None)
                })

            except Exception:
                pass

        # Sort by CPU usage
        processes.sort(
            key=lambda x: x["cpu_percent"],
            reverse=True
        )

        # Top 10 processes
        processes = processes[:10]

        base_metrics = {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "cpu": cpu,
            "memory_percent": memory.percent,
            "memory_used": round(memory.used / 1024 / 1024, 2),
            "memory_total": round(memory.total / 1024 / 1024, 2),
            "disk_percent": disk.percent,
            "disk_used": round(disk.used / 1024 / 1024 / 1024, 2),
            "disk_total": round(disk.total / 1024 / 1024 / 1024, 2),
            "bytes_sent": network.bytes_sent,
            "bytes_received": network.bytes_recv,
            "boot_time": boot.strftime("%Y-%m-%d %H:%M:%S"),
            "top_processes": processes
        }
        
        import os
        if os.path.exists("mock_cpu_high.txt"):
            base_metrics["cpu"] = 99.0
        if os.path.exists("mock_memory_high.txt"):
            base_metrics["memory_percent"] = 95.0
        if os.path.exists("mock_disk_high.txt"):
            base_metrics["disk_percent"] = 95.0
            
        return base_metrics