#!/usr/bin/env bash
set -euo pipefail
: "${SRC_SQL:?path to backup sql}"
: "${TARGET_DB_URL:?target Postgres URL}"
psql "$TARGET_DB_URL" -c "SELECT 1;" >/dev/null
psql "$TARGET_DB_URL" < "$SRC_SQL"
echo "Restored $SRC_SQL to $TARGET_DB_URL at $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
