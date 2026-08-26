#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
verifier="$root/scripts/deploy/verify-runtime-paths.sh"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT

write_config() {
  local destination="$1"
  cat >"$destination" <<EOF
VERIFICATION_STATE=UNVERIFIED
LIVE_MUTATION_ALLOWED=false
EXPECTED_HOSTNAME=UNVERIFIED
REPOSITORY_ROOT=$fixture/repository
BACKEND_COMPOSE_PATH=$fixture/repository/docker-compose.production.yml
FRONTEND_COMPOSE_PATH=$fixture/repository/deploy/frontend/docker-compose.frontend.yml
LEGACY_BACKEND_COMPOSE_PATH=$fixture/repository/deploy/production/docker-compose.backend.yml
CADDY_CONFIG_PATH=$fixture/etc/caddy/Caddyfile
BACKEND_ENV_PATH=$fixture/etc/breero/backend.env
FRONTEND_ENV_PATH=$fixture/etc/breero/frontend.env
EXPECTED_BACKEND_COMPOSE_SHA256=UNVERIFIED
EXPECTED_FRONTEND_COMPOSE_SHA256=UNVERIFIED
EXPECTED_CADDY_CONFIG_SHA256=UNVERIFIED
EXPECTED_API_IMAGE=UNVERIFIED
EXPECTED_FRONTEND_IMAGE=UNVERIFIED
EXPECTED_PRIVATE_NETWORK=UNVERIFIED
EXPECTED_BACKEND_EDGE_NETWORK=UNVERIFIED
EXPECTED_FRONTEND_EDGE_NETWORK=UNVERIFIED
EXPECTED_WEB_HOST=UNVERIFIED
EXPECTED_API_HOST=UNVERIFIED
EXPECTED_WEB_UPSTREAM=UNVERIFIED
EXPECTED_API_UPSTREAM=UNVERIFIED
EOF
}

expect_failure() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "scenario unexpectedly passed: $name" >&2
    exit 1
  fi
}

valid="$fixture/valid.env"
write_config "$valid"
output="$($verifier --config "$valid" --mode syntax)"
grep -Fxq 'RUNTIME_PATH_CONFIGURATION=VALID' <<<"$output"
grep -Fxq 'LIVE_MUTATION_ALLOWED=false' <<<"$output"
grep -Fxq 'RUNTIME_PATHS_VERIFIED=NO' <<<"$output"
grep -Fxq 'LIVE_SERVER_CHANGED=NO' <<<"$output"

relative="$fixture/relative.env"
write_config "$relative"
sed -i 's#^REPOSITORY_ROOT=.*#REPOSITORY_ROOT=relative/path#' "$relative"
expect_failure relative-path "$verifier" --config "$relative" --mode syntax

unknown="$fixture/unknown.env"
write_config "$unknown"
printf 'UNEXPECTED_SECRET_PATH=/tmp/not-allowed\n' >>"$unknown"
expect_failure unknown-key "$verifier" --config "$unknown" --mode syntax

mutation="$fixture/mutation.env"
write_config "$mutation"
sed -i 's/^LIVE_MUTATION_ALLOWED=false$/LIVE_MUTATION_ALLOWED=true/' "$mutation"
expect_failure mutation-enabled "$verifier" --config "$mutation" --mode syntax

unready="$fixture/unready.env"
write_config "$unready"
expect_failure unready-host-verification "$verifier" --config "$unready" --mode host-read-only

stdin_output="$($verifier --config - --mode syntax <"$valid")"
grep -Fxq 'RUNTIME_PATH_CONFIGURATION=VALID' <<<"$stdin_output"

forbidden_tokens=(
  "docker compose u""p"
  "docker compose d""own"
  "docker compose p""ull"
  "docker compose r""un"
  "docker compose e""xec"
  "caddy r""eload"
  "systemctl r""estart"
  "systemctl r""eload"
  "alembic u""pgrade"
  "ssh "
  "scp "
  "rsync "
)
for token in "${forbidden_tokens[@]}"; do
  if grep -Fq "$token" "$verifier"; then
    echo "read-only verifier contains forbidden mutation token: $token" >&2
    exit 1
  fi
done

if grep -Eq '(^|[;&|[:space:]])(rm|mv|cp|touch|mkdir|chmod|chown)([;&|[:space:]]|$)' "$verifier"; then
  echo 'read-only verifier contains a filesystem mutation command' >&2
  exit 1
fi

echo 'RUNTIME_PATH_VERIFIER_TESTS=PASS'
echo 'LIVE_SERVER_CHANGED=NO'
