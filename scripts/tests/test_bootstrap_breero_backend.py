from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "bootstrap_breero_backend.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_breero_backend", MODULE_PATH)
assert SPEC and SPEC.loader
bootstrap = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bootstrap
SPEC.loader.exec_module(bootstrap)


class ExecutionContextTests(unittest.TestCase):
    def test_expected_clean_branch_allows_apply(self) -> None:
        bootstrap.validate_execution_context(
            branch=bootstrap.EXPECTED_BRANCH,
            dirty=[],
            apply=True,
            allow_other_branch=False,
        )

    def test_dirty_dry_run_is_allowed_and_reportable(self) -> None:
        bootstrap.validate_execution_context(
            branch=bootstrap.EXPECTED_BRANCH,
            dirty=[" M README.md"],
            apply=False,
            allow_other_branch=False,
        )

    def test_dirty_apply_is_rejected(self) -> None:
        with self.assertRaisesRegex(bootstrap.BootstrapError, "clean worktree"):
            bootstrap.validate_execution_context(
                branch=bootstrap.EXPECTED_BRANCH,
                dirty=[" M README.md"],
                apply=True,
                allow_other_branch=False,
            )

    def test_protected_branch_apply_is_rejected_even_with_override(self) -> None:
        for branch in ("main", "master", "release/2026-08", "production/hotfix"):
            with self.subTest(branch=branch):
                with self.assertRaisesRegex(bootstrap.BootstrapError, "forbidden"):
                    bootstrap.validate_execution_context(
                        branch=branch,
                        dirty=[],
                        apply=True,
                        allow_other_branch=True,
                    )

    def test_other_branch_requires_explicit_override(self) -> None:
        with self.assertRaisesRegex(bootstrap.BootstrapError, "Expected branch"):
            bootstrap.validate_execution_context(
                branch="feature/example",
                dirty=[],
                apply=False,
                allow_other_branch=False,
            )

        bootstrap.validate_execution_context(
            branch="feature/example",
            dirty=[],
            apply=False,
            allow_other_branch=True,
        )

    def test_detached_head_is_rejected(self) -> None:
        with self.assertRaisesRegex(bootstrap.BootstrapError, "Detached HEAD"):
            bootstrap.validate_execution_context(
                branch="",
                dirty=[],
                apply=False,
                allow_other_branch=True,
            )


class FileSafetyTests(unittest.TestCase):
    def test_safe_relative_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(bootstrap.BootstrapError, "escaped"):
                bootstrap.safe_relative(root, Path("../outside.txt"))

    def test_write_if_missing_is_idempotent_for_identical_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.txt"
            self.assertTrue(bootstrap.write_if_missing(path, "expected\n"))
            self.assertFalse(bootstrap.write_if_missing(path, "expected\n"))

    def test_write_if_missing_rejects_non_identical_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.txt"
            path.write_text("existing\n", encoding="utf-8")
            with self.assertRaisesRegex(bootstrap.BootstrapError, "Refusing to overwrite"):
                bootstrap.write_if_missing(path, "different\n")

    def test_apply_plan_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            actions = bootstrap.plan_actions(root)
            self.assertTrue(actions)
            bootstrap.apply_actions(root, actions)
            self.assertEqual(bootstrap.plan_actions(root), [])


class RepositoryScopeTests(unittest.TestCase):
    def _create_repo(self, remote: str, readme: str = "# BREERO\n") -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "apps" / "api").mkdir(parents=True)
        (root / "README.md").write_text(readme, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=root, check=True)
        return root

    def test_verified_breero_repository_is_accepted(self) -> None:
        root = self._create_repo("https://github.com/appolon1908-hue/Breero.com.git")
        bootstrap.verify_breero_scope(root)

    def test_cross_project_remote_is_rejected(self) -> None:
        cross_project = "https://github.com/example/" + "Money" + "bee-Backend.git"
        root = self._create_repo(cross_project)
        with self.assertRaisesRegex(bootstrap.BootstrapError, "Cross-project"):
            bootstrap.verify_breero_scope(root)

    def test_missing_monorepo_structure_is_rejected(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        with self.assertRaisesRegex(bootstrap.BootstrapError, "expected BREERO"):
            bootstrap.verify_breero_scope(root)


if __name__ == "__main__":
    unittest.main()
