"""Project detection and dependency sensing for DepGuard."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from checks.base import iter_project_files, normalize_dependency_name, read_text


NODE_SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
CONFIG_SUFFIXES = {
    ".env",
    ".example",
    ".ini",
    ".json",
    ".php",
    ".properties",
    ".rb",
    ".tf",
    ".toml",
    ".yaml",
    ".yml",
}

LANGUAGE_FILES = {
    "python": {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", ".python-version"},
    "node": {"package.json", ".nvmrc"},
    "java": {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"},
    "go": {"go.mod"},
    "dotnet": {"global.json"},
    "php": {"composer.json"},
    "rust": {"Cargo.toml", "rust-toolchain", "rust-toolchain.toml"},
    "ruby": {"Gemfile", ".ruby-version"},
}

LANGUAGE_SUFFIXES = {
    "python": {".py"},
    "node": NODE_SOURCE_SUFFIXES,
    "java": {".java"},
    "go": {".go"},
    "dotnet": {".cs", ".csproj", ".sln"},
    "php": {".php"},
    "rust": {".rs"},
    "ruby": {".rb"},
}

PYTHON_IMPORT_MAP = {
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "psycopg": "psycopg",
    "psycopg2": "psycopg2",
    "asyncpg": "asyncpg",
    "pg8000": "pg8000",
    "pymysql": "pymysql",
    "mysql": "mysql-connector-python",
    "pymongo": "pymongo",
    "motor": "motor",
    "redis": "redis",
    "cx_oracle": "cx-oracle",
    "oracledb": "oracledb",
}

NODE_IMPORT_MAP = {
    "react": "react",
    "next": "next",
    "pg": "pg",
    "postgres": "postgres",
    "mysql": "mysql",
    "mysql2": "mysql2",
    "mongodb": "mongodb",
    "mongoose": "mongoose",
    "redis": "redis",
    "ioredis": "ioredis",
    "oracledb": "oracledb",
}

JAVA_IMPORT_HINTS = {
    "org.springframework.boot": "spring-boot",
    "org.springframework.web": "spring-web",
    "org.postgresql": "postgresql",
    "com.mysql": "mysql-connector-java",
    "com.mongodb": "mongodb-driver-sync",
    "redis.clients.jedis": "jedis",
    "io.lettuce.core": "lettuce-core",
    "oracle.jdbc": "ojdbc11",
}

GO_IMPORT_HINTS = {
    "github.com/jackc/pgx": "github.com/jackc/pgx/v5",
    "github.com/lib/pq": "github.com/lib/pq",
    "github.com/go-sql-driver/mysql": "github.com/go-sql-driver/mysql",
    "go.mongodb.org/mongo-driver": "go.mongodb.org/mongo-driver",
    "github.com/redis/go-redis": "github.com/redis/go-redis/v9",
    "github.com/godror/godror": "github.com/godror/godror",
}

DOTNET_USING_HINTS = {
    "microsoft.aspnetcore": "microsoft.aspnetcore.app",
    "npgsql": "npgsql",
    "mysqlconnector": "mysqlconnector",
    "mysql.data": "mysql.data",
    "mongodb.driver": "mongodb.driver",
    "stackexchange.redis": "stackexchange.redis",
    "oracle.manageddataaccess": "oracle.manageddataaccess",
}

PHP_USE_HINTS = {
    "illuminate\\": "laravel/framework",
    "laravel\\": "laravel/framework",
    "mongodb\\": "mongodb/mongodb",
    "predis\\": "predis/predis",
    "redis\\": "ext-redis",
    "yajra\\oci8\\": "yajra/laravel-oci8",
}

RUST_USE_HINTS = {
    "postgres": "postgres",
    "tokio_postgres": "tokio-postgres",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "redis": "redis",
    "oracle": "oracle",
}

RUBY_REQUIRE_HINTS = {
    "rails": "rails",
    "pg": "pg",
    "mysql2": "mysql2",
    "mongo": "mongo",
    "redis": "redis",
    "ruby-oci8": "ruby-oci8",
}

FRAMEWORK_DEPENDENCIES = {
    "react": "React",
    "next": "Next.js",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring-boot": "Spring Boot",
    "spring-web": "Spring Boot",
    "microsoft.aspnetcore.app": "ASP.NET",
    "laravel/framework": "Laravel",
    "rails": "Ruby on Rails",
}

DATABASE_DEPENDENCIES = {
    "psycopg": "PostgreSQL",
    "psycopg2": "PostgreSQL",
    "asyncpg": "PostgreSQL",
    "pg8000": "PostgreSQL",
    "pg": "PostgreSQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "github.com/jackc/pgx/v5": "PostgreSQL",
    "github.com/lib/pq": "PostgreSQL",
    "npgsql": "PostgreSQL",
    "pymysql": "MySQL",
    "mysql": "MySQL",
    "mysql2": "MySQL",
    "mysql-connector-python": "MySQL",
    "mysql-connector-java": "MySQL",
    "github.com/go-sql-driver/mysql": "MySQL",
    "mysqlconnector": "MySQL",
    "mysql.data": "MySQL",
    "pymongo": "MongoDB",
    "motor": "MongoDB",
    "mongodb": "MongoDB",
    "mongoose": "MongoDB",
    "mongodb-driver-sync": "MongoDB",
    "go.mongodb.org/mongo-driver": "MongoDB",
    "mongodb.driver": "MongoDB",
    "redis": "Redis",
    "ioredis": "Redis",
    "jedis": "Redis",
    "lettuce-core": "Redis",
    "github.com/redis/go-redis/v9": "Redis",
    "stackexchange.redis": "Redis",
    "predis/predis": "Redis",
    "ext-redis": "Redis",
    "cx-oracle": "Oracle Database",
    "oracledb": "Oracle Database",
    "ojdbc11": "Oracle Database",
    "github.com/godror/godror": "Oracle Database",
    "oracle.manageddataaccess": "Oracle Database",
    "yajra/laravel-oci8": "Oracle Database",
    "oracle": "Oracle Database",
    "ruby-oci8": "Oracle Database",
}

DEPENDENCY_EQUIVALENTS = {
    "spring-boot": {"spring-boot", "spring-boot-starter", "spring-boot-starter-web", "spring-boot-starter-webflux"},
    "microsoft.aspnetcore.app": {"microsoft.aspnetcore.app", "microsoft.net.sdk.web"},
    "laravel/framework": {"laravel/framework"},
    "rails": {"rails"},
}


@dataclass(frozen=True)
class ProjectContext:
    project: Path
    languages: frozenset[str]
    frameworks: frozenset[str]
    infrastructure: frozenset[str]
    databases: frozenset[str]
    declared_dependencies: dict[str, frozenset[str]]
    inferred_dependencies: dict[str, frozenset[str]]
    config_text: str

    def has_language(self, name: str) -> bool:
        return name in self.languages

    def has_framework(self, name: str) -> bool:
        return name in self.frameworks

    def has_infrastructure(self, name: str) -> bool:
        return name in self.infrastructure

    def has_database(self, name: str) -> bool:
        return name in self.databases

    def declared_for(self, ecosystem: str) -> frozenset[str]:
        return self.declared_dependencies.get(ecosystem, frozenset())

    def inferred_for(self, ecosystem: str) -> frozenset[str]:
        return self.inferred_dependencies.get(ecosystem, frozenset())

    def declares_dependency(self, ecosystem: str, name: str) -> bool:
        declared = self.declared_for(ecosystem)
        lowered = name.lower()
        aliases = DEPENDENCY_EQUIVALENTS.get(lowered, {lowered})
        for candidate in aliases:
            if candidate in declared:
                return True
            if candidate in {"spring-boot"} and any(dep.startswith("spring-boot") for dep in declared):
                return True
        return False


def detect_project(project: Path) -> ProjectContext:
    declared = {
        "python": _declared_python_dependencies(project),
        "node": _declared_node_dependencies(project),
        "java": _declared_java_dependencies(project),
        "go": _declared_go_dependencies(project),
        "dotnet": _declared_dotnet_dependencies(project),
        "php": _declared_php_dependencies(project),
        "rust": _declared_rust_dependencies(project),
        "ruby": _declared_ruby_dependencies(project),
    }
    inferred: dict[str, set[str]] = defaultdict(set)
    languages = _detect_languages(project)
    frameworks: set[str] = set()
    databases: set[str] = set()
    infrastructure = _detect_infrastructure(project)

    for path in iter_project_files(project):
        suffix = path.suffix.lower()
        if suffix not in {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".mjs",
            ".cjs",
            ".java",
            ".go",
            ".cs",
            ".php",
            ".rs",
            ".rb",
        }:
            continue
        try:
            text = read_text(path)
        except RuntimeError:
            continue

        if suffix == ".py":
            _apply_signals(_infer_python_dependencies(text), "python", inferred, frameworks, databases)
        elif suffix in NODE_SOURCE_SUFFIXES:
            _apply_signals(_infer_node_dependencies(text), "node", inferred, frameworks, databases)
        elif suffix == ".java":
            _apply_signals(_infer_java_dependencies(text), "java", inferred, frameworks, databases)
        elif suffix == ".go":
            _apply_signals(_infer_go_dependencies(text), "go", inferred, frameworks, databases)
        elif suffix == ".cs":
            _apply_signals(_infer_dotnet_dependencies(text), "dotnet", inferred, frameworks, databases)
        elif suffix == ".php":
            _apply_signals(_infer_php_dependencies(text), "php", inferred, frameworks, databases)
        elif suffix == ".rs":
            _apply_signals(_infer_rust_dependencies(text), "rust", inferred, frameworks, databases)
        elif suffix == ".rb":
            _apply_signals(_infer_ruby_dependencies(text), "ruby", inferred, frameworks, databases)

    for ecosystem, deps in declared.items():
        for dep in deps:
            framework = FRAMEWORK_DEPENDENCIES.get(dep)
            if framework:
                frameworks.add(framework)
            database = DATABASE_DEPENDENCIES.get(dep)
            if database:
                databases.add(database)

    frameworks.update(_detect_framework_markers(project))
    databases.update(_detect_database_markers(project))

    return ProjectContext(
        project=project,
        languages=frozenset(sorted(languages)),
        frameworks=frozenset(sorted(frameworks)),
        infrastructure=frozenset(sorted(infrastructure)),
        databases=frozenset(sorted(databases)),
        declared_dependencies={key: frozenset(sorted(value)) for key, value in declared.items()},
        inferred_dependencies={key: frozenset(sorted(value)) for key, value in inferred.items()},
        config_text=_build_config_text(project),
    )


def _apply_signals(
    dependencies: set[str],
    ecosystem: str,
    inferred: dict[str, set[str]],
    frameworks: set[str],
    databases: set[str],
) -> None:
    for dependency in dependencies:
        inferred[ecosystem].add(dependency)
        framework = FRAMEWORK_DEPENDENCIES.get(dependency)
        if framework:
            frameworks.add(framework)
        database = DATABASE_DEPENDENCIES.get(dependency)
        if database:
            databases.add(database)


def _detect_languages(project: Path) -> set[str]:
    languages: set[str] = set()
    for language, names in LANGUAGE_FILES.items():
        if any((project / name).exists() for name in names):
            languages.add(language)

    for path in iter_project_files(project):
        for language, suffixes in LANGUAGE_SUFFIXES.items():
            if path.suffix.lower() in suffixes:
                languages.add(language)
        if path.suffix.lower() == ".csproj":
            languages.add("dotnet")
    return languages


def _detect_framework_markers(project: Path) -> set[str]:
    frameworks: set[str] = set()
    if (project / "next.config.js").is_file() or (project / "next.config.mjs").is_file():
        frameworks.add("Next.js")
    if (project / "manage.py").is_file():
        frameworks.add("Django")
    if (project / "artisan").is_file():
        frameworks.add("Laravel")
    if (project / "config" / "application.rb").is_file():
        frameworks.add("Ruby on Rails")
    if (project / "Program.cs").is_file():
        try:
            text = read_text(project / "Program.cs")
        except RuntimeError:
            text = ""
        if "Microsoft.AspNetCore" in text or "WebApplication.CreateBuilder" in text:
            frameworks.add("ASP.NET")
    if _has_spring_boot_annotation(project):
        frameworks.add("Spring Boot")
    return frameworks


def _detect_infrastructure(project: Path) -> set[str]:
    infrastructure: set[str] = set()
    if (project / "Dockerfile").is_file() or (project / "dockerfile").is_file():
        infrastructure.add("Docker")
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        if (project / name).is_file():
            infrastructure.add("Docker Compose")
            break
    workflows = project / ".github" / "workflows"
    if workflows.is_dir() and any(workflows.glob("*.y*ml")):
        infrastructure.add("GitHub Actions")
    if any(project.rglob("*.tf")) or (project / ".terraform.lock.hcl").is_file():
        infrastructure.add("Terraform")
    if _has_kubernetes_manifest(project):
        infrastructure.add("Kubernetes")
    return infrastructure


def _detect_database_markers(project: Path) -> set[str]:
    databases: set[str] = set()
    config_text = _build_config_text(project)
    if any(token in config_text for token in ("postgres://", "postgresql://", "jdbc:postgresql:", "npgsql", "pg_host")):
        databases.add("PostgreSQL")
    if any(token in config_text for token in ("mysql://", "jdbc:mysql:", "mysql_host", "pdo_mysql")):
        databases.add("MySQL")
    if any(token in config_text for token in ("mongodb://", "mongodb+srv://", "mongodb_uri")):
        databases.add("MongoDB")
    if any(token in config_text for token in ("redis://", "redis_url", "stackexchange.redis")):
        databases.add("Redis")
    if any(token in config_text for token in ("jdbc:oracle:", "oracle.manageddataaccess", "oci8", "oracle_dsn")):
        databases.add("Oracle Database")
    return databases


def _build_config_text(project: Path) -> str:
    parts: list[str] = []
    for path in iter_project_files(project):
        if path.suffix.lower() not in CONFIG_SUFFIXES and not path.name.startswith(".env"):
            continue
        try:
            parts.append(read_text(path).lower())
        except RuntimeError:
            continue
    return "\n".join(parts)


def _declared_python_dependencies(project: Path) -> set[str]:
    dependencies: set[str] = set()
    req_file = project / "requirements.txt"
    if req_file.is_file():
        try:
            for line in read_text(req_file).splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                    continue
                dependencies.add(normalize_dependency_name(stripped))
        except RuntimeError:
            pass

    pyproject = project / "pyproject.toml"
    if pyproject.is_file():
        try:
            content = read_text(pyproject)
        except RuntimeError:
            content = ""
        for block in re.findall(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL):
            for entry in re.findall(r'["\']([^"\']+)["\']', block):
                dependencies.add(normalize_dependency_name(entry))
    return dependencies


def _declared_node_dependencies(project: Path) -> set[str]:
    package_json = project / "package.json"
    if not package_json.is_file():
        return set()
    try:
        data = json.loads(read_text(package_json))
    except (RuntimeError, json.JSONDecodeError):
        return set()
    dependencies: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        section = data.get(key) or {}
        dependencies.update(normalize_dependency_name(name) for name in section)
    return dependencies


def _declared_java_dependencies(project: Path) -> set[str]:
    dependencies: set[str] = set()
    pom = project / "pom.xml"
    if pom.is_file():
        try:
            content = read_text(pom)
        except RuntimeError:
            content = ""
        for block in re.findall(r"<dependency>(.*?)</dependency>", content, re.DOTALL):
            artifact = re.search(r"<artifactId>([^<]+)</artifactId>", block)
            if artifact:
                dependencies.add(normalize_dependency_name(artifact.group(1)))
    for name in ("build.gradle", "build.gradle.kts"):
        path = project / name
        if not path.is_file():
            continue
        try:
            content = read_text(path)
        except RuntimeError:
            continue
        for match in re.finditer(r"['\"]([^:'\"]+):([^:'\"]+):[^'\"]+['\"]", content):
            dependencies.add(normalize_dependency_name(match.group(2)))
    return dependencies


def _declared_go_dependencies(project: Path) -> set[str]:
    go_mod = project / "go.mod"
    if not go_mod.is_file():
        return set()
    try:
        content = read_text(go_mod)
    except RuntimeError:
        return set()
    dependencies: set[str] = set()
    for match in re.finditer(r"^\s*require\s+([^\s]+)\s+", content, re.MULTILINE):
        dependencies.add(normalize_dependency_name(match.group(1)))
    for block in re.findall(r"require\s*\((.*?)\)", content, re.DOTALL):
        for line in block.splitlines():
            parts = line.strip().split()
            if parts:
                dependencies.add(normalize_dependency_name(parts[0]))
    return dependencies


def _declared_dotnet_dependencies(project: Path) -> set[str]:
    dependencies: set[str] = set()
    for path in project.rglob("*.csproj"):
        if "bin" in path.parts or "obj" in path.parts:
            continue
        try:
            content = read_text(path)
        except RuntimeError:
            continue
        project_sdk = re.search(r'<Project\s+Sdk="([^"]+)"', content)
        if project_sdk:
            dependencies.add(normalize_dependency_name(project_sdk.group(1)))
        for match in re.finditer(r'<PackageReference\s+Include="([^"]+)"', content):
            dependencies.add(normalize_dependency_name(match.group(1)))
    return dependencies


def _declared_php_dependencies(project: Path) -> set[str]:
    composer_json = project / "composer.json"
    if not composer_json.is_file():
        return set()
    try:
        data = json.loads(read_text(composer_json))
    except (RuntimeError, json.JSONDecodeError):
        return set()
    dependencies: set[str] = set()
    for key in ("require", "require-dev"):
        section = data.get(key) or {}
        dependencies.update(normalize_dependency_name(name) for name in section)
    return dependencies


def _declared_rust_dependencies(project: Path) -> set[str]:
    cargo = project / "Cargo.toml"
    if not cargo.is_file():
        return set()
    try:
        content = read_text(cargo)
    except RuntimeError:
        return set()
    dependencies: set[str] = set()
    in_dependencies = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_dependencies = stripped in {
                "[dependencies]",
                "[dev-dependencies]",
                "[workspace.dependencies]",
            }
            continue
        if in_dependencies and "=" in stripped:
            dependencies.add(normalize_dependency_name(stripped.split("=", maxsplit=1)[0]))
    return dependencies


def _declared_ruby_dependencies(project: Path) -> set[str]:
    gemfile = project / "Gemfile"
    if not gemfile.is_file():
        return set()
    try:
        content = read_text(gemfile)
    except RuntimeError:
        return set()
    return {
        normalize_dependency_name(match.group(1))
        for match in re.finditer(r'^\s*gem\s+["\']([^"\']+)["\']', content, re.MULTILINE)
    }


def _infer_python_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    for match in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_][\w\.]*)", text, re.MULTILINE):
        module = match.group(1).split(".", maxsplit=1)[0].lower()
        dependency = PYTHON_IMPORT_MAP.get(module)
        if dependency:
            dependencies.add(dependency)
    return dependencies


def _infer_node_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    patterns = (
        r'from\s+["\']([^"\']+)["\']',
        r'require\(\s*["\']([^"\']+)["\']\s*\)',
        r'import\(\s*["\']([^"\']+)["\']\s*\)',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            package_name = _normalize_node_package(match.group(1))
            dependency = NODE_IMPORT_MAP.get(package_name)
            if dependency:
                dependencies.add(dependency)
    return dependencies


def _infer_java_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    for match in re.finditer(r"^\s*import\s+([A-Za-z_][\w\.]+)", text, re.MULTILINE):
        imported = match.group(1)
        for prefix, dependency in JAVA_IMPORT_HINTS.items():
            if imported.startswith(prefix):
                dependencies.add(dependency)
    return dependencies


def _infer_go_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    for match in re.finditer(r'^\s*"([^"]+)"', text, re.MULTILINE):
        imported = normalize_dependency_name(match.group(1))
        for prefix, dependency in GO_IMPORT_HINTS.items():
            if imported.startswith(prefix):
                dependencies.add(dependency)
    return dependencies


def _infer_dotnet_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    for match in re.finditer(r"^\s*using\s+([A-Za-z_][\w\.]+)", text, re.MULTILINE):
        imported = match.group(1).lower()
        for prefix, dependency in DOTNET_USING_HINTS.items():
            if imported.startswith(prefix):
                dependencies.add(dependency)
    return dependencies


def _infer_php_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    for match in re.finditer(r"^\s*use\s+([A-Za-z_\\][\w\\]+)", text, re.MULTILINE):
        imported = match.group(1).lower()
        for prefix, dependency in PHP_USE_HINTS.items():
            if imported.startswith(prefix):
                dependencies.add(dependency)
    return dependencies


def _infer_rust_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    patterns = (
        r"^\s*use\s+([A-Za-z_][\w:]*)",
        r"^\s*extern\s+crate\s+([A-Za-z_][\w]*)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            root = match.group(1).split("::", maxsplit=1)[0].lower()
            dependency = RUST_USE_HINTS.get(root)
            if dependency:
                dependencies.add(dependency)
    return dependencies


def _infer_ruby_dependencies(text: str) -> set[str]:
    dependencies: set[str] = set()
    for match in re.finditer(r'^\s*require\s+["\']([^"\']+)["\']', text, re.MULTILINE):
        required = match.group(1).lower()
        dependency = RUBY_REQUIRE_HINTS.get(required)
        if dependency:
            dependencies.add(dependency)
    if "Rails.application" in text:
        dependencies.add("rails")
    return dependencies


def _normalize_node_package(specifier: str) -> str:
    cleaned = specifier.strip().lower()
    if cleaned.startswith("."):
        return ""
    if cleaned.startswith("@"):
        parts = cleaned.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else cleaned
    return cleaned.split("/", maxsplit=1)[0]


def _has_kubernetes_manifest(project: Path) -> bool:
    for path in iter_project_files(project, suffixes={".yml", ".yaml"}):
        try:
            text = read_text(path)
        except RuntimeError:
            continue
        lowered = text.lower()
        if "apiversion:" in lowered and re.search(
            r"kind:\s*(deployment|service|configmap|secret|ingress|statefulset|daemonset|job|cronjob)",
            lowered,
        ):
            return True
    return False


def _has_spring_boot_annotation(project: Path) -> bool:
    for path in iter_project_files(project, suffixes={".java"}):
        try:
            text = read_text(path)
        except RuntimeError:
            continue
        if "@SpringBootApplication" in text:
            return True
    return False
