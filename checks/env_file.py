"""Check for missing .env when .env.example exists."""

from __future__ import annotations

from pathlib import Path

from checks.base import CheckResult, Status, copy_env_command


def check_env_file(project: Path) -> CheckResult:
    name = "Environment File"
    env_example = project / ".env.example"
    env_file = project / ".env"

    if not env_example.is_file():
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="No .env.example found — environment template not required.",
        )

    if env_file.is_file():
        return CheckResult(
            name=name,
            status=Status.PASS,
            message=".env file is present.",
        )

    return CheckResult(
        name=name,
        status=Status.WARN,
        message=".env is missing but .env.example exists.",
        fix_command=copy_env_command(project),
    )
