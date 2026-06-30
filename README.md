# DepGuard

**Scan any project folder. Diagnose setup problems. Get exact fix commands.**

DepGuard is a cross-platform Python CLI that inspects a local project, detects the stacks that are actually present, and runs only the relevant checks for that project. Each issue comes with a copy-paste terminal command tailored to your operating system.

Works on **Windows, macOS, and Linux** — on any project with standard config files.

Repository: **[github.com/ernestkibz/DepGuard](https://github.com/ernestkibz/DepGuard)**

> **Setup guide:** [setup.md](setup.md) — install, CI, Python API, and handoff notes for the next developer.

> **Slack bot (separate repo):** [github.com/ernestkibz/depguard-slack](https://github.com/ernestkibz/depguard-slack) — not part of this git repo. Local copy may exist at `depguard-slack/` (gitignored).

---

## Repositories (important)

| Repo | GitHub | What it is |
|------|--------|------------|
| **DepGuard** | [ernestkibz/DepGuard](https://github.com/ernestkibz/DepGuard) | This repo — CLI only |
| **DepGuard for Slack** | [ernestkibz/depguard-slack](https://github.com/ernestkibz/depguard-slack) | Slack bot + MCP — separate git history |

Current release: **`v1.1.0`** · Entry point: **`depguard.py`**

---

## Quick install

```bash
pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.1.0"
depguard /path/to/your/project
```

---

## Features

DepGuard now detects and routes checks for these stacks:

- **Languages:** Python, Node.js, Java, Go, .NET / C#, PHP, Rust, Ruby
- **Frameworks:** React, Next.js, Django, Flask, FastAPI, Spring Boot, ASP.NET, Laravel, Ruby on Rails
- **Infrastructure:** Docker, Docker Compose, Kubernetes, GitHub Actions, Terraform
- **Databases:** PostgreSQL, MySQL, MongoDB, Redis, Oracle Database
- **Dependency sensing:** compares known code imports and usage against manifest declarations instead of relying only on config files

Representative checks include:

| Check family | What it validates |
|-------------|-------------------|
| Runtime versions | Matches project constraints for Python, Node.js, Java, Go, .NET, PHP, Rust, and Ruby |
| Dependency alignment | Detects known dependencies from source code and verifies they are declared in manifests |
| Framework configuration | Validates common framework entry/config markers only when the framework is detected |
| Infrastructure | Detects Docker, Compose, Kubernetes, GitHub Actions, and Terraform and checks local tooling where relevant |
| Database configuration | Detects supported databases and looks for common connection/config markers |
| Project hygiene | Git initialized, env-file presence, Node modules, Python venv, and requirements installability |

Output uses [Rich](https://github.com/Textualize/rich) for color-coded results:

- ✅ **Green** — check passed
- ❌ **Red** — check failed + exact fix command
- ⚠️ **Yellow** — warning + suggested command

Final score: **`X/Y relevant checks passed`**

---

## Requirements

- Python 3.10 or newer
- pip

Optional (only when scanning projects that use them):

- Node.js — for Node version and `node_modules` checks
- Docker — when the target project contains a `Dockerfile`
- Git — for the Git initialized check

---

## Usage

```bash
depguard                  # scan current directory
depguard /path/to/project # scan any folder
depguard --version
```

After cloning the repo locally:

```bash
git clone https://github.com/ernestkibz/DepGuard.git
cd DepGuard
pip install -e .
depguard .
```

See [setup.md](setup.md) for Makefile scripts, `requirements-dev.txt`, GitHub Actions, and programmatic use.

### Detection-first behavior

DepGuard does not run every possible check on every repository. It first builds a project context from:

- manifest files such as `pom.xml`, `go.mod`, `.csproj`, `composer.json`, `Cargo.toml`, `Gemfile`, `pyproject.toml`, and `package.json`
- framework and infrastructure markers such as `next.config.js`, `manage.py`, `Dockerfile`, Compose files, `.github/workflows`, and `.tf`
- known code imports and usage patterns across supported languages

That context decides which checks appear in the report.

### Example output

```
╭──────────────────────────────────────────────╮
│ DepGuard                                     │
│ Scanning: C:\projects\my-app                 │
╰──────────────────────────────────────────────╯

✅ Python Version — Python 3.11.8 satisfies required 3.11.0.
✅ Node Version — Node.js 20.11.0 satisfies required 20.0.0.
❌ Requirements Installable — requirements.txt has install issues: ...
   Fix: python -m pip install -r requirements.txt
❌ Node Modules — package.json exists but node_modules is missing.
   Fix: npm install
⚠️ Environment File — .env is missing but .env.example exists.
   Fix: Copy-Item ".env.example" ".env"
✅ Docker Available — No Dockerfile found — Docker not required.
❌ Git Initialized — Git is not initialized in this project folder.
   Fix: git init
⚠️ Virtual Environment — Python project detected but no virtual environment is active.
   Fix: python -m venv .venv && .venv\Scripts\activate

Final score: 4/8 checks passed
```

Exit code is `0` when all relevant checks pass, `1` otherwise.

---

## Screenshots

![DepGuard scanning a real project — pass, fail, and warn checks with fix commands](docs/screenshots/depguard-scan.png)

---

## Project structure

```
DepGuard/
├── depguard.py            # CLI entry point
├── checks/
│   ├── __init__.py        # Check registry and version
│   ├── base.py            # Shared types, OS helpers, fix commands
│   ├── detection.py       # Project context, tech detection, dependency sensing
│   ├── runtime_versions.py
│   ├── dependency_alignment.py
│   ├── frameworks.py
│   ├── infrastructure.py
│   ├── databases.py
│   └── ...                # Python/Node env and project hygiene checks
├── pyproject.toml         # Package metadata and depguard console script
├── setup.md               # Install from GitHub, CI, project integration
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Architecture

```text
depguard.py
    └── checks.detect_project(project) -> ProjectContext
            ├── detected languages / frameworks / infrastructure / databases
            ├── declared dependencies from manifests
            └── inferred dependencies from source imports
    └── checks.ALL_CHECKS
            └── check_*(context: ProjectContext) -> CheckResult | None
```

Design principles:

- **Registry pattern** — add a check function and register it in `ALL_CHECKS`
- **Context-driven checks** — each check receives a `ProjectContext` and skips itself when not relevant
- **Dependency sensing** — known frameworks and services can be inferred from code, not just declarations
- **Centralized platform logic** — fix commands live in `checks/base.py` so every check stays consistent across OSes
- **Graceful degradation** — missing config files pass with an informational message
- **UTF-8 everywhere** — Windows console is reconfigured on startup; file reads try multiple encodings

---

## Extending

Add a new check in `checks/`:

```python
from checks.base import CheckResult, Status
from checks.detection import ProjectContext

def check_my_thing(context: ProjectContext) -> CheckResult | None:
    return CheckResult(
        name="My Check",
        status=Status.PASS,
        message="Everything looks good.",
    )
```

Register it in `checks/__init__.py` inside `ALL_CHECKS`.

---

## Integrations

- [DepGuard for Slack](https://github.com/ernestkibz/depguard-slack) — `/depguard` slash command in Slack; setup in [depguard-slack/setup.md](https://github.com/ernestkibz/depguard-slack/blob/main/setup.md)
- Local workspace copy: `depguard-slack/` (separate `.git`, ignored by this repo)

---

## Handoff for next AI / developer

Read **[setup.md](setup.md)** for full context. Summary:

- **This repo** = CLI only (`depguard.py`, `checks/`, `pyproject.toml`)
- **Do not** commit Slack bot code here — use [depguard-slack](https://github.com/ernestkibz/depguard-slack)
- **Install tag:** `@v1.1.0`
- **Extend checks:** add module in `checks/`, register in `checks/__init__.py` → `ALL_CHECKS`, and update `checks/detection.py` if the check depends on detected tech
- **Slack integration:** `depguard-slack` can consume the richer check set once its dependency is bumped to this release
- Stress tests were removed intentionally; keep this repo production-focused

---

## License

MIT — see [LICENSE](LICENSE).
