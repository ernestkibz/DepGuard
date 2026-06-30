"""Check for missing .env when .env.example exists."""

from __future__ import annotations

from checks.base import CheckResult, Status, copy_env_command
from checks.detection import ProjectContext


def check_env_file(context: ProjectContext) -> CheckResult | None:
    name = "Environment File"
    project = context.project
    env_example = project / ".env.example"
    env_file = project / ".env"

    if not env_example.is_file() and not env_file.is_file():
        return None

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
        fix_command=copy_env_command(context.project),
    )
