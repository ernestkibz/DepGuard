# DepGuard

DepGuard is the core scan engine. It inspects a local project folder, detects what stack is actually present, and runs only the checks that make sense for that project.

Repository: https://github.com/ernestkibz/DepGuard

Separate Slack repo: https://github.com/ernestkibz/depguard-slack

Important: `DepGuard` and `depguard-slack` are two separate git repositories. A local `depguard-slack/` folder may sit beside this repo for convenience, but it has its own `.git` history and should be committed separately.

---

## README 1 - For Users

### What DepGuard does

DepGuard is a Python CLI that:

- scans any local project folder
- detects languages, frameworks, infrastructure, and database signals
- checks only the relevant setup rules for that project
- prints exact fix commands and situation-aware suggestions when something is missing or broken

Supported detection includes:

- Languages: Python, Node.js, Java, Go, .NET, PHP, Rust, Ruby
- Frameworks: React, Next.js, Django, Flask, FastAPI, Spring Boot, ASP.NET, Laravel, Ruby on Rails
- Infrastructure: Docker, Docker Compose, Kubernetes, GitHub Actions, Terraform
- Databases: PostgreSQL, MySQL, MongoDB, Redis, Oracle Database

### Quick start

```bash
pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.1.0"
depguard /path/to/project
```

Or run from a local clone:

```bash
git clone https://github.com/ernestkibz/DepGuard.git
cd DepGuard
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -e .
depguard .
```

### Command usage

```bash
depguard
depguard /path/to/project
depguard --version
```

### How to read the results

- `PASS` means DepGuard found enough evidence that the check is satisfied.
- `FAIL` means DepGuard found a concrete setup problem or could not run a required dependency/tool check.
- `WARN` means DepGuard found a signal worth reviewing, but not always hard proof of a real production problem.

This distinction matters in grey-area cases.

Examples:

- If source code imports a package but the manifest does not declare it, DepGuard warns that the dependency may be used. That could still be optional code, test code, example code, or an adapter that is not part of the deployed path.
- If DepGuard sees Oracle-related packages or code markers, do not automatically assume the project definitely uses Oracle Database in production. Read it as possible Oracle-related usage detected until config or runtime evidence confirms it.
- If a framework is detected but common files are missing, that can also be normal in monorepos, starter templates, generated examples, or custom layouts.

### Detection-first behavior

DepGuard builds a `ProjectContext` before it runs checks. It uses:

- manifests such as `pyproject.toml`, `package.json`, `pom.xml`, `go.mod`, `.csproj`, `composer.json`, `Cargo.toml`, `Gemfile`
- framework and infrastructure markers such as `next.config.js`, `manage.py`, `Dockerfile`, Compose files, GitHub Actions workflows, and Terraform files
- known source imports and usage patterns

That context decides which checks appear in the report.

### Example output

```text
[PASS] Python Version - Python 3.11.8 satisfies required 3.11.0.
[FAIL] Node Modules - package.json exists but node_modules is missing.
       Suggestion: Run the repository's package manager from the project root, let it restore dependencies from the lockfile, and then rerun the app build or tests.
       Fix: npm install
[WARN] Database Configuration - DepGuard found database-related dependencies or code signals, but could not confirm common connection markers for: Oracle Database. This may be expected if configuration lives in deployment variables, a secrets manager, optional adapters, or non-standard config files.
       Suggestion: Verify the real runtime database from environment variables, secrets management, deployment config, or connection factory code before treating this as a confirmed production dependency.

Final score: 2/3 checks passed
```

Exit code is `0` when all relevant checks pass and `1` when any relevant check fails or warns.

### Screenshots

![DepGuard scan output](docs/screenshots/depguard-scan.png)

---

## README 2 - For Builder/Owner

### What this repo is

This repo is the core engine only.

- CLI entry point: `depguard.py`
- Check modules: `checks/`
- Packaging: `pyproject.toml`
- Current release line documented here: `v1.1.0`

Slack-specific behavior does not belong in this repo. Slack message formatting, slash commands, MCP transport, and Railway deployment live in `depguard-slack`.

### How the core works

```text
depguard.py
  -> detect_project(project) -> ProjectContext
  -> run ALL_CHECKS against that ProjectContext
  -> render PASS / FAIL / WARN output with fix commands
```

Key design choices:

- detection-driven architecture instead of running every check on every repo
- dependency sensing from manifests and source imports
- OS-specific fix commands centralized in `checks/base.py`
- checks return `CheckResult | None` so irrelevant checks quietly skip themselves
- nested directories with their own `.git` folders are ignored during scans

### Grey-area communication model

The wording upgrade in this repo is intentional. Some findings are evidence-based warnings, not hard confirmation.

Current ambiguity-sensitive checks are:

- `Dependency Alignment`
- `Framework Configuration`
- `Database Configuration`

The language now aims to separate:

- confirmed failures
- likely but unconfirmed usage
- common alternative explanations such as optional adapters, examples, tests, monorepo layouts, secrets managers, and custom config paths

This is especially important for foreign or complex repos where a team may over-read a signal as certainty.

### Project story

The build path was:

1. Start with `DepGuard` as the reusable core CLI for local project scanning.
2. Expand detection so the engine can sense stacks from manifests and source code, not manifests alone.
3. Add richer stack coverage across languages, frameworks, infrastructure, and databases.
4. Improve warning language so ambiguous signals are communicated carefully.
5. Build `depguard-slack` as a separate wrapper repo for Slack and MCP use.

### Relationship to `depguard-slack`

`depguard-slack` consumes this engine as a dependency and presents results inside Slack. During local development, the Slack repo can prefer a parent-folder checkout of this repo so unreleased engine changes can be exercised before the next tag.

Keep the repo boundary strict:

- core scanning logic here
- Slack transport and formatting there
- separate git histories for each repo

### Typical files to edit

- `checks/detection.py` for tech detection and source-signal inference
- `checks/__init__.py` for check registration and version
- `checks/base.py` for shared helpers and fix commands
- individual `checks/*.py` modules for targeted logic
- `depguard.py` for CLI rendering and summary behavior

### Extending the engine

1. Add or update detection rules if the new check depends on stack discovery.
2. Implement the check in `checks/`.
3. Register it in `checks/__init__.py`.
4. Add focused tests in `tests/` when the behavior is non-trivial.
5. Keep user wording careful when the check relies on indirect signals.

### Handoff notes

- Do not move Slack bot code into this repo.
- Do not assume a detected database marker proves production usage.
- Keep release tags in sync with docs and downstream `depguard-slack` dependency bumps.
- If demoing the system, common examples include scanning `DepGuard` itself or the Slack demo target repo used in conversations such as `chaosapp-demo`.

For install, CI, Python API, release notes, and builder workflow, see [setup.md](setup.md).

---

## License

MIT - see [LICENSE](LICENSE).
