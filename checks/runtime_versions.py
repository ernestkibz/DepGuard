"""Runtime version checks for additional language ecosystems."""

from __future__ import annotations

import json
import re
import subprocess

from checks.base import (
    CheckResult,
    Status,
    command_exists,
    dotnet_version_fix,
    extract_minimum_version,
    first_line,
    go_version_fix,
    java_version_fix,
    parse_version_numbers,
    php_version_fix,
    read_text,
    ruby_version_fix,
    run_command,
    rust_version_fix,
    satisfies_minimum,
    version_to_string,
)
from checks.detection import ProjectContext


def _evaluate_runtime(
    *,
    context: ProjectContext,
    name: str,
    executable: str,
    args: list[str],
    required: tuple[int, int, int] | None,
    missing_message: str,
    fix_command: str,
) -> CheckResult:
    runtime_label = name.removesuffix(" Version")
    if required is None:
        return CheckResult(name=name, status=Status.PASS, message=missing_message)

    required_text = version_to_string(required)
    if not command_exists(executable):
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"{runtime_label} is not installed, but {required_text} is required.",
            fix_command=fix_command,
            suggestion=(
                f"Install or switch to {runtime_label} {required_text} or newer, "
                "then reopen your shell and rerun DepGuard."
            ),
        )

    try:
        result = run_command(args, cwd=context.project, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"Could not read {name.lower()}: {exc}",
            fix_command=fix_command,
            suggestion=(
                f"Confirm `{executable}` works in this shell and points to the expected "
                f"{runtime_label} installation before rerunning DepGuard."
            ),
        )

    if result.returncode != 0:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"{runtime_label} is installed but version detection failed.",
            fix_command=fix_command,
            suggestion=(
                f"Run `{executable}` manually in this shell, fix any PATH or startup issues, "
                "and then rerun DepGuard."
            ),
        )

    current = parse_version_numbers(f"{result.stdout}\n{result.stderr}")
    current_text = version_to_string(current)
    if satisfies_minimum(current, required):
        return CheckResult(
            name=name,
            status=Status.PASS,
            message=f"{runtime_label} {current_text} satisfies required {required_text}.",
        )

    return CheckResult(
        name=name,
        status=Status.FAIL,
        message=f"{runtime_label} {current_text} does not satisfy required {required_text}.",
        fix_command=fix_command,
        suggestion=(
            f"Switch this project to {runtime_label} {required_text} or newer, "
            "then rerun installs, builds, and DepGuard in the updated shell."
        ),
    )


def _required_java_version(context: ProjectContext) -> tuple[int, int, int] | None:
    pom = context.project / "pom.xml"
    if pom.is_file():
        try:
            content = read_text(pom)
        except RuntimeError:
            content = ""
        for pattern in (
            r"<java\.version>([^<]+)</java\.version>",
            r"<maven\.compiler\.source>([^<]+)</maven\.compiler\.source>",
            r"<maven\.compiler\.target>([^<]+)</maven\.compiler\.target>",
        ):
            match = re.search(pattern, content)
            if match:
                return parse_version_numbers(match.group(1))

    for name in ("build.gradle", "build.gradle.kts"):
        path = context.project / name
        if not path.is_file():
            continue
        try:
            content = read_text(path)
        except RuntimeError:
            continue
        for pattern in (
            r"sourceCompatibility\s*=\s*JavaVersion\.VERSION_(\d+)",
            r"targetCompatibility\s*=\s*JavaVersion\.VERSION_(\d+)",
            r"sourceCompatibility\s*=\s*['\"]([^'\"]+)['\"]",
            r"languageVersion\s*=\s*JavaLanguageVersion\.of\((\d+)\)",
        ):
            match = re.search(pattern, content)
            if match:
                return parse_version_numbers(match.group(1))
    return None


def _required_go_version(context: ProjectContext) -> tuple[int, int, int] | None:
    go_mod = context.project / "go.mod"
    if not go_mod.is_file():
        return None
    try:
        content = read_text(go_mod)
    except RuntimeError:
        return None
    match = re.search(r"^\s*go\s+([0-9]+(?:\.[0-9]+){1,2})", content, re.MULTILINE)
    if match:
        return parse_version_numbers(match.group(1))
    return None


def _required_dotnet_version(context: ProjectContext) -> tuple[int, int, int] | None:
    global_json = context.project / "global.json"
    if global_json.is_file():
        try:
            data = json.loads(read_text(global_json))
        except (RuntimeError, json.JSONDecodeError):
            data = {}
        sdk = (data.get("sdk") or {}).get("version")
        if sdk:
            return parse_version_numbers(str(sdk))

    for path in context.project.rglob("*.csproj"):
        if "bin" in path.parts or "obj" in path.parts:
            continue
        try:
            content = read_text(path)
        except RuntimeError:
            continue
        match = re.search(r"<TargetFramework>net([0-9]+(?:\.[0-9]+)?)</TargetFramework>", content)
        if match:
            return parse_version_numbers(match.group(1))
    return None


def _required_php_version(context: ProjectContext) -> tuple[int, int, int] | None:
    composer_json = context.project / "composer.json"
    if not composer_json.is_file():
        return None
    try:
        data = json.loads(read_text(composer_json))
    except (RuntimeError, json.JSONDecodeError):
        return None
    require = data.get("require") or {}
    php_spec = require.get("php") or (((data.get("config") or {}).get("platform")) or {}).get("php")
    if php_spec:
        return extract_minimum_version(str(php_spec))
    return None


def _required_rust_version(context: ProjectContext) -> tuple[int, int, int] | None:
    rust_toolchain_toml = context.project / "rust-toolchain.toml"
    if rust_toolchain_toml.is_file():
        try:
            content = read_text(rust_toolchain_toml)
        except RuntimeError:
            content = ""
        match = re.search(r'channel\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            channel = match.group(1).strip()
            if re.match(r"^\d+(?:\.\d+){0,2}$", channel):
                return parse_version_numbers(channel)
            return None

    rust_toolchain = context.project / "rust-toolchain"
    if rust_toolchain.is_file():
        try:
            channel = first_line(read_text(rust_toolchain)).strip()
        except (RuntimeError, IndexError):
            return None
        if re.match(r"^\d+(?:\.\d+){0,2}$", channel):
            return parse_version_numbers(channel)
        return None

    cargo = context.project / "Cargo.toml"
    if cargo.is_file():
        try:
            content = read_text(cargo)
        except RuntimeError:
            content = ""
        match = re.search(r'rust-version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return parse_version_numbers(match.group(1))
    return None


def _required_ruby_version(context: ProjectContext) -> tuple[int, int, int] | None:
    ruby_version = context.project / ".ruby-version"
    if ruby_version.is_file():
        try:
            return parse_version_numbers(first_line(read_text(ruby_version)))
        except (RuntimeError, IndexError):
            return None

    gemfile = context.project / "Gemfile"
    if gemfile.is_file():
        try:
            content = read_text(gemfile)
        except RuntimeError:
            content = ""
        match = re.search(r'^\s*ruby\s+["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            return parse_version_numbers(match.group(1))
    return None


def check_java_version(context: ProjectContext) -> CheckResult | None:
    if not context.has_language("java"):
        return None
    required = _required_java_version(context)
    return _evaluate_runtime(
        context=context,
        name="Java Version",
        executable="java",
        args=["java", "-version"],
        required=required,
        missing_message="No Java version constraint found (pom.xml or Gradle).",
        fix_command=java_version_fix(version_to_string(required or (17, 0, 0))),
    )


def check_go_version(context: ProjectContext) -> CheckResult | None:
    if not context.has_language("go"):
        return None
    required = _required_go_version(context)
    return _evaluate_runtime(
        context=context,
        name="Go Version",
        executable="go",
        args=["go", "version"],
        required=required,
        missing_message="No Go version constraint found (go.mod).",
        fix_command=go_version_fix(version_to_string(required or (1, 22, 0))),
    )


def check_dotnet_version(context: ProjectContext) -> CheckResult | None:
    if not context.has_language("dotnet"):
        return None
    required = _required_dotnet_version(context)
    return _evaluate_runtime(
        context=context,
        name=".NET Version",
        executable="dotnet",
        args=["dotnet", "--version"],
        required=required,
        missing_message="No .NET SDK version constraint found (global.json or .csproj).",
        fix_command=dotnet_version_fix(version_to_string(required or (8, 0, 0))),
    )


def check_php_version(context: ProjectContext) -> CheckResult | None:
    if not context.has_language("php"):
        return None
    required = _required_php_version(context)
    return _evaluate_runtime(
        context=context,
        name="PHP Version",
        executable="php",
        args=["php", "-v"],
        required=required,
        missing_message="No PHP version constraint found (composer.json).",
        fix_command=php_version_fix(version_to_string(required or (8, 2, 0))),
    )


def check_rust_version(context: ProjectContext) -> CheckResult | None:
    if not context.has_language("rust"):
        return None
    required = _required_rust_version(context)
    return _evaluate_runtime(
        context=context,
        name="Rust Version",
        executable="rustc",
        args=["rustc", "--version"],
        required=required,
        missing_message="No Rust toolchain constraint found (rust-toolchain or Cargo.toml).",
        fix_command=rust_version_fix(version_to_string(required or (1, 75, 0))),
    )


def check_ruby_version(context: ProjectContext) -> CheckResult | None:
    if not context.has_language("ruby"):
        return None
    required = _required_ruby_version(context)
    return _evaluate_runtime(
        context=context,
        name="Ruby Version",
        executable="ruby",
        args=["ruby", "--version"],
        required=required,
        missing_message="No Ruby version constraint found (.ruby-version or Gemfile).",
        fix_command=ruby_version_fix(version_to_string(required or (3, 2, 0))),
    )
