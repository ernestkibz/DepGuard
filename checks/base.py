"""Shared types and helpers for setup checks."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence


EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "bin",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}


class Status(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: Status
    message: str
    fix_command: str | None = None
    suggestion: str | None = None


def read_text(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"Could not read {path.name}: {exc}") from exc

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def first_line(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip().splitlines()[0].strip()


def is_windows() -> bool:
    return platform.system() == "Windows"


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def normalize_dependency_name(name: str) -> str:
    cleaned = name.strip().strip('"').strip("'")
    cleaned = cleaned.split(";", maxsplit=1)[0]
    cleaned = cleaned.split("[", maxsplit=1)[0]
    cleaned = re.split(r"\s*(?:==|>=|<=|~=|!=|>|<|\^|~|@|\(|\{)", cleaned, maxsplit=1)[0]
    return cleaned.strip().lower()


def iter_project_files(
    project: Path,
    *,
    suffixes: Iterable[str] | None = None,
) -> Iterable[Path]:
    allowed = {suffix.lower() for suffix in suffixes} if suffixes else None
    for path in project.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        try:
            relative_parent = path.relative_to(project).parent
        except ValueError:
            continue
        if relative_parent != Path("."):
            nested_root = project
            skip_nested_repo = False
            for part in relative_parent.parts:
                nested_root = nested_root / part
                if nested_root != project and (nested_root / ".git").is_dir():
                    skip_nested_repo = True
                    break
            if skip_nested_repo:
                continue
        if allowed and path.suffix.lower() not in allowed:
            continue
        yield path


def python_version_fix(project: Path, required_text: str) -> str:
    major_minor = ".".join(required_text.split(".")[:2])
    if is_windows():
        if command_exists("py"):
            return (
                f"py -{major_minor} -m venv .venv && "
                f".venv\\Scripts\\activate"
            )
        slug = major_minor.replace(".", "")
        return f"winget install Python.Python.{slug}"
    if (project / ".python-version").is_file() and command_exists("pyenv"):
        return f"pyenv install {required_text} && pyenv local {required_text}"
    return f"Install Python {required_text} and recreate your virtual environment."


def node_version_fix(required_text: str) -> str:
    if is_windows():
        if command_exists("nvm"):
            return f"nvm install {required_text} && nvm use {required_text}"
        major = required_text.split(".")[0]
        return f"winget install OpenJS.NodeJS --version {major}.0.0"
    return f"nvm install {required_text} && nvm use {required_text}"


def java_version_fix(required_text: str) -> str:
    major = required_text.split(".")[0]
    if is_windows():
        return f"winget install Microsoft.OpenJDK.{major}"
    if platform.system() == "Darwin":
        return f"brew install openjdk@{major}"
    return f"Install JDK {required_text} with your package manager or sdkman."


def go_version_fix(required_text: str) -> str:
    if is_windows():
        return "winget install GoLang.Go"
    return f"Install Go {required_text} from https://go.dev/dl/"


def dotnet_version_fix(required_text: str) -> str:
    major = required_text.split(".")[0]
    if is_windows():
        return f"winget install Microsoft.DotNet.SDK.{major}"
    return f"Install .NET SDK {required_text} from https://dotnet.microsoft.com/download"


def php_version_fix(required_text: str) -> str:
    if is_windows():
        return "winget install PHP.PHP"
    return f"Install PHP {required_text} with your package manager."


def rust_version_fix(required_text: str) -> str:
    if command_exists("rustup"):
        return f"rustup toolchain install {required_text} && rustup default {required_text}"
    return "Install rustup, then install the required Rust toolchain."


def ruby_version_fix(required_text: str) -> str:
    if is_windows():
        return "winget install RubyInstallerTeam.RubyWithDevKit"
    return f"Install Ruby {required_text} with rbenv, asdf, or your package manager."


def copy_env_command(project: Path) -> str:
    example = project / ".env.example"
    target = project / ".env"
    if is_windows():
        return f'Copy-Item "{example.name}" "{target.name}"'
    return f'cp "{example.name}" "{target.name}"'


def docker_install_fix() -> str:
    if is_windows():
        return "winget install Docker.DockerDesktop"
    if platform.system() == "Darwin":
        return "brew install --cask docker"
    return "curl -fsSL https://get.docker.com | sh"


def docker_daemon_fix() -> str:
    if is_windows():
        return "Start-Process 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe'"
    if platform.system() == "Darwin":
        return "open -a Docker"
    if command_exists("systemctl"):
        return "sudo systemctl start docker"
    return "Start the Docker daemon for your platform (e.g. systemctl or Docker Desktop)."


def terraform_install_fix() -> str:
    if is_windows():
        return "winget install Hashicorp.Terraform"
    return "Install Terraform from https://developer.hashicorp.com/terraform/downloads"


def kubectl_install_fix() -> str:
    if is_windows():
        return "winget install Kubernetes.kubectl"
    if platform.system() == "Darwin":
        return "brew install kubectl"
    return "Install kubectl using your package manager."


def venv_create_and_activate_fix() -> str:
    if is_windows():
        return "python -m venv .venv && .venv\\Scripts\\activate"
    return "python3 -m venv .venv && source .venv/bin/activate"


def parse_version_numbers(version: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version.strip())
    if not match:
        return (0, 0, 0)
    major, minor, patch = match.groups()
    return (int(major), int(minor), int(patch or 0))


def version_to_string(version: tuple[int, int, int]) -> str:
    return f"{version[0]}.{version[1]}.{version[2]}"


def compare_versions(
    current: tuple[int, int, int],
    required: tuple[int, int, int],
) -> int:
    if current == required:
        return 0
    if current > required:
        return 1
    return -1


def satisfies_minimum(
    current: tuple[int, int, int],
    required: tuple[int, int, int],
) -> bool:
    return compare_versions(current, required) >= 0


def extract_minimum_version(spec: str) -> tuple[int, int, int] | None:
    cleaned = spec.strip().strip('"').strip("'")
    for pattern in (
        r">=\s*(\d+(?:\.\d+){0,2})",
        r"\^(\d+(?:\.\d+){0,2})",
        r"~(\d+(?:\.\d+){0,2})",
        r"(\d+(?:\.\d+){0,2})",
    ):
        match = re.search(pattern, cleaned)
        if match:
            return parse_version_numbers(match.group(1))
    return None
