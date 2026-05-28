#!/usr/bin/env bash
# Crée ou met à jour les vues KPI (sql/views.sql) sur une base déjà initialisée
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Créer .env depuis env.example avant d'exécuter ce script." >&2
  exit 1
fi
# shellcheck disable=SC1091
set -a
source .env
set +a

USER="${POSTGRES_USER:-edi}"
DB="${POSTGRES_DB:-edi_validation}"

for sql in sql/order_facts.sql sql/views.sql; do
  docker compose exec -T db psql -U "$USER" -d "$DB" -v ON_ERROR_STOP=1 < "$sql"
done
echo "Schéma order_facts + vues KPI appliqués (v_runs_enriched, v_lines_enriched, …)."
