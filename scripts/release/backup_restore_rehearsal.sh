#!/usr/bin/env sh
set -eu

: "${BREERO_BACKUP_DIR:?Set an explicit backup directory}"
: "${BREERO_SOURCE_DB_CONTAINER:?Set the source PostgreSQL container}"
: "${BREERO_RESTORE_DB_CONTAINER:?Set a distinct restore-test PostgreSQL container}"

if [ "$BREERO_SOURCE_DB_CONTAINER" = "$BREERO_RESTORE_DB_CONTAINER" ]; then
  echo "restore target must be isolated from source" >&2
  exit 1
fi

mkdir -p "$BREERO_BACKUP_DIR"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$BREERO_BACKUP_DIR/breero-$stamp.dump"

docker exec "$BREERO_SOURCE_DB_CONTAINER" sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl' >"$archive"
test -s "$archive"
sha256sum "$archive" >"$archive.sha256"
pg_restore --list "$archive" >/dev/null

docker exec -i "$BREERO_RESTORE_DB_CONTAINER" sh -c 'dropdb -U "$POSTGRES_USER" --if-exists breero_restore && createdb -U "$POSTGRES_USER" breero_restore' </dev/null
docker exec -i "$BREERO_RESTORE_DB_CONTAINER" sh -c 'pg_restore -U "$POSTGRES_USER" -d breero_restore --no-owner --no-acl' <"$archive"
docker exec "$BREERO_RESTORE_DB_CONTAINER" sh -c 'psql -U "$POSTGRES_USER" -d breero_restore -Atc "select version_num from alembic_version order by version_num; select count(*) from information_schema.tables where table_schema = '\''public'\'';"'

echo "backup=$archive"
cat "$archive.sha256"
