"""DepGuard — project setup checks."""

__version__ = "1.1.2"

from checks.base import CheckResult, Status
from checks.databases import check_database_configuration
from checks.dependency_alignment import check_dependency_alignment
from checks.detection import ProjectContext, detect_project
from checks.docker import check_docker
from checks.env_file import check_env_file
from checks.frameworks import check_framework_configuration
from checks.git_init import check_git_init
from checks.infrastructure import check_infrastructure_stack
from checks.node_modules import check_node_modules
from checks.node_version import check_node_version
from checks.python_version import check_python_version
from checks.requirements import check_requirements
from checks.runtime_versions import (
    check_dotnet_version,
    check_go_version,
    check_java_version,
    check_php_version,
    check_ruby_version,
    check_rust_version,
)
from checks.venv_active import check_venv_active

from checks.web_frontend import (
    check_html_content,
    check_javascript_manifest,
    check_typescript_configuration,
)

ALL_CHECKS = [
    ("Python Version", check_python_version),
    ("Node Version", check_node_version),
    ("Java Version", check_java_version),
    ("Go Version", check_go_version),
    (".NET Version", check_dotnet_version),
    ("PHP Version", check_php_version),
    ("Rust Version", check_rust_version),
    ("Ruby Version", check_ruby_version),
    ("Requirements Installable", check_requirements),
    ("Node Modules", check_node_modules),
    ("HTML Content", check_html_content),
    ("JavaScript / TypeScript Manifest", check_javascript_manifest),
    ("TypeScript Configuration", check_typescript_configuration),
    ("Dependency Alignment", check_dependency_alignment),
    ("Framework Configuration", check_framework_configuration),
    ("Environment File", check_env_file),
    ("Docker Available", check_docker),
    ("Infrastructure Stack", check_infrastructure_stack),
    ("Database Configuration", check_database_configuration),
    ("Git Initialized", check_git_init),
    ("Virtual Environment", check_venv_active),
]

__all__ = [
    "ALL_CHECKS",
    "CheckResult",
    "ProjectContext",
    "Status",
    "__version__",
    "detect_project",
]
