#!/usr/bin/env sh
set -eu

: "${BREERO_API_IMAGE:?Set an immutable BREERO_API_IMAGE}"
: "${BREERO_WEB_IMAGE:?Set an immutable BREERO_WEB_IMAGE}"
: "${BREERO_STAGING_ENV_FILE:?Set the absolute staging env-file path}"

case "$BREERO_API_IMAGE $BREERO_WEB_IMAGE" in
  *latest*) echo "latest tags are forbidden" >&2; exit 1 ;;
esac

test -f "$BREERO_STAGING_ENV_FILE"
docker compose -f docker-compose.staging.yml config --quiet
docker compose -f docker-compose.staging.yml --profile migration config --services
