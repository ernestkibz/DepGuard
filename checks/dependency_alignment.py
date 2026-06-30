"""Check whether known code-level dependency signals are declared in manifests."""

from __future__ import annotations

from checks.base import CheckResult, Status
from checks.detection import ProjectContext


ECOSYSTEM_LABELS = {
    "python": "Python",
    "node": "Node.js",
    "java": "Java",
    "go": "Go",
    "dotnet": ".NET",
    "php": "PHP",
    "rust": "Rust",
    "ruby": "Ruby",
}


def check_dependency_alignment(context: ProjectContext) -> CheckResult | None:
    name = "Dependency Alignment"
    missing: list[str] = []
    covered: list[str] = []

    for ecosystem, label in ECOSYSTEM_LABELS.items():
        inferred = context.inferred_for(ecosystem)
        if not inferred:
            continue
        declared = context.declared_for(ecosystem)
        missing_here = sorted(dep for dep in inferred if not context.declares_dependency(ecosystem, dep))
        if missing_here:
            missing.append(f"{label}: {', '.join(missing_here)}")
        else:
            covered.append(label)

    if not missing and not covered:
        return None

    if missing:
        return CheckResult(
            name=name,
            status=Status.WARN,
            message=(
                "Code usage suggests dependencies that are not declared in manifests: "
                + "; ".join(missing)
            ),
        )

    return CheckResult(
        name=name,
        status=Status.PASS,
        message=(
            "Known dependencies inferred from source are declared in manifests for "
            + ", ".join(sorted(covered))
            + "."
        ),
    )
