"""Database configuration checks based on detected dependencies and config signals."""

from __future__ import annotations

from checks.base import CheckResult, Status
from checks.detection import ProjectContext


DATABASE_PATTERNS = {
    "PostgreSQL": ("postgres://", "postgresql://", "jdbc:postgresql:", "pg_host", "postgres_host", "npgsql"),
    "MySQL": ("mysql://", "jdbc:mysql:", "mysql_host", "mysql_database", "pdo_mysql"),
    "MongoDB": ("mongodb://", "mongodb+srv://", "mongodb_uri", "mongo_url"),
    "Redis": ("redis://", "redis_url", "redis_host", "stackexchange.redis"),
    "Oracle Database": ("jdbc:oracle:", "oracle_dsn", "oracle.manageddataaccess", "oci8"),
}


def check_database_configuration(context: ProjectContext) -> CheckResult | None:
    name = "Database Configuration"
    if not context.databases:
        return None

    configured: list[str] = []
    missing: list[str] = []
    config_text = context.config_text

    for database in sorted(context.databases):
        patterns = DATABASE_PATTERNS.get(database, ())
        if any(pattern in config_text for pattern in patterns):
            configured.append(database)
        else:
            missing.append(database)

    if missing:
        return CheckResult(
            name=name,
            status=Status.WARN,
            message=(
                "DepGuard found database-related dependencies or code signals, but could not confirm common connection markers for: "
                + ", ".join(missing)
                + ". This may be expected if configuration lives in deployment variables, a secrets manager, optional adapters, or non-standard config files."
            ),
            suggestion=(
                "Verify the real runtime database from environment variables, secrets management, deployment config, "
                "or connection factory code before treating this as a confirmed production dependency."
            ),
        )

    return CheckResult(
        name=name,
        status=Status.PASS,
        message="Detected database configuration markers for " + ", ".join(configured) + ".",
    )
