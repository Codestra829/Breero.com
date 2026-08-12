#!/usr/bin/env sh
set -eu

: "${BREERO_BACKEND_IMAGE:?Set an immutable BREERO_BACKEND_IMAGE}"
: "${BREERO_FRONTEND_IMAGE:?Set an immutable BREERO_FRONTEND_IMAGE}"
: "${BREERO_STAGING_BACKEND_IMAGE:?Set an immutable BREERO_STAGING_BACKEND_IMAGE}"
: "${BREERO_STAGING_FRONTEND_IMAGE:?Set an immutable BREERO_STAGING_FRONTEND_IMAGE}"
: "${BREERO_STAGING_ENV_FILE:?Set the absolute staging env-file path}"
: "${BREERO_PRODUCTION_ENV_FILE:?Set the absolute production env-file path}"

case "$BREERO_BACKEND_IMAGE $BREERO_FRONTEND_IMAGE $BREERO_STAGING_BACKEND_IMAGE $BREERO_STAGING_FRONTEND_IMAGE" in
  *latest*) echo "latest tags are forbidden" >&2; exit 1 ;;
esac

test -f "$BREERO_STAGING_ENV_FILE"
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

docker compose -f infra/production/compose.frontend.yml config --services
docker compose -f infra/production/compose.backend.yml --profile migration config --services
docker compose -f infra/staging/compose.frontend.yml config --services
docker compose -f infra/staging/compose.backend.yml --profile migration config --services
