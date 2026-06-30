"""Check that the project folder is a Git repository."""

from __future__ import annotations

from checks.base import CheckResult, Status
from checks.detection import ProjectContext


def check_git_init(context: ProjectContext) -> CheckResult:
    name = "Git Initialized"
    project = context.project

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
        suggestion=(
            "Initialize Git before the first commit, or clone the canonical repository again "
            "if this folder was expected to already be version-controlled."
        ),
    )
