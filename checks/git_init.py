"""Check that the project folder is a Git repository."""

from __future__ import annotations

from pathlib import Path

from checks.base import CheckResult, Status


def check_git_init(project: Path) -> CheckResult:
    name = "Git Initialized"

    if (project / ".git").exists():
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="Git repository is initialized.",
        )

    return CheckResult(
        name=name,
        status=Status.FAIL,
        message="Git is not initialized in this project folder.",
        fix_command="git init",
    )
