#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

set -a
source "$APP_DIR/.env"
set +a

echo "[migrate] Waiting for DB to be ready..."
for i in $(seq 1 20); do
    if docker compose -f "$APP_DIR/docker-compose.yml" exec -T db \
        mysqladmin ping -h localhost -p"${MYSQL_ROOT_PASSWORD:-root123}" --silent 2>/dev/null; then
        echo "[migrate] DB is ready."
        break
    fi
    echo "[migrate] attempt $i/20, retrying in 3s..."
    sleep 3
done

cd "$APP_DIR"

echo "[migrate] Adding bank columns to users table..."
docker compose exec -T db mysql \
    -u"${MYSQL_USER:-vulntrade}" \
    -p"${MYSQL_PASSWORD:-vulntrade123}" \
    "${MYSQL_DATABASE:-vulntrade}" \
    -e "ALTER TABLE users
          ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100) DEFAULT NULL,
          ADD COLUMN IF NOT EXISTS account_number VARCHAR(50) DEFAULT NULL,
          ADD COLUMN IF NOT EXISTS account_holder VARCHAR(50) DEFAULT NULL;"

echo "[migrate] Done."
