import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sync_skills as sync


ROOT = Path(__file__).resolve().parents[1]


class SyncSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)

    def run_cli(self, *args, env=None):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "sync_skills.py"), *args],
            cwd=self.project, capture_output=True, text=True, env=env,
        )

    def test_profiles_are_curated_and_can_be_combined(self):
        def names(*args):
            result = self.run_cli("--list", *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            return {line.split()[0] for line in result.stdout.splitlines()
                    if line and not line[0].isspace()}

        starter = names()
        research = names("--profile", "research")
        full = names("--profile", "full")
        self.assertLess(len(starter), 25)
        self.assertIn("test-driven-development", starter)
        self.assertNotIn("academic-pipeline", starter)
        self.assertIn("literature-search", research)
        self.assertEqual(names("--profile", "starter,research"), starter | research)
        self.assertLessEqual(starter | research, full)
        self.assertEqual(len(full), 73)

    def test_only_installs_exact_choices_and_supporting_files(self):
        result = self.run_cli(
            "--scope", "project", "--targets", "claude-code", "--mode", "copy",
            "--only", "webapp-testing,pdf", "--exclude", "pdf",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        base = self.project / ".claude/skills"
        self.assertEqual({p.name for p in base.iterdir()}, {"webapp-testing", sync.MANIFEST})
        self.assertTrue((base / "webapp-testing/SKILL.md").is_file())
        self.assertTrue((base / "webapp-testing/scripts/with_server.py").is_file())
        self.assertFalse((base / "webapp-testing").is_symlink())

    def test_custom_claude_config_directory_and_symlinks(self):
        config = self.project / "claude-config"
        result = self.run_cli(
            "--targets", "claude", "--only", "test-driven-development",
            env={**os.environ, "CLAUDE_CONFIG_DIR": str(config)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        skill = config / "skills/test-driven-development"
        self.assertTrue(skill.is_symlink())
        self.assertEqual(skill.resolve(), ROOT / "agent-skills/skills/test-driven-development")
        self.assertTrue((skill.resolve() / "../../references/testing-patterns.md").is_file())

    def test_claude_config_override_does_not_change_project_scope(self):
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.project / "custom")}):
            self.assertEqual(
                sync.target_dir(self.project, sync.TARGETS["claude"], "project"),
                self.project / ".claude/skills",
            )

    def test_dry_run_does_not_create_directories(self):
        result = self.run_cli("--scope", "project", "--targets", "claude",
                              "--only", "pdf", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would link", result.stdout)
        self.assertFalse((self.project / ".claude").exists())

    def test_invalid_selection_fails_before_writing(self):
        for selection in [("--only", "missing-skill"), ("--profile", "unknown"),
                          ("--only", "pdf", "--all-skills"), ("--only", ",")]:
            with self.subTest(selection=selection):
                result = self.run_cli("--scope", "project", "--targets", "claude", *selection)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse((self.project / ".claude").exists())

    def test_skipped_personal_skill_is_never_adopted_or_pruned(self):
        skill = sync.Skill("personal", self.project / "upstream", "upstream")
        skill.source.mkdir()
        (skill.source / "SKILL.md").write_text("upstream")
        for symlink in (False, True):
            with self.subTest(symlink=symlink), contextlib.redirect_stdout(io.StringIO()):
                base = self.project / str(symlink)
                base.mkdir()
                personal = base / "personal"
                if symlink:
                    personal.symlink_to(skill.source, target_is_directory=True)
                else:
                    personal.mkdir()
                    (personal / "SKILL.md").write_text("my own skill")
                sync.sync_target([skill], sync.TARGETS["claude"], base, "copy", False, True, False)
                manifest = json.loads((base / sync.MANIFEST).read_text())
                self.assertNotIn("personal", manifest["skills"])
                sync.sync_target([], sync.TARGETS["claude"], base, "copy", False, True, False)
                self.assertTrue(personal.exists())
                self.assertEqual(personal.is_symlink(), symlink)

    def test_no_prune_retains_tracking_for_later_cleanup(self):
        def run(*extra):
            result = self.run_cli("--scope", "project", "--targets", "claude", *extra)
            self.assertEqual(result.returncode, 0, result.stderr)

        run("--only", "pdf")
        run("--only", "xlsx", "--no-prune")
        base = self.project / ".claude/skills"
        self.assertEqual(set(json.loads((base / sync.MANIFEST).read_text())["skills"]), {"pdf", "xlsx"})
        run("--only", "xlsx")
        self.assertFalse((base / "pdf").exists())
        self.assertTrue((base / "xlsx/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
