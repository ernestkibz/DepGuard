from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import depguard
from checks import CheckResult, Status
from checks.databases import check_database_configuration
from checks.dependency_alignment import check_dependency_alignment
from checks.detection import detect_project
from checks.frameworks import check_framework_configuration
from checks.node_version import check_node_version
from checks.runtime_versions import check_rust_version


class DetectionTests(unittest.TestCase):
    def make_project(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory()

    def write(self, root: Path, relative_path: str, content: str) -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_detects_nextjs_from_manifest_and_markers(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(
                root,
                "package.json",
                '{"dependencies": {"next": "14.2.0", "react": "18.2.0"}}',
            )
            self.write(root, "next.config.js", "module.exports = {};")
            self.write(root, "app/page.tsx", "import React from 'react';")

            context = detect_project(root)

            self.assertIn("node", context.languages)
            self.assertIn("Next.js", context.frameworks)
            self.assertIn("React", context.frameworks)

    def test_dependency_alignment_warns_for_missing_fastapi(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "pyproject.toml", '[project]\nname = "demo"\nversion = "0.1.0"\n')
            self.write(root, "app.py", "from fastapi import FastAPI\napp = FastAPI()\n")

            context = detect_project(root)
            result = check_dependency_alignment(context)

            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.status, Status.WARN)
            self.assertIn("fastapi", result.message.lower())

    def test_detects_postgres_from_go_mod_and_env(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "go.mod", "module demo\n\ngo 1.22\n\nrequire github.com/jackc/pgx/v5 v5.7.0\n")
            self.write(root, "main.go", 'package main\nimport "github.com/jackc/pgx/v5"\n')
            self.write(root, ".env.example", "DATABASE_URL=postgresql://localhost:5432/app\n")

            context = detect_project(root)

            self.assertIn("go", context.languages)
            self.assertIn("PostgreSQL", context.databases)

    def test_ambiguity_messages_use_careful_language(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "package.json", '{"dependencies": {"next": "14.2.0"}}')
            self.write(root, "src/index.ts", "import oracledb from 'oracledb';\nimport next from 'next';\n")

            context = detect_project(root)

            dep_result = check_dependency_alignment(context)
            framework_result = check_framework_configuration(context)
            database_result = check_database_configuration(context)

            self.assertIsNotNone(dep_result)
            self.assertIsNotNone(framework_result)
            self.assertIsNotNone(database_result)
            assert dep_result is not None
            assert framework_result is not None
            assert database_result is not None
            self.assertIn("may be used", dep_result.message)
            self.assertIsNotNone(dep_result.suggestion)
            self.assertIn("custom layouts", framework_result.message)
            self.assertIsNotNone(framework_result.suggestion)
            self.assertIn("could not confirm common connection markers", database_result.message)
            self.assertIsNotNone(database_result.suggestion)

    def test_rust_nightly_channel_does_not_become_zero_version(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "Cargo.toml", '[package]\nname = "demo"\nversion = "0.1.0"\n')
            self.write(root, "rust-toolchain.toml", '[toolchain]\nchannel = "nightly"\n')
            self.write(root, "src/main.rs", "fn main() {}\n")

            context = detect_project(root)
            result = check_rust_version(context)

            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.status, Status.PASS)
            self.assertIn("No Rust toolchain constraint found", result.message)

    def test_version_failures_include_suggestion_text(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(
                root,
                "package.json",
                '{\n  "name": "demo",\n  "engines": {"node": ">=99.0.0"}\n}\n',
            )
            self.write(root, "src/index.js", "console.log('hi')\n")

            context = detect_project(root)
            result = check_node_version(context)

            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.status, Status.FAIL)
            self.assertIsNotNone(result.suggestion)
            self.assertIn("Switch this project to Node.js", result.suggestion)

    def test_run_checks_uses_project_context_and_skips_none_results(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "composer.json", '{"require": {"php": "^8.2"}}')

            def summarize_languages(context):
                return CheckResult(
                    name="Context Summary",
                    status=Status.PASS,
                    message=",".join(sorted(context.languages)),
                )

            with patch.object(
                depguard,
                "ALL_CHECKS",
                [("Context Summary", summarize_languages), ("Skipped", lambda context: None)],
            ):
                results = depguard.run_checks(root)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "Context Summary")
            self.assertEqual(results[0].message, "php")

    def test_polyglot_python_and_node_detects_both_stacks(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(
                root,
                "pyproject.toml",
                '[project]\nname = "fullstack"\nrequires-python = ">=3.11"\n',
            )
            self.write(root, "requirements.txt", "django>=5.0\n")
            self.write(root, "app.py", "import django\n")
            self.write(
                root,
                "package.json",
                '{"name": "web", "dependencies": {"next": "14.2.0", "react": "18.2.0"}}',
            )
            self.write(root, "next.config.js", "module.exports = {};")
            self.write(root, "pages/index.tsx", "import React from 'react';\n")

            context = detect_project(root)

            self.assertIn("python", context.languages)
            self.assertIn("node", context.languages)
            self.assertIn("Next.js", context.frameworks)
            self.assertIn("Django", context.frameworks)

            from checks.python_version import check_python_version
            from checks.node_version import check_node_version
            from checks.node_modules import check_node_modules
            from checks.requirements import check_requirements

            self.assertIsNotNone(check_python_version(context))
            self.assertIsNotNone(check_node_version(context))
            self.assertIsNotNone(check_node_modules(context))
            self.assertIsNotNone(check_requirements(context))

    def test_detects_html_static_site(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "index.html", "<!DOCTYPE html><html><body>Hi</body></html>\n")
            self.write(root, "setup.html", "<html><body>Setup</body></html>\n")
            self.write(root, "data/items.json", "{}\n")

            context = detect_project(root)
            self.assertIn("html", context.languages)

            from checks.web_frontend import check_html_content

            result = check_html_content(context)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.status, Status.PASS)
            self.assertIn("HTML content detected", result.message)

    def test_typescript_without_tsconfig_warns(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "src/app.ts", "export const app = 1;\n")

            context = detect_project(root)
            self.assertIn("typescript", context.languages)

            from checks.web_frontend import check_typescript_configuration

            result = check_typescript_configuration(context)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.status, Status.WARN)

    def test_nested_git_repo_is_ignored_during_detection(self) -> None:
        with self.make_project() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "pyproject.toml", '[project]\nname = "depguard"\nversion = "0.1.0"\n')
            self.write(root, "checks/base.py", "from pathlib import Path\n")
            (root / "embedded-bot" / ".git").mkdir(parents=True, exist_ok=True)
            self.write(root, "embedded-bot/slack_bot.py", "from flask import Flask\napp = Flask(__name__)\n")
            self.write(root, "embedded-bot/requirements.txt", "flask\n")

            context = detect_project(root)

            self.assertIn("python", context.languages)
            self.assertNotIn("Flask", context.frameworks)


if __name__ == "__main__":
    unittest.main()
