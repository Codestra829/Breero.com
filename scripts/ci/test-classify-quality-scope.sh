#!/usr/bin/env bash
set -euo pipefail

classifier="$(dirname "$0")/classify-quality-scope.sh"

assert_scope() {
  local name="$1" expected="$2"
  shift 2
  local actual
  actual="$(printf '%s\n' "$@" | "$classifier")"
  [[ "$actual" == "$expected" ]] || {
    printf 'scenario %s failed\nexpected:\n%s\nactual:\n%s\n' "$name" "$expected" "$actual" >&2
    exit 1
  }
}

assert_scope backend-only $'backend=true\nfrontend=true\nbootstrap=false' apps/api/app/main.py
assert_scope frontend-only $'backend=false\nfrontend=true\nbootstrap=false' apps/web/app/page.tsx
assert_scope backend-and-frontend $'backend=true\nfrontend=true\nbootstrap=false' apps/api/app/main.py apps/web/app/page.tsx
assert_scope workflow-only $'backend=false\nfrontend=false\nbootstrap=false' .github/workflows/quality.yml
assert_scope documentation-only $'backend=false\nfrontend=false\nbootstrap=false' docs/runbook.md

echo 'QUALITY_SCOPE_SCENARIOS=PASS'
