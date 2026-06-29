# DepGuard Setup Guide

Install and run [DepGuard](https://github.com/ernestkibz/DepGuard) on any machine (Windows, macOS, Linux) and wire it into your own projects.

---

## Quick start (install from GitHub)

No clone required — install directly with pip:

```bash
pip install "git+https://github.com/ernestkibz/DepGuard.git"
```

Then scan any project folder:

```bash
depguard
depguard /path/to/your/project
```

Pin a specific release tag when you need a stable version:

```bash
pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.0.0"
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

Run: `make setup-check`

### Add to `package.json` scripts

```json
{
  "scripts": {
    "setup-check": "depguard ."
  }
}
```

Run: `npm run setup-check` (DepGuard must be installed in the environment that runs the script.)

### Pin DepGuard as a dev dependency

Add to `requirements-dev.txt`:

```text
git+https://github.com/ernestkibz/DepGuard.git@v1.0.0
```

Install with your other dev tools:

```bash
pip install -r requirements-dev.txt
```

Or in `pyproject.toml` (optional dev group):

```toml
[project.optional-dependencies]
dev = ["depguard @ git+https://github.com/ernestkibz/DepGuard.git@v1.0.0"]
```

```bash
pip install -e ".[dev]"
depguard .
```

---

## CI integration (GitHub Actions)

Add a workflow so every push runs DepGuard on your repo:

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

      - name: Install DepGuard
        run: pip install "git+https://github.com/ernestkibz/DepGuard.git"

      - name: Run setup checks
        run: depguard .
```

Use `continue-on-error: true` on the run step if you only want warnings in CI while rolling out.

---

## Call DepGuard from Python

Use the check engine inside your own scripts, onboarding tools, or tests:

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

if passed < len(results):
    raise SystemExit(1)
```

Import individual checks if you only need one:

```python
from pathlib import Path
from checks import check_requirements, check_env_file

project = Path(".")
print(check_requirements(project))
print(check_env_file(project))
```

---

## Requirements on the machine running DepGuard

| Tool | Required? | When |
|------|-----------|------|
| Python 3.10+ | Yes | Always |
| pip | Yes | Always |
| Node.js | No | Only if the scanned project has `package.json` / `.nvmrc` |
| Docker | No | Only if the scanned project has a `Dockerfile` |
| Git | No | Only for the Git initialized check on the target project |

DepGuard itself has one runtime dependency: [Rich](https://github.com/Textualize/rich).

---

## Troubleshooting

**`depguard` command not found**

Install with `pip install -e .` or ensure the venv where you installed DepGuard is activated.

**Windows encoding / emoji issues**

DepGuard reconfigures stdout to UTF-8 on Windows automatically. Use PowerShell or Windows Terminal for best results.

**pip install from GitHub fails**

- Ensure Git is installed (`git` on PATH) — pip uses it to clone the repo.
- Or clone manually and run `pip install -e .` from the `DepGuard` folder.

**Checks fail on a healthy project**

Some checks depend on your local environment (active venv, Docker daemon, Node version). Read the fix command printed under each failed check — they are tailored to your OS.

---

## Links

- Repository: [github.com/ernestkibz/DepGuard](https://github.com/ernestkibz/DepGuard)
- Full feature overview: [README.md](README.md)
- License: [MIT](LICENSE)
