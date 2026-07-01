"""Checks for HTML, JavaScript, and TypeScript web content."""

from __future__ import annotations

from checks.base import CheckResult, Status, iter_project_files
from checks.detection import ProjectContext

HTML_SUFFIXES = {".html", ".htm"}
JAVASCRIPT_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs"}
TYPESCRIPT_SUFFIXES = {".ts", ".tsx"}


def _count_files(project, suffixes: set[str]) -> int:
    return sum(
        1
        for path in iter_project_files(project, suffixes=suffixes)
    )


def check_html_content(context: ProjectContext) -> CheckResult | None:
    name = "HTML Content"
    if not context.has_language("html"):
        return None

    project = context.project
    html_count = _count_files(project, HTML_SUFFIXES)
    has_package_json = (project / "package.json").is_file()
    file_note = f"{html_count} HTML file{'s' if html_count != 1 else ''}"

    if has_package_json:
        return CheckResult(
            name=name,
            status=Status.PASS,
            message=f"HTML content detected ({file_note}) alongside a Node.js manifest.",
        )

    return CheckResult(
        name=name,
        status=Status.PASS,
        message=(
            f"HTML content detected ({file_note}). "
            "This looks like a static web or data site without a Node.js package manifest."
        ),
        suggestion=(
            "If this site uses build tooling or npm dependencies, add a package.json. "
            "Otherwise no Node setup is required for plain HTML assets."
        ),
    )


def check_javascript_manifest(context: ProjectContext) -> CheckResult | None:
    name = "JavaScript / TypeScript Manifest"
    has_js = context.has_language("javascript")
    has_ts = context.has_language("typescript")
    if not has_js and not has_ts:
        return None

    project = context.project
    package_json = project / "package.json"
    labels: list[str] = []
    if has_js:
        labels.append("JavaScript")
    if has_ts:
        labels.append("TypeScript")
    stack = " and ".join(labels)

    if package_json.is_file():
        return CheckResult(
            name=name,
            status=Status.PASS,
            message=f"{stack} source detected and package.json is present.",
        )

    js_count = _count_files(project, JAVASCRIPT_SUFFIXES)
    ts_count = _count_files(project, TYPESCRIPT_SUFFIXES)
    return CheckResult(
        name=name,
        status=Status.WARN,
        message=(
            f"{stack} source detected ({js_count} JS, {ts_count} TS files) "
            "but no package.json was found."
        ),
        fix_command="npm init -y",
        suggestion=(
            "Add a package.json if this project uses npm dependencies, a bundler, or a "
            "Node-based dev server. Skip this if the scripts are standalone browser files only."
        ),
    )


def check_typescript_configuration(context: ProjectContext) -> CheckResult | None:
    name = "TypeScript Configuration"
    if not context.has_language("typescript"):
        return None

    project = context.project
    tsconfig_candidates = (
        "tsconfig.json",
        "tsconfig.base.json",
        "tsconfig.app.json",
        "jsconfig.json",
    )
    if any((project / name).is_file() for name in tsconfig_candidates):
        return CheckResult(
            name=name,
            status=Status.PASS,
            message="TypeScript source detected and a tsconfig/jsconfig file is present.",
        )

    ts_count = _count_files(project, TYPESCRIPT_SUFFIXES)
    return CheckResult(
        name=name,
        status=Status.WARN,
        message=(
            f"TypeScript source detected ({ts_count} file{'s' if ts_count != 1 else ''}) "
            "but no tsconfig.json or jsconfig.json was found."
        ),
        fix_command="npx tsc --init",
        suggestion=(
            "Add a tsconfig.json if this project is compiled or type-checked with TypeScript. "
            "Standalone .ts snippets or generated files may not need one."
        ),
    )
