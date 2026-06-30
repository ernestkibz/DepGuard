"""Framework-specific detection and configuration checks."""

from __future__ import annotations

from pathlib import Path

from checks.base import CheckResult, Status, iter_project_files, read_text
from checks.detection import ProjectContext


def _find_file(project: Path, name: str) -> bool:
    return any(path.name == name for path in iter_project_files(project))


def _contains(project: Path, suffixes: set[str], needle: str) -> bool:
    for path in iter_project_files(project, suffixes=suffixes):
        try:
            if needle in read_text(path):
                return True
        except RuntimeError:
            continue
    return False


def check_framework_configuration(context: ProjectContext) -> CheckResult | None:
    name = "Framework Configuration"
    if not context.frameworks:
        return None

    project = context.project
    missing: list[str] = []

    if context.has_framework("React") and not context.has_framework("Next.js"):
        react_entry = any(
            (project / candidate).exists()
            for candidate in ("src/App.jsx", "src/App.tsx", "src/main.jsx", "src/main.tsx")
        )
        if not react_entry:
            missing.append("React: expected a common src entry file such as src/App.tsx or src/main.tsx")

    if context.has_framework("Next.js"):
        has_next_layout = any((project / candidate).exists() for candidate in ("next.config.js", "next.config.mjs"))
        has_next_routes = any((project / candidate).exists() for candidate in ("app", "pages"))
        if not has_next_layout and not has_next_routes:
            missing.append("Next.js: expected next.config.* or an app/pages directory")

    if context.has_framework("Django"):
        if not (project / "manage.py").is_file() and not _find_file(project, "settings.py"):
            missing.append("Django: expected manage.py or settings.py")

    if context.has_framework("Flask"):
        if not _contains(project, {".py"}, "Flask(") and not any((project / candidate).is_file() for candidate in ("app.py", "wsgi.py")):
            missing.append("Flask: expected Flask(...) usage or an app.py/wsgi.py entrypoint")

    if context.has_framework("FastAPI"):
        if not _contains(project, {".py"}, "FastAPI("):
            missing.append("FastAPI: expected FastAPI(...) usage in Python source")

    if context.has_framework("Spring Boot"):
        has_app_config = any(
            (project / candidate).is_file()
            for candidate in (
                "src/main/resources/application.properties",
                "src/main/resources/application.yml",
                "src/main/resources/application.yaml",
            )
        )
        if not has_app_config and not _contains(project, {".java"}, "@SpringBootApplication"):
            missing.append("Spring Boot: expected application.properties/application.yml or @SpringBootApplication")

    if context.has_framework("ASP.NET"):
        if not (project / "Program.cs").is_file() and not _find_file(project, "appsettings.json"):
            missing.append("ASP.NET: expected Program.cs or appsettings.json")

    if context.has_framework("Laravel"):
        if not (project / "artisan").is_file() and not (project / "config" / "app.php").is_file():
            missing.append("Laravel: expected artisan or config/app.php")

    if context.has_framework("Ruby on Rails"):
        has_routes = (project / "config" / "routes.rb").is_file()
        has_application = (project / "config" / "application.rb").is_file()
        if not has_routes or not has_application:
            missing.append("Ruby on Rails: expected config/application.rb and config/routes.rb")

    if missing:
        return CheckResult(
            name=name,
            status=Status.WARN,
            message="Frameworks detected but some common framework files are missing: " + "; ".join(missing),
        )

    return CheckResult(
        name=name,
        status=Status.PASS,
        message="Detected framework configuration looks consistent for " + ", ".join(sorted(context.frameworks)) + ".",
    )
