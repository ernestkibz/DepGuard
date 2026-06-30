"""Check that requirements.txt packages are installable."""

from __future__ import annotations

import sys

from checks.base import CheckResult, Status, run_command
from checks.detection import ProjectContext


def check_requirements(context: ProjectContext) -> CheckResult | None:
    name = "Requirements Installable"
    if not context.has_language("python"):
        return None

    project = context.project
    req_file = project / "requirements.txt"

    if not req_file.is_file():
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="No requirements.txt found — nothing to validate.",
        )

    try:
        dry_run = run_command(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(req_file.name),
                "--dry-run",
            ],
            cwd=project,
            timeout=180,
        )
    except OSError as exc:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"Could not run pip: {exc}",
            fix_command=f"{sys.executable} -m pip install -r requirements.txt",
        )

    if dry_run.returncode == 0:
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="All packages in requirements.txt are installable.",
        )

    stderr = (dry_run.stderr or "").strip()
    if "no such option: --dry-run" in stderr.lower():
        return CheckResult(
            name=name,
            status=Status.WARN,
            message="pip is too old for dry-run validation; upgrade pip to verify packages.",
            fix_command=f"{sys.executable} -m pip install --upgrade pip",
        )

    detail = stderr.splitlines()[-1] if stderr else "pip install failed."
    return CheckResult(
        name=name,
        status=Status.FAIL,
        message=f"requirements.txt has install issues: {detail}",
        fix_command=f"{sys.executable} -m pip install -r requirements.txt",
    )
