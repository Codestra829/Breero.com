#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  verify-runtime-paths.sh --config FILE --mode syntax
  verify-runtime-paths.sh --config FILE --mode host-read-only
  verify-runtime-paths.sh --config - --mode host-read-only < runtime-paths.env

The verifier never sources the configuration and never performs a deployment,
container mutation, proxy reload, migration, package installation, or file write.
EOF
}

fail() {
  printf 'RUNTIME_PATH_VERIFICATION_ERROR=%s\n' "$1" >&2
  exit 2
}

config_path=""
mode=""
while (($#)); do
  case "$1" in
    --config)
      (($# >= 2)) || fail "--config requires a value"
      config_path="$2"
      shift 2
      ;;
    --mode)
      (($# >= 2)) || fail "--mode requires a value"
      mode="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "$config_path" ]] || fail "--config is required"
[[ "$mode" == syntax || "$mode" == host-read-only ]] || fail "mode must be syntax or host-read-only"
if [[ "$config_path" != - ]]; then
  [[ -f "$config_path" && -r "$config_path" ]] || fail "configuration is not a readable file"
fi

declare -A cfg=()
declare -A allowed=()
required_keys=(
  VERIFICATION_STATE
  LIVE_MUTATION_ALLOWED
  EXPECTED_HOSTNAME
  REPOSITORY_ROOT
  BACKEND_COMPOSE_PATH
  FRONTEND_COMPOSE_PATH
  LEGACY_BACKEND_COMPOSE_PATH
  CADDY_CONFIG_PATH
  BACKEND_ENV_PATH
  FRONTEND_ENV_PATH
  EXPECTED_BACKEND_COMPOSE_SHA256
  EXPECTED_FRONTEND_COMPOSE_SHA256
  EXPECTED_CADDY_CONFIG_SHA256
  EXPECTED_API_IMAGE
  EXPECTED_FRONTEND_IMAGE
  EXPECTED_PRIVATE_NETWORK
  EXPECTED_BACKEND_EDGE_NETWORK
  EXPECTED_FRONTEND_EDGE_NETWORK
  EXPECTED_WEB_HOST
  EXPECTED_API_HOST
  EXPECTED_WEB_UPSTREAM
  EXPECTED_API_UPSTREAM
)
for key in "${required_keys[@]}"; do allowed["$key"]=1; done

line_number=0
parse_line() {
  local line="$1" key value
  ((line_number += 1))
  line="${line%$'\r'}"
  [[ "$line" =~ ^[[:space:]]*$ ]] && return
  [[ "$line" =~ ^[[:space:]]*# ]] && return
  [[ "$line" =~ ^([A-Z0-9_]+)=(.*)$ ]] || fail "invalid configuration line $line_number"
  key="${BASH_REMATCH[1]}"
  value="${BASH_REMATCH[2]}"
  [[ ${allowed[$key]+yes} ]] || fail "unknown key on line $line_number: $key"
  [[ ! ${cfg[$key]+yes} ]] || fail "duplicate key on line $line_number: $key"
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || fail "multiline values are forbidden"
  cfg["$key"]="$value"
}

if [[ "$config_path" == - ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do parse_line "$line"; done
else
  while IFS= read -r line || [[ -n "$line" ]]; do parse_line "$line"; done <"$config_path"
fi

for key in "${required_keys[@]}"; do
  [[ ${cfg[$key]+yes} && -n "${cfg[$key]}" ]] || fail "missing required key: $key"
done

[[ "${cfg[LIVE_MUTATION_ALLOWED]}" == false ]] || fail "LIVE_MUTATION_ALLOWED must remain false"
[[ "${cfg[VERIFICATION_STATE]}" == UNVERIFIED || "${cfg[VERIFICATION_STATE]}" == READY_FOR_READ_ONLY_VERIFICATION ]] \
  || fail "VERIFICATION_STATE must be UNVERIFIED or READY_FOR_READ_ONLY_VERIFICATION"

absolute_path_keys=(
  REPOSITORY_ROOT BACKEND_COMPOSE_PATH FRONTEND_COMPOSE_PATH LEGACY_BACKEND_COMPOSE_PATH
  CADDY_CONFIG_PATH BACKEND_ENV_PATH FRONTEND_ENV_PATH
)
for key in "${absolute_path_keys[@]}"; do
  value="${cfg[$key]}"
  [[ "$value" == /* ]] || fail "$key must be an absolute path"
  [[ ! "$value" =~ (^|/)\.\.(/|$) ]] || fail "$key must not contain parent traversal"
done

safe_name='^[A-Za-z0-9._:-]+$'
for key in EXPECTED_HOSTNAME EXPECTED_PRIVATE_NETWORK EXPECTED_BACKEND_EDGE_NETWORK EXPECTED_FRONTEND_EDGE_NETWORK EXPECTED_WEB_HOST EXPECTED_API_HOST EXPECTED_WEB_UPSTREAM EXPECTED_API_UPSTREAM; do
  [[ "${cfg[$key]}" == UNVERIFIED || "${cfg[$key]}" =~ $safe_name ]] || fail "$key contains unsafe characters"
done

image_pattern='^[^[:space:]]+@sha256:[0-9a-f]{64}$'
for key in EXPECTED_API_IMAGE EXPECTED_FRONTEND_IMAGE; do
  [[ "${cfg[$key]}" == UNVERIFIED || "${cfg[$key]}" =~ $image_pattern ]] || fail "$key must be UNVERIFIED or an immutable sha256 digest"
done

hash_pattern='^[0-9a-f]{64}$'
for key in EXPECTED_BACKEND_COMPOSE_SHA256 EXPECTED_FRONTEND_COMPOSE_SHA256 EXPECTED_CADDY_CONFIG_SHA256; do
  [[ "${cfg[$key]}" == UNVERIFIED || "${cfg[$key]}" =~ $hash_pattern ]] || fail "$key must be UNVERIFIED or a SHA-256 hash"
done

printf 'RUNTIME_PATH_CONFIGURATION=VALID\n'
printf 'LIVE_MUTATION_ALLOWED=false\n'
printf 'VERIFICATION_MODE=%s\n' "$mode"

if [[ "$mode" == syntax ]]; then
  printf 'RUNTIME_PATHS_VERIFIED=NO\n'
  printf 'LIVE_SERVER_CHANGED=NO\n'
  exit 0
fi

[[ "${cfg[VERIFICATION_STATE]}" == READY_FOR_READ_ONLY_VERIFICATION ]] \
  || fail "host-read-only mode requires VERIFICATION_STATE=READY_FOR_READ_ONLY_VERIFICATION"
for key in EXPECTED_HOSTNAME EXPECTED_BACKEND_COMPOSE_SHA256 EXPECTED_FRONTEND_COMPOSE_SHA256 EXPECTED_CADDY_CONFIG_SHA256 EXPECTED_API_IMAGE EXPECTED_FRONTEND_IMAGE EXPECTED_PRIVATE_NETWORK EXPECTED_BACKEND_EDGE_NETWORK EXPECTED_FRONTEND_EDGE_NETWORK EXPECTED_WEB_HOST EXPECTED_API_HOST EXPECTED_WEB_UPSTREAM EXPECTED_API_UPSTREAM; do
  [[ "${cfg[$key]}" != UNVERIFIED ]] || fail "$key must be populated for host-read-only verification"
done

for command_name in hostname sha256sum stat docker caddy ss grep awk; do
  command -v "$command_name" >/dev/null 2>&1 || fail "required read-only command is unavailable: $command_name"
done

[[ -d "${cfg[REPOSITORY_ROOT]}" ]] || fail "repository root does not exist"
for key in BACKEND_COMPOSE_PATH FRONTEND_COMPOSE_PATH LEGACY_BACKEND_COMPOSE_PATH CADDY_CONFIG_PATH BACKEND_ENV_PATH FRONTEND_ENV_PATH; do
  [[ -f "${cfg[$key]}" && -r "${cfg[$key]}" ]] || fail "$key is not a readable file"
done

actual_hostname="$(hostname -f 2>/dev/null || hostname)"
[[ "$actual_hostname" == "${cfg[EXPECTED_HOSTNAME]}" ]] || fail "hostname does not match the approved inventory"

verify_hash() {
  local path="$1" expected="$2" label="$3" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || fail "$label checksum mismatch"
  printf '%s_SHA256=%s\n' "$label" "$actual"
}
verify_hash "${cfg[BACKEND_COMPOSE_PATH]}" "${cfg[EXPECTED_BACKEND_COMPOSE_SHA256]}" BACKEND_COMPOSE
verify_hash "${cfg[FRONTEND_COMPOSE_PATH]}" "${cfg[EXPECTED_FRONTEND_COMPOSE_SHA256]}" FRONTEND_COMPOSE
verify_hash "${cfg[CADDY_CONFIG_PATH]}" "${cfg[EXPECTED_CADDY_CONFIG_SHA256]}" CADDY_CONFIG

for key in BACKEND_ENV_PATH FRONTEND_ENV_PATH; do
  mode_bits="$(stat -c '%a' "${cfg[$key]}")"
  world_digit="${mode_bits: -1}"
  [[ "$world_digit" == 0 ]] || fail "$key must not be world-accessible"
done

backend_images="$(docker compose --env-file "${cfg[BACKEND_ENV_PATH]}" -f "${cfg[BACKEND_COMPOSE_PATH]}" config --images)"
docker compose --env-file "${cfg[BACKEND_ENV_PATH]}" -f "${cfg[BACKEND_COMPOSE_PATH]}" config --quiet
frontend_images="$(docker compose --env-file "${cfg[FRONTEND_ENV_PATH]}" -f "${cfg[FRONTEND_COMPOSE_PATH]}" config --images)"
docker compose --env-file "${cfg[FRONTEND_ENV_PATH]}" -f "${cfg[FRONTEND_COMPOSE_PATH]}" config --quiet
grep -Fxq "${cfg[EXPECTED_API_IMAGE]}" <<<"$backend_images" || fail "approved API image digest is not rendered by backend Compose"
grep -Fxq "${cfg[EXPECTED_FRONTEND_IMAGE]}" <<<"$frontend_images" || fail "approved frontend image digest is not rendered by frontend Compose"

private_internal="$(docker network inspect --format '{{.Internal}}' "${cfg[EXPECTED_PRIVATE_NETWORK]}")"
[[ "$private_internal" == true ]] || fail "approved private network is missing or not internal"
docker network inspect "${cfg[EXPECTED_BACKEND_EDGE_NETWORK]}" >/dev/null
docker network inspect "${cfg[EXPECTED_FRONTEND_EDGE_NETWORK]}" >/dev/null

caddy validate --config "${cfg[CADDY_CONFIG_PATH]}" >/dev/null
adapted_caddy="$(caddy adapt --config "${cfg[CADDY_CONFIG_PATH]}" 2>/dev/null)"
for key in EXPECTED_WEB_HOST EXPECTED_API_HOST EXPECTED_WEB_UPSTREAM EXPECTED_API_UPSTREAM; do
  grep -Fq "${cfg[$key]}" <<<"$adapted_caddy" || fail "$key was not found in the adapted Caddy configuration"
done

while IFS= read -r local_address; do
  [[ -n "$local_address" ]] || continue
  case "$local_address" in
    127.0.0.1:*|\[::1\]:*|::1:*) continue ;;
  esac
  port="${local_address##*:}"
  case "$port" in
    3000|8000|5432|6379) fail "public or non-loopback listener detected on protected port $port" ;;
  esac
done < <(ss -H -lnt | awk '{print $4}')

printf 'EXPECTED_HOSTNAME=%s\n' "${cfg[EXPECTED_HOSTNAME]}"
printf 'CANONICAL_BACKEND_COMPOSE=%s\n' "${cfg[BACKEND_COMPOSE_PATH]}"
printf 'LEGACY_BACKEND_COMPOSE_INVENTORY=%s\n' "${cfg[LEGACY_BACKEND_COMPOSE_PATH]}"
printf 'RUNTIME_PATHS_VERIFIED=YES\n'
printf 'LIVE_SERVER_CHANGED=NO\n'
