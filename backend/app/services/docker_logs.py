import docker


class DockerLogService:

    def __init__(self):
        self.client = docker.from_env()

    def get_logs(self, container_id, lines=100):

        container = self.client.containers.get(container_id)

        logs = container.logs(
            tail=lines
        ).decode(
            "utf-8",
            errors="ignore"
        )

        return {
            "container": container.name,
            "logs": logs
        }