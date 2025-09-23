#!/usr/bin/env bash
set -euo pipefail
: "${DB_URL:?set DB_URL to your Postgres URL}"
ts=$(date -u +"%Y%m%d-%H%M%S")
pg_dump "$DB_URL" > "backup-$ts.sql"
echo "Wrote backup-$ts.sql"
