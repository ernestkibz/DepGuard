"""Check that Docker is installed when a Dockerfile is present."""

from __future__ import annotations

from checks.base import (
    CheckResult,
    Status,
    command_exists,
    docker_daemon_fix,
    docker_install_fix,
    run_command,
)
from checks.detection import ProjectContext


def check_docker(context: ProjectContext) -> CheckResult | None:
    name = "Docker Available"
    if not context.has_infrastructure("Docker"):
        return None

    project = context.project
    dockerfile = project / "Dockerfile"

    if not dockerfile.is_file():
        alt = project / "dockerfile"
        if not alt.is_file():
            return CheckResult(
                name=name,
                status=Status.PASS,
                message="Docker support is detected, but no Dockerfile was found.",
            )

    if not command_exists("docker"):
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="Dockerfile exists but Docker is not installed or not on PATH.",
            fix_command=docker_install_fix(),
            suggestion=(
                "Install Docker before running image builds, compose commands, or container-based "
                "development tasks for this project."
            ),
        )

    try:
        result = run_command(["docker", "info"], cwd=project, timeout=30)
    except OSError as exc:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"Docker is on PATH but not responding: {exc}",
            fix_command=docker_daemon_fix(),
            suggestion=(
                "Start Docker Desktop or the Docker daemon for this machine, then rerun "
                "container commands from the project root."
            ),
        )

    if result.returncode != 0:
        return CheckResult(
            name=name,
            status=Status.WARN,
            message="Docker is installed but the daemon is not running.",
            fix_command=docker_daemon_fix(),
            suggestion=(
                "Start the Docker daemon before running local builds, compose stacks, "
                "or integration workflows that rely on containers."
            ),
        )

    return CheckResult(
        name=name,
        status=Status.PASS,
        message="Docker is installed and the daemon is reachable.",
    )
