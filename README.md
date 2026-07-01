# DepGuard

DepGuard is a Python CLI that scans a local project folder, detects what stack is actually present, and runs only the setup checks that make sense for that project.

Repository: https://github.com/ernestkibz/DepGuard

Slack integration (separate repo): https://github.com/ernestkibz/depguard-slack

---

## What DepGuard does

DepGuard:

- scans any local project folder
- detects languages, frameworks, infrastructure, and database signals
- runs only the relevant setup rules for that project
- prints exact fix commands and situation-aware suggestions when something is missing or incompatible

Supported detection includes:

- **Languages:** Python, Node.js, Java, Go, .NET, PHP, Rust, Ruby
- **Frameworks:** React, Next.js, Django, Flask, FastAPI, Spring Boot, ASP.NET, Laravel, Ruby on Rails
- **Infrastructure:** Docker, Docker Compose, Kubernetes, GitHub Actions, Terraform
- **Databases:** PostgreSQL, MySQL, MongoDB, Redis, Oracle Database

---

## Quick start

Install from GitHub:

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

---

## Command usage

```bash
depguard
depguard /path/to/project
depguard --version
```

---

## How to read the results

- **PASS** — DepGuard found enough evidence that the check is satisfied.
- **FAIL** — a concrete setup problem: a missing tool, wrong version, or unmet requirement.
- **WARN** — a signal worth reviewing, not always proof of a production problem.

Hard failures are worded directly, for example:

- `Node.js is not installed, but 20.0.0 is required.`
- `Java 17.0.1 does not satisfy required 21.0.0.`

Softer findings use cautious language, for example:

- code-level signals suggest a dependency may be used but is not declared
- DepGuard could not confirm common connection markers for a database

Each failing or warning check includes:

- **Suggestion** — what to investigate or do next in plain language
- **Fix** — a copy-paste command when one is available

### Grey-area warnings

Some checks infer from manifests and source code rather than proving runtime behavior:

- **Dependency Alignment** — imports may come from tests, examples, or optional adapters
- **Framework Configuration** — markers may be missing in monorepos or custom layouts
- **Database Configuration** — package or code signals do not automatically prove production database usage

Read WARN items as “review this,” not “confirmed broken.”

---

## Example output

```text
[PASS] Python Version — Python 3.11.8 satisfies required 3.11.0.
[FAIL] Node Modules — package.json exists but node_modules is missing.
       Suggestion: Run the repository's package manager from the project root, let it restore dependencies from the lockfile, and then rerun the app build or tests.
       Fix: npm install
[WARN] Database Configuration — DepGuard found database-related dependencies or code signals, but could not confirm common connection markers for: Oracle Database.
       Suggestion: Verify the real runtime database from environment variables, secrets management, deployment config, or connection factory code before treating this as a confirmed production dependency.

Final score: 2/3 checks passed
```

Exit code is `0` when all relevant checks pass and `1` when any relevant check fails or warns.

---

## Screenshot

![DepGuard scan output](docs/screenshots/depguard-scan.png)

---

## More setup options

For CI integration, Python API usage, machine requirements, and safe warning interpretation, see [setup.md](setup.md).

For Slack-based scanning of public GitHub repos, see [depguard-slack](https://github.com/ernestkibz/depguard-slack).

---

## License

MIT — see [LICENSE](LICENSE).
