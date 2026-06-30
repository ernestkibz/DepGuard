"""Infrastructure-oriented checks for compose, Kubernetes, GitHub Actions, and Terraform."""

from __future__ import annotations

from checks.base import (
    CheckResult,
    Status,
    command_exists,
    kubectl_install_fix,
    terraform_install_fix,
)
from checks.detection import ProjectContext


def check_infrastructure_stack(context: ProjectContext) -> CheckResult | None:
    name = "Infrastructure Stack"
    if not context.infrastructure:
        return None

    messages: list[str] = []
    fix_commands: list[str] = []
    status = Status.PASS

    if context.has_infrastructure("Docker Compose"):
        if command_exists("docker") or command_exists("docker-compose"):
            messages.append("Docker Compose files detected and compose tooling is available")
        else:
            status = Status.WARN
            messages.append("Docker Compose files detected but neither docker nor docker-compose is available")
            fix_commands.append("Install Docker Desktop or docker-compose")

    if context.has_infrastructure("Kubernetes"):
        if command_exists("kubectl"):
            messages.append("Kubernetes manifests detected and kubectl is available")
        else:
            status = Status.WARN
            messages.append("Kubernetes manifests detected but kubectl is missing")
            fix_commands.append(kubectl_install_fix())

    if context.has_infrastructure("GitHub Actions"):
        messages.append("GitHub Actions workflows are present")

    if context.has_infrastructure("Terraform"):
        if command_exists("terraform"):
            messages.append("Terraform files detected and terraform is available")
        else:
            status = Status.WARN
            messages.append("Terraform files detected but terraform is missing")
            fix_commands.append(terraform_install_fix())

    if context.has_infrastructure("Docker") and not messages:
        messages.append("Docker-related project files are present")

    return CheckResult(
        name=name,
        status=status,
        message="; ".join(messages),
        fix_command=" && ".join(dict.fromkeys(fix_commands)) or None,
    )
