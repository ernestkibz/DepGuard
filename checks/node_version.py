"""Check that the active Node.js version matches project constraints."""

from __future__ import annotations

import json
import subprocess

from checks.base import (
    CheckResult,
    Status,
    command_exists,
    extract_minimum_version,
    first_line,
    node_version_fix,
    parse_version_numbers,
    read_text,
    run_command,
    satisfies_minimum,
    version_to_string,
)
from checks.detection import ProjectContext


def _required_from_nvmrc(context: ProjectContext) -> tuple[int, int, int] | None:
    project = context.project
    nvmrc = project / ".nvmrc"
    if not nvmrc.is_file():
        return None

    try:
        content = first_line(read_text(nvmrc))
    except (RuntimeError, IndexError):
        return None

    if not content:
        return None
    if content.startswith("v"):
        content = content[1:]
    return parse_version_numbers(content)


def _required_from_package_json(context: ProjectContext) -> tuple[int, int, int] | None:
    project = context.project
    package_json = project / "package.json"
    if not package_json.is_file():
        return None

    try:
        data = json.loads(read_text(package_json))
    except (RuntimeError, json.JSONDecodeError):
        return None

    engines = data.get("engines") or {}
    node_spec = engines.get("node")
    if not node_spec:
        return None
    return extract_minimum_version(str(node_spec))


def check_node_version(context: ProjectContext) -> CheckResult | None:
    name = "Node Version"
    if not context.has_web_scripting():
        return None

    required = _required_from_nvmrc(context) or _required_from_package_json(context)

    if required is None:
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="No Node.js version constraint found (.nvmrc or package.json engines).",
        )

    required_text = version_to_string(required)

    if not command_exists("node"):
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"Node.js is not installed, but {required_text} is required.",
            fix_command=node_version_fix(required_text),
            suggestion=(
                f"Install Node.js {required_text} or newer, reopen your terminal, "
                "and rerun dependency installation from the project root."
            ),
        )

    try:
        result = run_command(["node", "--version"], cwd=context.project, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"Could not read Node.js version: {exc}",
            fix_command=node_version_fix(required_text),
            suggestion=(
                "Check that `node --version` runs successfully in this shell and that the "
                "expected Node.js installation is first on PATH."
            ),
        )

    if result.returncode != 0:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="Node.js is installed but `node --version` failed.",
            fix_command=node_version_fix(required_text),
            suggestion=(
                "Fix the local Node.js installation or PATH issue, then rerun DepGuard and "
                "your package manager from the same shell."
            ),
        )

    current = parse_version_numbers(result.stdout.strip())
    current_text = version_to_string(current)

    if satisfies_minimum(current, required):
        return CheckResult(
            name=name,
            status=Status.PASS,
            message=f"Node.js {current_text} satisfies required {required_text}.",
        )

    return CheckResult(
        name=name,
        status=Status.FAIL,
        message=f"Node.js {current_text} does not satisfy required {required_text}.",
        fix_command=node_version_fix(required_text),
        suggestion=(
            f"Switch this project to Node.js {required_text} or newer, then rerun "
            "`npm install`, `pnpm install`, or `yarn install` in the updated shell."
        ),
    )
