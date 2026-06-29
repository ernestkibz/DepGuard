"""Check that Docker is installed when a Dockerfile is present."""

from __future__ import annotations

from pathlib import Path

from checks.base import (
    CheckResult,
    Status,
    command_exists,
    docker_daemon_fix,
    docker_install_fix,
    run_command,
)


def check_docker(project: Path) -> CheckResult:
    name = "Docker Available"
    dockerfile = project / "Dockerfile"

    if not dockerfile.is_file():
        alt = project / "dockerfile"
        if not alt.is_file():
            return CheckResult(
                name=name,
                status=Status.PASS,
                message="No Dockerfile found — Docker not required.",
            )

    if not command_exists("docker"):
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="Dockerfile exists but Docker is not installed or not on PATH.",
            fix_command=docker_install_fix(),
        )

    try:
        result = run_command(["docker", "info"], cwd=project, timeout=30)
    except OSError as exc:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"Docker is on PATH but not responding: {exc}",
            fix_command=docker_daemon_fix(),
        )

    if result.returncode != 0:
        return CheckResult(
            name=name,
            status=Status.WARN,
            message="Docker is installed but the daemon is not running.",
            fix_command=docker_daemon_fix(),
        )

    return CheckResult(
        name=name,
        status=Status.PASS,
        message="Docker is installed and the daemon is reachable.",
    )
