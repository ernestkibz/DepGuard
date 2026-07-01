# DepGuard Setup Guide

Install and use DepGuard on your machine or in CI.

Overview: [README.md](README.md)

---

## Install from GitHub

```bash
pip install "git+https://github.com/ernestkibz/DepGuard.git@v1.1.0"
depguard /path/to/project
```

---

## Install from a clone

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

---

## Run a scan

```bash
depguard
depguard .
depguard /path/to/project
```

---

## Add DepGuard to CI

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

---

## Add DepGuard to a project workflow

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

---

## Call it from Python

```python
from pathlib import Path
from depguard import run_checks, score_results

project = Path('.').resolve()
results = run_checks(project)
passed = score_results(results)

print(f"Passed: {passed}/{len(results)}")
for result in results:
    print(result.name, result.status.value, result.message)
    if result.suggestion:
        print("  Suggestion:", result.suggestion)
    if result.fix_command:
        print("  Fix:", result.fix_command)
```

---

## Machine requirements

**Required:**

- Python 3.10+
- pip

**Optional** (only when scanning matching projects):

- Node.js, Java, Go, .NET SDK, PHP, Rust, Ruby
- Docker, kubectl, Terraform, Git

DepGuard skips checks that do not apply to the detected stack.

---

## Interpreting results safely

| Status | Meaning |
|--------|---------|
| **FAIL** | Concrete issue or unmet requirement — act on this |
| **WARN** | Signal-based finding — review before treating as confirmed |
| **PASS** | Enough evidence that the check is satisfied |

**Suggestion** explains the safest next step. **Fix** is the copy-paste command when one exists.

Database and dependency warnings can come from tests, examples, adapters, or environment-managed config. That wording is deliberate so teams do not overstate ambiguous findings.

---

## Links

- Core repo: https://github.com/ernestkibz/DepGuard
- Slack integration: https://github.com/ernestkibz/depguard-slack
