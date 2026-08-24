#!/usr/bin/env python3
"""Safely bootstrap missing BREERO backend production-foundation boundaries.

This script is intentionally conservative:

- It operates only on a BREERO repository checkout.
- It is dry-run by default.
- It never overwrites an existing file unless the existing content is identical.
- It does not create database migrations automatically.
- It does not enable production capabilities, providers, payments, payouts,
  external sends, matching, messaging, or automation.
- It extends the existing ``apps/api`` backend instead of rebuilding it.

Typical use:

    python scripts/bootstrap_breero_backend.py
    python scripts/bootstrap_breero_backend.py --apply

The expected implementation branch is:

    bootstrap/backend-production-foundation
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXPECTED_BRANCH = "bootstrap/backend-production-foundation"
BACKEND_ROOT = Path("apps/api")
APP_ROOT = BACKEND_ROOT / "app"
TEST_ROOT = BACKEND_ROOT / "tests"

# These are structural package boundaries only. Domain behavior belongs in
# independently reviewable implementation PRs.
PACKAGE_DIRS: tuple[Path, ...] = (
    APP_ROOT / "api" / "v2",
    APP_ROOT / "application",
    APP_ROOT / "core",
    APP_ROOT / "domains" / "identity",
    APP_ROOT / "domains" / "tenancy",
    APP_ROOT / "domains" / "requests",
    APP_ROOT / "domains" / "marketplace",
    APP_ROOT / "domains" / "providers",
    APP_ROOT / "domains" / "quotes",
    APP_ROOT / "domains" / "bookings",
    APP_ROOT / "domains" / "jobs",
    APP_ROOT / "domains" / "documents",
    APP_ROOT / "domains" / "geo",
    APP_ROOT / "domains" / "operations",
    APP_ROOT / "domains" / "authorization",
    APP_ROOT / "domains" / "capabilities",
    APP_ROOT / "domains" / "integrations",
    APP_ROOT / "integrations" / "codestra",
    APP_ROOT / "integrations" / "odoo",
    APP_ROOT / "integrations" / "klyrow",
    APP_ROOT / "integrations" / "telnexa",
    APP_ROOT / "integrations" / "n8n",
    APP_ROOT / "workers",
    APP_ROOT / "observability",
)

TEST_DIRS: tuple[Path, ...] = (
    TEST_ROOT / "unit",
    TEST_ROOT / "integration",
    TEST_ROOT / "security",
    TEST_ROOT / "concurrency",
    TEST_ROOT / "postgres",
    TEST_ROOT / "postgis",
)

PACKAGE_MARKERS: tuple[Path, ...] = tuple(
    directory / "__init__.py" for directory in PACKAGE_DIRS
)

README_FILES: dict[Path, str] = {
    APP_ROOT / "domains" / "README.md": """# BREERO backend domains

Domain packages own business rules, policies, state machines, commands,
repositories, queries, events, and domain errors.

Transport code must remain thin. External provider calls must not occur inside
authoritative PostgreSQL transactions. Production-sensitive mutations must
follow the shared authentication, authorization, policy, capability,
idempotency/concurrency, audit, and transactional-outbox path.
""",
    APP_ROOT / "integrations" / "README.md": """# BREERO backend integrations

Provider-specific code belongs behind provider-neutral interfaces.

Outbound work:
domain command -> transactional outbox -> worker -> adapter -> provider.

Inbound work:
verified callback -> durable inbox -> worker -> translator -> authorized
domain command.

Adapters must not become authoritative for marketplace state.
""",
    TEST_ROOT / "README.md": """# BREERO backend tests

Production-foundation work must include, where applicable:

- unit/domain tests;
- PostgreSQL integration tests;
- PostGIS tests for geographic behavior;
- negative authorization tests;
- idempotency and concurrency tests;
- outbox/inbox/webhook tests;
- migration and OpenAPI drift checks;
- security and fail-closed capability tests.

Do not substitute SQLite for PostgreSQL-specific behavior.
""",
}

BRANCH_PLAN = """BREERO backend branch plan

main
├── bootstrap/backend-production-foundation
├── auth/identity-tenancy
├── domain/request-marketplace
├── domain/provider-network
├── domain/quotes-bookings-jobs
├── integration/outbox-inbox
├── adapters/codestra-odoo-klyrow-telnexa-n8n
├── documents/secure-pipeline
├── geo/postgis-matching
├── operations/recovery
├── observability/postgres-tests
└── release/staging-recovery
"""


@dataclass(frozen=True)
class Action:
    kind: str
    path: Path
    detail: str


class BootstrapError(RuntimeError):
    """Raised when the repository is not safe to bootstrap."""


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BootstrapError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise BootstrapError("No Git repository found from the current directory.")


def verify_breero_scope(root: Path) -> None:
    required = (
        root / "apps",
        root / "apps" / "api",
        root / "README.md",
    )
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]
    if missing:
        raise BootstrapError(
            "This checkout does not have the expected BREERO monorepo structure: "
            + ", ".join(missing)
        )

    readme = (root / "README.md").read_text(encoding="utf-8", errors="ignore")
    remote = run_git("remote", "get-url", "origin")
    identity_text = f"{readme}\n{remote}".lower()

    if "breero" not in identity_text:
        raise BootstrapError(
            "Repository identity check failed: BREERO was not found in README/origin."
        )

    forbidden = "money" + "bee"
    if forbidden in remote.lower():
        raise BootstrapError("Cross-project repository detected; refusing to modify it.")


def current_branch() -> str:
    return run_git("branch", "--show-current")


def ensure_clean_or_report() -> list[str]:
    status = run_git("status", "--porcelain")
    return [line for line in status.splitlines() if line.strip()]


def safe_relative(root: Path, path: Path) -> Path:
    resolved = (root / path).resolve()
    try:
        return resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise BootstrapError(f"Path escaped repository root: {path}") from exc


def plan_actions(root: Path) -> list[Action]:
    actions: list[Action] = []

    for directory in (*PACKAGE_DIRS, *TEST_DIRS):
        relative = safe_relative(root, directory)
        target = root / relative
        if not target.exists():
            actions.append(Action("mkdir", relative, "create directory"))

    for marker in PACKAGE_MARKERS:
        relative = safe_relative(root, marker)
        target = root / relative
        if not target.exists():
            actions.append(Action("write", relative, "create Python package marker"))

    for path, content in README_FILES.items():
        relative = safe_relative(root, path)
        target = root / relative
        if not target.exists():
            actions.append(Action("write", relative, f"create {len(content)}-byte README"))

    plan_file = Path("docs") / "backend" / "BRANCH_PLAN.md"
    relative = safe_relative(root, plan_file)
    target = root / relative
    if not target.exists():
        actions.append(Action("write", relative, "record backend branch sequence"))

    return actions


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="strict")
        if existing == content:
            return False
        raise BootstrapError(
            f"Refusing to overwrite existing non-identical file: {path}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def apply_actions(root: Path, actions: Iterable[Action]) -> None:
    readme_lookup = {
        safe_relative(root, path): content for path, content in README_FILES.items()
    }
    package_markers = {safe_relative(root, path) for path in PACKAGE_MARKERS}
    branch_plan_path = Path("docs") / "backend" / "BRANCH_PLAN.md"

    for action in actions:
        target = root / action.path

        if action.kind == "mkdir":
            target.mkdir(parents=True, exist_ok=True)
            print(f"CREATE_DIR {action.path}")
            continue

        if action.kind != "write":
            raise BootstrapError(f"Unknown action kind: {action.kind}")

        if action.path in package_markers:
            content = (
                '"""BREERO backend package boundary.\n\n'
                "Behavior is added only in the owning reviewed implementation PR.\n"
                '"""\n'
            )
        elif action.path in readme_lookup:
            content = readme_lookup[action.path]
        elif action.path == branch_plan_path:
            content = f"# {BRANCH_PLAN}"
        else:
            raise BootstrapError(f"No content template for {action.path}")

        if write_if_missing(target, content):
            print(f"CREATE_FILE {action.path}")


def print_plan(actions: Iterable[Action]) -> None:
    planned = list(actions)
    if not planned:
        print("BOOTSTRAP_STATUS=NO_CHANGES_REQUIRED")
        return

    print("BOOTSTRAP_STATUS=CHANGES_PLANNED")
    for action in planned:
        print(f"{action.kind.upper()} {action.path} :: {action.detail}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely scaffold missing BREERO backend production-foundation "
            "package boundaries."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write missing files/directories. Default is dry-run.",
    )
    parser.add_argument(
        "--allow-other-branch",
        action="store_true",
        help=(
            "Allow execution outside bootstrap/backend-production-foundation. "
            "This does not relax repository-scope checks."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        root = find_repo_root(Path.cwd())
        # git helpers must run inside the repository root.
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(root)
            verify_breero_scope(root)
            branch = current_branch()
            dirty = ensure_clean_or_report()

            print(f"REPOSITORY_ROOT={root}")
            print(f"BRANCH={branch}")
            print("SCOPE=BREERO_BACKEND_ONLY")
            print("PRODUCTION_ACTIVATION=DISABLED")
            print("EXTERNAL_SENDS=DISABLED")
            print("PAYMENTS=DISABLED")
            print("PAYOUTS=DISABLED")

            if branch != EXPECTED_BRANCH and not args.allow_other_branch:
                raise BootstrapError(
                    f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}. "
                    "Switch branches or use --allow-other-branch deliberately."
                )

            if dirty:
                print("WORKTREE_DIRTY=YES")
                for line in dirty:
                    print(f"WORKTREE_CHANGE={line}")
            else:
                print("WORKTREE_DIRTY=NO")

            actions = plan_actions(root)
            print_plan(actions)

            if not args.apply:
                print("MODE=DRY_RUN")
                print("NEXT_SAFE_ACTION=rerun with --apply after reviewing the plan")
                return 0

            apply_actions(root, actions)
            print("MODE=APPLY")
            print("BOOTSTRAP_APPLIED=YES")
            print(
                "NEXT_SAFE_ACTION=review git diff, run backend CI/tests, "
                "then open or update the draft PR"
            )
            return 0
        finally:
            import os

            os.chdir(original_cwd)
    except BootstrapError as exc:
        print(f"BOOTSTRAP_ERROR={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
