from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import depguard
from checks import CheckResult, Status
from checks.dependency_alignment import check_dependency_alignment
from checks.detection import detect_project


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
