# DepGuard — Planned Upgrades

This document tracks future work that is **out of scope for the current release (v1.1.0)** but worth building next. The core product today focuses on **setup diagnostics and dependency alignment** across detected stacks — not CVE advisory scanning.

Related repos:

- Core engine: https://github.com/ernestkibz/DepGuard
- Slack wrapper: https://github.com/ernestkibz/depguard-slack

---

## Current scope (v1.1.0)

DepGuard already:

- Detects **all stacks present** in a repo (polyglot-safe — Python + Node + Java together, not "Python only")
- Reads each ecosystem's manifest (`requirements.txt`, `package.json`, `pom.xml`, `go.mod`, `composer.json`, `Cargo.toml`, `Gemfile`)
- Runs runtime, install, framework, infrastructure, and database **setup** checks
- Compares source imports to declared dependencies (**Dependency Alignment**)
- Returns suggestions + copy-paste fix commands

DepGuard does **not** yet query OSV, GitHub Advisory Database, or ecosystem audit tools for known CVEs.

---

## Upgrade 1 — Advisory / CVE scanning (v2.0 candidate)

### Goal

Add **optional** known-vulnerability reporting on **declared** dependencies, without replacing setup checks.

Keep reports clearly separated:

```text
[SETUP]  Node Modules — missing
[ALIGN]  Dependency Alignment — import not in package.json
[SEC]    Advisories — 2 moderate (OSV) on declared deps
```

### Why optional

| Concern | Setup checks (today) | Advisory scanning (proposed) |
|---------|----------------------|------------------------------|
| Primary question | Can this repo run? | Are declared deps affected by known CVEs? |
| Network | Mostly local | Requires OSV / registry / audit APIs |
| Speed | Seconds | Slower; rate limits and timeouts |
| Slack UX | Fast slash-command flow | Needs async + clear "security" labeling |
| Noise | Setup signals | Severity disputes, transitive deps, dev-only packages |

### Recommended design

1. **Opt-in flag** — do not run advisories by default  
   - CLI: `depguard --advisories` or `depguard --security`  
   - Slack: separate command or explicit flag (e.g. `/depguard-security`)  
2. **Declared deps only first** — scan manifests, not every inferred import  
3. **Per-ecosystem adapters** (implement in order):

| Ecosystem | Tool / API | Notes |
|-----------|------------|-------|
| Python | `pip-audit` or [OSV API](https://google.osv.dev/) | Lock/requirements pins |
| Node.js | `npm audit --json` or OSV bulk query | Needs `package-lock.json` / `npm-shrinkwrap` for best results |
| Java | OSV Maven coordinates | From `pom.xml` / Gradle lockfiles if present |
| Go | OSV or `govulncheck` | `go.mod` + sum |
| .NET | OSV NuGet | `.csproj` PackageReference |
| PHP | OSV Composer | `composer.lock` preferred |
| Rust | `cargo audit` or OSV | `Cargo.lock` |
| Ruby | OSV RubyGems | `Gemfile.lock` |

4. **New check module** — `checks/advisories.py`  
   - Returns `CheckResult` with `Status.WARN` or dedicated status label in message  
   - Never fail the whole scan solely for moderate advisories unless `--strict-security` added later  
5. **Register in** `checks/__init__.py` behind a feature flag or only when `--advisories` passed  
6. **Network policy** — document that Railway/CI must allow outbound HTTPS to OSV / registries  

### Slack wrapper changes (`depguard-slack`)

- Bump pinned `depguard` after core v2 tag
- Optional second MCP tool: `scan_github_repo_security` **or** pass `include_advisories=true` to existing tool
- Block Kit section header: **Security advisories (OSV)** separate from setup checks
- Longer timeout + user message: "Security scan may take up to 60s"

### Tests

- Mock OSV / audit CLI responses — no live network in unit tests
- Fixture repos with one known vulnerable pinned version (use OSV test cases)

### Docs

- User README: one paragraph — setup vs security, opt-in only  
- Do not claim Snyk/Dependabot parity in marketing copy  

### Release checklist

1. Implement core `--advisories` + tests  
2. Tag `v2.0.0`  
3. Bump `depguard-slack/requirements.txt` pin  
4. Redeploy Railway  
5. Update Devpost / demo only if submitting security track separately  

---

## Upgrade 2 — Per-ecosystem manifest install validation

Today only Python runs `pip install --dry-run` on `requirements.txt`. Future:

| Ecosystem | Possible check |
|-----------|----------------|
| Node | Verify lockfile consistency (`npm ci --dry-run` / `pnpm install --frozen-lockfile`) |
| Java | `mvn -q validate` / Gradle dependency insight when wrapper present |
| Go | `go mod verify` |
| PHP | `composer validate --strict` |
| Rust | `cargo fetch --locked` when `Cargo.lock` exists |
| Ruby | `bundle check` when `Gemfile.lock` exists |

Implement only when the tool is likely available on the scan host (CLI local) or document CI-only behavior.

---

## Upgrade 3 — Monorepo / subdirectory roots

Detect multiple package roots (e.g. `apps/web/package.json`, `services/api/pyproject.toml`) and run context per root or aggregate with path labels.

---

## Upgrade 4 — Private repositories (Slack)

Requires secure GitHub token handling, never logged, scoped read-only — separate design doc before implementation.

---

## What not to do

- Do not fold CVE scanning into default `/depguard` without an opt-in — slows every scan and blurs product positioning  
- Do not treat Dependency Alignment WARN as confirmed CVE exposure  
- Do not commit local submission/hackathon files (`SUBMISSION.md`, `submission/`) into public repos  

---

## Tracking

| Upgrade | Target version | Status |
|---------|----------------|--------|
| Setup + multi-stack alignment | v1.1.0 | **Shipped** |
| Advisory / OSV scanning | v2.0.0 | Planned |
| Manifest install validation (all ecosystems) | v2.x | Planned |
| Monorepo roots | v2.x | Planned |
| Private GitHub repos (Slack) | TBD | Planned |

When starting v2 advisory work, begin with **Python + Node only**, ship behind `--advisories`, then expand ecosystems.
