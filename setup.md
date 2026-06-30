# DepGuard Setup Guide

This file is split into two tracks:

- `Setup 1` is for people installing and using DepGuard.
- `Setup 2` is for you as the builder/owner maintaining the engine and its relationship to `depguard-slack`.

Remember: `DepGuard` and `depguard-slack` are separate git repositories.

---

## Setup 1 - Install and Use DepGuard

### Option A: install directly from GitHub

```bash
pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.1.0"
depguard /path/to/project
```

### Option B: install from a clone

```bash
git clone https://github.com/ernestkibz/DepGuard.git
cd DepGuard
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install the package:

```bash
pip install -e .
```

Verify:

```bash
depguard --version
```

### Run a scan

```bash
depguard
depguard .
depguard /path/to/project
```

### Add DepGuard to CI

```yaml
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
      - run: pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.1.0"
      - run: depguard .
```

### Add DepGuard to a project workflow

`Makefile`:

```makefile
.PHONY: setup-check
setup-check:
	depguard .
```

`package.json`:

```json
{
  "scripts": {
    "setup-check": "depguard ."
  }
}
```

### Call it from Python

```python
from pathlib import Path
from depguard import run_checks, score_results

project = Path('.').resolve()
results = run_checks(project)
passed = score_results(results)

print(f"Passed: {passed}/{len(results)}")
for result in results:
    print(result.name, result.status.value, result.message)
```

### Machine requirements

Required:

- Python 3.10+
- pip

Optional and only needed when scanning matching projects:

- Node.js
- Java
- Go
- .NET SDK
- PHP
- Rust
- Ruby
- Docker
- kubectl
- Terraform
- Git

### Interpreting warnings safely

Use these reading rules with teams:

- `FAIL` means a concrete issue or unmet requirement was found.
- `WARN` means review is needed, not automatic proof of production usage.
- Database and dependency warnings are often signal-based and can come from tests, examples, adapters, or environment-managed config.
- Suggestions explain the safest next investigation step, while fix commands remain the copy-paste action when one is available.

That wording is deliberate so teams do not overstate ambiguous findings.

---

## Setup 2 - Builder/Owner Workflow

### Repo boundary

There are two repos in this system:

- `DepGuard` - core engine and CLI
- `depguard-slack` - Slack and MCP wrapper around the core engine

Do not mix their git histories. A local workspace can contain both repos side by side, but commits must stay in the correct repo.

### Core architecture

```text
depguard.py
  -> detect_project(project)
  -> ProjectContext
  -> ALL_CHECKS
  -> CheckResult objects
  -> Rich CLI rendering
```

Important implementation points:

- `checks/detection.py` builds `ProjectContext`
- source imports are used alongside manifest files for dependency sensing
- nested directories containing their own `.git` folders are ignored
- checks return `None` when irrelevant
- OS-specific fix commands live in `checks/base.py`

### Releasing and downstream consumption

The Slack repo pins this repo by git tag in `requirements.txt`. A normal release flow is:

1. Make and test engine changes here.
2. Update version metadata if needed.
3. Tag and push the release.
4. Bump the pinned `depguard` dependency in `depguard-slack`.
5. Redeploy the Slack app when its dependency changes.

### Where the communication upgrade lives

The ambiguity-language upgrade currently centers on:

- `checks/dependency_alignment.py`
- `checks/frameworks.py`
- `checks/databases.py`
- `checks/runtime_versions.py` for the Rust toolchain edge case
- `depguard.py` for the CLI summary note

The goal is to avoid misleading statements such as treating Oracle-related signals as guaranteed Oracle production usage.

### Adding or changing checks

1. Update detection rules if the check depends on stack discovery.
2. Implement the check in `checks/`.
3. Register it in `checks/__init__.py`.
4. Add focused tests under `tests/`.
5. Keep wording calibrated to the evidence level.

### Story so far

- DepGuard started as the standalone project scanner.
- The engine expanded into a detection-driven system with broader stack support.
- Dependency sensing moved beyond manifests into code-import signals.
- Communication was tightened so grey areas are explained carefully.
- `depguard-slack` was then built as a separate Slack/MCP delivery layer for demos and real usage.

### Demo context

Useful demo targets include:

- `DepGuard` itself
- a known public demo repo such as `chaosapp-demo` when available
- any public GitHub repo with visible stack markers for Slack demonstrations

### Troubleshooting for maintainers

- If a warning sounds too certain, check whether the evidence is signal-based instead of configuration-based.
- If Slack behavior needs changes, make them in `depguard-slack`, not here.
- If a downstream demo behaves differently from the CLI, compare the pinned release in the Slack repo against the local core checkout.

### Related repo

Slack app, MCP server, Railway deployment, slash command behavior, and Slack message formatting live in `depguard-slack`:

- https://github.com/ernestkibz/depguard-slack

---

## Links

- Core repo: https://github.com/ernestkibz/DepGuard
- Separate Slack repo: https://github.com/ernestkibz/depguard-slack
- Overview: [README.md](README.md)
