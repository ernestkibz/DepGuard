"""Check that the active Python version matches project constraints."""

from __future__ import annotations

import re
import sys

from checks.base import (
    CheckResult,
    Status,
    extract_minimum_version,
    first_line,
    parse_version_numbers,
    python_version_fix,
    read_text,
    satisfies_minimum,
    version_to_string,
)
from checks.detection import ProjectContext


def _required_from_pyproject(context: ProjectContext) -> tuple[int, int, int] | None:
    project = context.project
    pyproject = project / "pyproject.toml"
    if not pyproject.is_file():
        return None

    try:
        content = read_text(pyproject)
    except RuntimeError:
        return None

    match = re.search(
        r'requires-python\s*=\s*["\']([^"\']+)["\']',
        content,
        re.IGNORECASE,
    )
    if match:
        return extract_minimum_version(match.group(1))
    return None


def _required_from_python_version(context: ProjectContext) -> tuple[int, int, int] | None:
    project = context.project
    dot_file = project / ".python-version"
    if not dot_file.is_file():
        return None

    try:
        content = first_line(read_text(dot_file))
    except (RuntimeError, IndexError):
        return None

    if not content:
        return None
    return parse_version_numbers(content)


def check_python_version(context: ProjectContext) -> CheckResult | None:
    name = "Python Version"
    if not context.has_language("python"):
        return None

    required = _required_from_python_version(context) or _required_from_pyproject(context)

    if required is None:
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="No Python version constraint found (.python-version or pyproject.toml).",
        )

    current = parse_version_numbers(
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    required_text = version_to_string(required)
    current_text = version_to_string(current)

    if satisfies_minimum(current, required):
        return CheckResult(
            name=name,
            status=Status.PASS,
            message=f"Python {current_text} satisfies required {required_text}.",
        )

    fix = python_version_fix(context.project, required_text)
    return CheckResult(
        name=name,
        status=Status.FAIL,
        message=f"Python {current_text} does not satisfy required {required_text}.",
        fix_command=fix,
    )
