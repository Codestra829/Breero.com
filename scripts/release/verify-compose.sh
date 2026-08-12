#!/usr/bin/env sh
set -eu

: "${BREERO_BACKEND_IMAGE:?Set an immutable BREERO_BACKEND_IMAGE}"
: "${BREERO_WEB_IMAGE:?Set an immutable BREERO_WEB_IMAGE}"
: "${BREERO_STAGING_BACKEND_IMAGE:?Set an immutable BREERO_STAGING_BACKEND_IMAGE}"
: "${BREERO_STAGING_WEB_IMAGE:?Set an immutable BREERO_STAGING_WEB_IMAGE}"
: "${BREERO_STAGING_APP_ENV_FILE:?Set the staging application env-file path}"
: "${BREERO_STAGING_POSTGRES_ENV_FILE:?Set the staging PostgreSQL env-file path}"
: "${BREERO_STAGING_REDIS_ENV_FILE:?Set the staging Redis env-file path}"
: "${BREERO_PRODUCTION_APP_ENV_FILE:?Set the production application env-file path}"
: "${BREERO_PRODUCTION_POSTGRES_ENV_FILE:?Set the production PostgreSQL env-file path}"
: "${BREERO_PRODUCTION_REDIS_ENV_FILE:?Set the production Redis env-file path}"

case "$BREERO_BACKEND_IMAGE $BREERO_WEB_IMAGE $BREERO_STAGING_BACKEND_IMAGE $BREERO_STAGING_WEB_IMAGE" in
  *latest*) echo "latest tags are forbidden" >&2; exit 1 ;;
esac

for env_file in "$BREERO_STAGING_APP_ENV_FILE" "$BREERO_STAGING_POSTGRES_ENV_FILE" \
  "$BREERO_STAGING_REDIS_ENV_FILE" "$BREERO_PRODUCTION_APP_ENV_FILE" \
  "$BREERO_PRODUCTION_POSTGRES_ENV_FILE" "$BREERO_PRODUCTION_REDIS_ENV_FILE"; do
  test -f "$env_file"
done

BREERO_STAGING_APP_ENV_FILE=$(realpath "$BREERO_STAGING_APP_ENV_FILE")
BREERO_STAGING_POSTGRES_ENV_FILE=$(realpath "$BREERO_STAGING_POSTGRES_ENV_FILE")
BREERO_STAGING_REDIS_ENV_FILE=$(realpath "$BREERO_STAGING_REDIS_ENV_FILE")
BREERO_PRODUCTION_APP_ENV_FILE=$(realpath "$BREERO_PRODUCTION_APP_ENV_FILE")
BREERO_PRODUCTION_POSTGRES_ENV_FILE=$(realpath "$BREERO_PRODUCTION_POSTGRES_ENV_FILE")
BREERO_PRODUCTION_REDIS_ENV_FILE=$(realpath "$BREERO_PRODUCTION_REDIS_ENV_FILE")
export BREERO_STAGING_APP_ENV_FILE BREERO_STAGING_POSTGRES_ENV_FILE
export BREERO_STAGING_REDIS_ENV_FILE BREERO_PRODUCTION_APP_ENV_FILE
export BREERO_PRODUCTION_POSTGRES_ENV_FILE BREERO_PRODUCTION_REDIS_ENV_FILE

if grep -Eq 'STRIPE|JWT|ODOO|SMTP|SMS|PAYOUT|GEOCOD' "$BREERO_PRODUCTION_POSTGRES_ENV_FILE" "$BREERO_PRODUCTION_REDIS_ENV_FILE" "$BREERO_STAGING_POSTGRES_ENV_FILE" "$BREERO_STAGING_REDIS_ENV_FILE"; then
  echo "provider/application secret leaked into a data-service env file" >&2
  exit 1
fi
docker compose -f infra/production/compose.frontend.yml config --quiet
docker compose -f infra/production/compose.backend.yml --profile migration config --quiet
docker compose -f infra/staging/compose.frontend.yml config --quiet
docker compose -f infra/staging/compose.backend.yml --profile migration config --quiet

for file in infra/production/compose.frontend.yml infra/production/compose.backend.yml infra/staging/compose.frontend.yml infra/staging/compose.backend.yml; do
  if docker compose -f "$file" config | grep -Eq 'published:|host_ip:|ports:'; then
    echo "public port policy violation in $file" >&2
    exit 1
  fi
done

test "$(docker compose -f infra/production/compose.frontend.yml config --services)" = "web"
test "$(docker compose -f infra/staging/compose.frontend.yml config --services)" = "web"

docker compose -f infra/production/compose.frontend.yml config --services
docker compose -f infra/production/compose.backend.yml --profile migration config --services
docker compose -f infra/staging/compose.frontend.yml config --services
docker compose -f infra/staging/compose.backend.yml --profile migration config --services
