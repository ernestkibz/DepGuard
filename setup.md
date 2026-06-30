# DepGuard Setup Guide

Install and run [DepGuard](https://github.com/ernestkibz/DepGuard) on any machine (Windows, macOS, Linux) and wire it into your own projects.

---

## Two separate Git repositories

DepGuard and DepGuard for Slack are **different repos**. Do not merge them.

| Project | GitHub | Purpose |
|---------|--------|---------|
| **DepGuard** (this repo) | [github.com/ernestkibz/DepGuard](https://github.com/ernestkibz/DepGuard) | CLI — scan local folders, 8 checks, Rich output |
| **DepGuard for Slack** | [github.com/ernestkibz/depguard-slack](https://github.com/ernestkibz/depguard-slack) | Slack bot + MCP server — scan public GitHub repos from Slack |

- **Current release tag:** `v1.0.1` (entry point is `depguard.py`, not `doctor.py`)
- **Local workspace note:** You may have `depguard-slack/` as a sibling folder for convenience. It is listed in this repo's `.gitignore` and has its **own** `.git` — commit Slack work only in the depguard-slack repo.

Slack setup, Railway deployment, and MCP integration: see [depguard-slack/setup.md](https://github.com/ernestkibz/depguard-slack/blob/main/setup.md) (or `depguard-slack/setup.md` locally).

---

## Quick start (install from GitHub)

No clone required — install directly with pip:

```bash
pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.0.1"
```

Then scan any project folder:

```bash
depguard
depguard /path/to/your/project
```

---

## Install from a clone

```bash
git clone https://github.com/ernestkibz/DepGuard.git
cd DepGuard
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows (PowerShell)
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install DepGuard:

```bash
# Recommended — adds the depguard command to your PATH (inside the venv)
pip install -e .

# Minimal — run without installing the command
pip install -r requirements.txt
python depguard.py
```

Verify:

```bash
depguard --version
# DepGuard 1.0.1
```

---

## Use DepGuard in your project

DepGuard scans **any** folder you point it at. You do not need to copy DepGuard into your repo — install it once, then run it against your project path.

### Scan your project from the terminal

```bash
cd /path/to/your/app
depguard .
```

Or from anywhere:

```bash
depguard /path/to/your/app
```

Exit code `0` means all 8 checks passed; `1` means at least one failed or warned.

### Add to your project's `Makefile`

```makefile
.PHONY: setup-check
setup-check:
	depguard .
```

### Add to `package.json` scripts

```json
{
  "scripts": {
    "setup-check": "depguard ."
  }
}
```

### Pin DepGuard as a dev dependency

```text
# requirements-dev.txt
git+https://github.com/ernestkibz/DepGuard.git@v1.0.1
```

Or in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["depguard @ git+https://github.com/ernestkibz/DepGuard.git@v1.0.1"]
```

---

## CI integration (GitHub Actions)

```yaml
# .github/workflows/depguard.yml
name: DepGuard

on:
  push:
    branches: [main]
  pull_request:

jobs:
  setup-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.0.1"
      - run: depguard .
```

---

## Call DepGuard from Python

```python
from pathlib import Path
from depguard import run_checks, score_results

project = Path(".").resolve()
results = run_checks(project)
passed = score_results(results)

for result in results:
    print(f"{result.name}: {result.status.value} — {result.message}")
    if result.fix_command:
        print(f"  Fix: {result.fix_command}")
```

Import individual checks:

```python
from pathlib import Path
from checks.requirements import check_requirements
from checks.env_file import check_env_file

print(check_requirements(Path(".")))
```

The Slack bot imports the same engine via `pip install depguard @ git+...@v1.0.1` in its own repo.

---

## Requirements on the machine running DepGuard

| Tool | Required? | When |
|------|-----------|------|
| Python 3.10+ | Yes | Always |
| pip | Yes | Always |
| Node.js | No | Only if the scanned project has `package.json` / `.nvmrc` |
| Docker | No | Only if the scanned project has a `Dockerfile` |
| Git | No | Only for the Git initialized check on the target project |

Runtime dependency: [Rich](https://github.com/Textualize/rich) only.

---

## Troubleshooting

**`depguard` command not found** — Run `pip install -e .` and activate your venv.

**Windows encoding** — DepGuard reconfigures stdout to UTF-8 on Windows. Use PowerShell or Windows Terminal.

**pip install from GitHub fails** — Ensure `git` is on PATH, or clone and `pip install -e .` locally.

**Checks fail on a healthy project** — Some checks depend on your local environment (venv, Docker, Node). Read the printed fix commands.

---

## Handoff notes for the next developer / AI

### What this repo is

Cross-platform Python CLI. Entry point: `depguard.py`. Package name: `depguard`. Version in `checks/__init__.py` and `pyproject.toml`.

### What was built (history)

1. Eight modular checks in `checks/` with registry in `checks/__init__.py`
2. Cross-platform fix commands centralized in `checks/base.py`
3. Renamed from `doctor.py` → `depguard.py` at v1.0.1
4. Packaging via `pyproject.toml` with console script `depguard`
5. Screenshot at `docs/screenshots/depguard-scan.png`
6. Stress tests removed — production CLI only
7. Slack integration lives in **separate repo** — do not add Slack code here

### What not to do

- Do not commit `depguard-slack/` into this repo (it is gitignored)
- Do not use tag `v1.0.0` for installs — use `v1.0.1` (has `depguard.py`)
- Do not re-add stress test fixtures to this repo unless explicitly requested

### Related repo

All Slack, MCP, Railway, and `/depguard` slash command work → [depguard-slack](https://github.com/ernestkibz/depguard-slack)

---

## Links

- Repository: [github.com/ernestkibz/DepGuard](https://github.com/ernestkibz/DepGuard)
- Slack integration: [github.com/ernestkibz/depguard-slack](https://github.com/ernestkibz/depguard-slack)
- Full overview: [README.md](README.md)
- License: [MIT](LICENSE)
