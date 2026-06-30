#!/usr/bin/env python3
"""DepGuard — scan a project folder and diagnose setup problems."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from checks import ALL_CHECKS, CheckResult, Status, __version__, detect_project


def render_result(console: Console, result: CheckResult) -> None:
    if result.status is Status.PASS:
        icon = "[bold green]✅[/bold green]"
        style = "green"
    elif result.status is Status.FAIL:
        icon = "[bold red]❌[/bold red]"
        style = "red"
    else:
        icon = "[bold yellow]⚠️[/bold yellow]"
        style = "yellow"

    console.print(
        f"{icon} [bold {style}]{result.name}[/bold {style}] — "
        f"[{style}]{result.message}[/{style}]"
    )

    if result.fix_command and result.status is not Status.PASS:
        console.print(f"   [dim]Fix:[/dim] [cyan]{result.fix_command}[/cyan]")


def describe_detected_stack(project_context) -> str:
    parts: list[str] = []
    if project_context.languages:
        parts.append("Languages: " + ", ".join(project_context.languages))
    if project_context.frameworks:
        parts.append("Frameworks: " + ", ".join(project_context.frameworks))
    if project_context.infrastructure:
        parts.append("Infrastructure: " + ", ".join(project_context.infrastructure))
    if project_context.databases:
        parts.append("Databases: " + ", ".join(project_context.databases))
    return "\n".join(parts) if parts else "No specific technology markers detected."


def run_checks(project: Path) -> list[CheckResult]:
    project_context = detect_project(project)
    results: list[CheckResult] = []
    for display_name, check_fn in ALL_CHECKS:
        try:
            result = check_fn(project_context)
            if result is not None:
                results.append(result)
        except Exception as exc:  # noqa: BLE001 — surface unexpected check failures
            results.append(
                CheckResult(
                    name=display_name,
                    status=Status.FAIL,
                    message=f"Check crashed: {exc}",
                    fix_command=None,
                )
            )
    return results


def score_results(results: list[CheckResult]) -> int:
    return sum(1 for result in results if result.status is Status.PASS)


def build_summary_table(results: list[CheckResult], passed: int) -> Table:
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Check", ratio=2)
    table.add_column("Status", ratio=1)
    table.add_column("Details", ratio=4)

    status_labels = {
        Status.PASS: ("✅ Pass", "green"),
        Status.FAIL: ("❌ Fail", "red"),
        Status.WARN: ("⚠️ Warn", "yellow"),
    }

    for result in results:
        label, color = status_labels[result.status]
        table.add_row(result.name, f"[{color}]{label}[/{color}]", result.message)

    table.add_section()
    table.add_row(
        "Summary",
        f"[bold]{passed}/{len(results)} checks passed[/bold]",
        "",
    )
    return table


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except (OSError, ValueError):
                    pass

    parser = argparse.ArgumentParser(
        prog="depguard",
        description="DepGuard — scan a project folder and diagnose setup problems across languages and tools.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project folder to scan (default: current directory)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"DepGuard {__version__}",
    )
    args = parser.parse_args(argv)

    console = Console()
    project = Path(args.path).expanduser().resolve()

    if not project.exists():
        console.print(f"[bold red]Error:[/bold red] Path does not exist: {project}")
        return 1

    if not project.is_dir():
        console.print(f"[bold red]Error:[/bold red] Path is not a directory: {project}")
        return 1

    project_context = detect_project(project)
    console.print(
        Panel.fit(
            "[bold]DepGuard[/bold]\n"
            f"Scanning: [cyan]{project}[/cyan]\n"
            f"{describe_detected_stack(project_context)}",
            border_style="blue",
        )
    )
    console.print()

    results = run_checks(project)
    passed = score_results(results)

    for result in results:
        render_result(console, result)
        console.print()

    console.print(build_summary_table(results, passed))
    console.print()
    console.print(f"[bold]Final score:[/bold] {passed}/{len(results)} checks passed")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
