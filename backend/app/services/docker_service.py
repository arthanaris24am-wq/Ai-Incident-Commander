import docker


class DockerService:

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None

    def get_containers(self):
        if not self.client:
            try:
                self.client = docker.from_env()
            except Exception:
                return []

        try:
            containers = self.client.containers.list(all=True)
        except Exception:
            return []

        result = []

        for container in containers:

            try:
                stats = container.stats(stream=False)
            except Exception:
                stats = {}

            # ---------------- CPU ----------------

            cpu_raw = (
                stats.get("cpu_stats", {})
                .get("cpu_usage", {})
                .get("total_usage", 0)
            )

            # ---------------- Memory ----------------

            memory = stats.get("memory_stats") or {}

            memory_used = memory.get("usage", 0)
            memory_limit = memory.get("limit", 1)

            memory_percent = (
                (memory_used / memory_limit) * 100
                if memory_limit
                else 0
            )

            # ---------------- Network ----------------

            network_rx = 0
            network_tx = 0

            networks = stats.get("networks") or {}

            for network in networks.values():
                network_rx += network.get("rx_bytes", 0)
                network_tx += network.get("tx_bytes", 0)

            # ---------------- Block IO ----------------

            block_read = 0
            block_write = 0

            blkio_stats = stats.get("blkio_stats") or {}
            blkio = blkio_stats.get("io_service_bytes_recursive") or []

            # Handle case where blkio might be None somehow despite the 'or []'
            if blkio and isinstance(blkio, list):
                for item in blkio:
                    if not isinstance(item, dict):
                        continue
                    op = item.get("op", "").lower()

                    if op == "read":
                        block_read += item.get("value", 0)

                    elif op == "write":
                        block_write += item.get("value", 0)

            # ---------------- PIDs ----------------

            pids = (
                stats.get("pids_stats", {})
                .get("current", 0)
            )

            result.append({

                "id": container.short_id,
                "full_id": container.id,
                "name": container.name.lstrip("/"),
                "image": container.image.tags if hasattr(container.image, "tags") else [],
                "status": container.status,
                "state": container.status,

                "cpu_raw": cpu_raw,

                "memory_used_mb": round(memory_used / 1024 / 1024, 2),
                "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
                "memory_percent": round(memory_percent, 2),

                "network_rx_mb": round(network_rx / 1024 / 1024, 2),
                "network_tx_mb": round(network_tx / 1024 / 1024, 2),

                "block_read_mb": round(block_read / 1024 / 1024, 2),
                "block_write_mb": round(block_write / 1024 / 1024, 2),

                "pids": pids

            })

        return result