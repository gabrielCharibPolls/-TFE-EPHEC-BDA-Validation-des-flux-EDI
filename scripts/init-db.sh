#!/usr/bin/env bash
# Initialise PostgreSQL : rôle, base, schéma (init.sql) et vues KPI (views.sql)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Créer .env depuis env.example : cp env.example .env" >&2
  exit 1
fi
# shellcheck disable=SC1091
set -a
source .env
set +a

PGUSER="${POSTGRES_USER:-edi}"
PGPASS="${POSTGRES_PASSWORD:-edi}"
PGDB="${POSTGRES_DB:-edi_validation}"
PGPORT="${POSTGRES_PORT:-5432}"
export PGPASSWORD="$PGPASS"

psql_admin() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    # Homebrew : superuser = utilisateur macOS courant
    psql -h localhost -p "$PGPORT" -d postgres "$@"
  elif command -v sudo >/dev/null 2>&1 && id postgres &>/dev/null; then
    sudo -u postgres psql -p "$PGPORT" "$@"
  else
    psql -h localhost -p "$PGPORT" -d postgres "$@"
  fi
}

echo "=== Création rôle et base (si absent) ==="
psql_admin -v ON_ERROR_STOP=0 <<SQL || true
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${PGUSER}') THEN
    CREATE ROLE ${PGUSER} LOGIN PASSWORD '${PGPASS}';
  END IF;
END
\$\$;
SQL

psql_admin -v ON_ERROR_STOP=0 -tc "SELECT 1 FROM pg_database WHERE datname = '${PGDB}'" | grep -q 1 \
  || psql_admin -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${PGDB} OWNER ${PGUSER};"

echo "=== Schéma (sql/init.sql) ==="
psql -h localhost -p "$PGPORT" -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 -f sql/init.sql

echo "=== Faits commande (sql/order_facts.sql) ==="
psql -h localhost -p "$PGPORT" -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 -f sql/order_facts.sql

echo "=== Vues KPI (sql/views.sql) ==="
psql -h localhost -p "$PGPORT" -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 -f sql/views.sql

echo "Base ${PGDB} prête (tables + faits commande + vues KPI)."
