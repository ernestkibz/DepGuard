"""DepGuard — project setup checks."""

__version__ = "1.0.1"

from checks.base import CheckResult, Status
from checks.docker import check_docker
from checks.env_file import check_env_file
from checks.git_init import check_git_init
from checks.node_modules import check_node_modules
from checks.node_version import check_node_version
from checks.python_version import check_python_version
from checks.requirements import check_requirements
from checks.venv_active import check_venv_active

ALL_CHECKS = [
    ("Python Version", check_python_version),
    ("Node Version", check_node_version),
    ("Requirements Installable", check_requirements),
    ("Node Modules", check_node_modules),
    ("Environment File", check_env_file),
    ("Docker Available", check_docker),
    ("Git Initialized", check_git_init),
    ("Virtual Environment", check_venv_active),
]

__all__ = [
    "ALL_CHECKS",
    "CheckResult",
    "Status",
    "__version__",
]
