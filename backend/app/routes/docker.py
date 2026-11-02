from flask import Blueprint, jsonify

from app.services.docker_service import DockerService
from app.services.docker_logs import DockerLogService
from app.services.docker_control import DockerControlService

docker_bp = Blueprint(
    "docker",
    __name__,
    url_prefix="/api/docker"
)


@docker_bp.route("/containers", methods=["GET"])
def containers():

    service = DockerService()

    return jsonify(
        service.get_containers()
    )


@docker_bp.route("/logs/<container_id>", methods=["GET"])
def container_logs(container_id):

    service = DockerLogService()

    return jsonify(
        service.get_logs(container_id)
    )
@docker_bp.route("/start/<container_id>", methods=["POST"])
def start_container(container_id):

    service = DockerControlService()

    return jsonify(
        service.start_container(container_id)
    )


@docker_bp.route("/stop/<container_id>", methods=["POST"])
def stop_container(container_id):

    service = DockerControlService()

    return jsonify(
        service.stop_container(container_id)
    )


@docker_bp.route("/restart/<container_id>", methods=["POST"])
def restart_container(container_id):

    service = DockerControlService()

    return jsonify(
        service.restart_container(container_id)
    )