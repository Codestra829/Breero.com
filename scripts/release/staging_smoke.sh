#!/usr/bin/env sh
set -eu

: "${BREERO_STAGING_API_URL:?Set staging API URL, including /api/v1 where applicable}"
: "${BREERO_STAGING_WEB_URL:?Set staging web URL}"

case "$BREERO_STAGING_API_URL $BREERO_STAGING_WEB_URL" in
  *localhost*|*127.0.0.1*) : ;;
  *staging*) : ;;
  *) echo "refusing to smoke a URL that is not clearly staging/loopback" >&2; exit 1 ;;
esac

curl --fail --silent --show-error "${BREERO_STAGING_API_URL%/api/v1}/health/live" >/dev/null
curl --fail --silent --show-error "${BREERO_STAGING_API_URL%/api/v1}/health/ready" >/dev/null
curl --fail --silent --show-error "$BREERO_STAGING_API_URL/services" >/dev/null
curl --fail --silent --show-error "$BREERO_STAGING_WEB_URL" >/dev/null
echo "staging smoke passed"
