"""Check whether a Python virtual environment is active."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from checks.base import CheckResult, Status, venv_create_and_activate_fix


def _looks_like_python_project(project: Path) -> bool:
    markers = (
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "poetry.lock",
    )
    return any((project / marker).is_file() for marker in markers)


def check_venv_active(project: Path) -> CheckResult:
    name = "Virtual Environment"

    if not _looks_like_python_project(project):
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="Not a Python project — virtual environment not required.",
        )

    in_venv = (
        os.environ.get("VIRTUAL_ENV") is not None
        or sys.prefix != sys.base_prefix
        or hasattr(sys, "real_prefix")
    )

    if in_venv:
        active = os.environ.get("VIRTUAL_ENV", sys.prefix)
        return CheckResult(
            name=name,
            status=Status.PASS,
            message=f"Virtual environment is active ({active}).",
        )

    return CheckResult(
        name=name,
        status=Status.WARN,
        message="Python project detected but no virtual environment is active.",
        fix_command=venv_create_and_activate_fix(),
    )
