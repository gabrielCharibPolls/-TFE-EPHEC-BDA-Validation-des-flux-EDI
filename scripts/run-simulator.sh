#!/usr/bin/env bash
# Génère des commandes simulées (~100/jour, ~10 % d'erreurs) + validation + trace JSONL
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a
  source .env
  set +a
fi

export SIM_OUTPUT_DIR="${SIM_OUTPUT_DIR:-$ROOT/in/simulated}"
export SIM_DAILY_QUOTA="${SIM_DAILY_QUOTA:-100}"
export SIM_ERROR_RATE="${SIM_ERROR_RATE:-0.10}"

# Validation → PostgreSQL Docker (port 5433)
docker compose up -d db >/dev/null
until docker compose exec -T db pg_isready -U edi -d edi_validation >/dev/null 2>&1; do sleep 1; done
docker compose exec -T db psql -U edi -d edi_validation -v ON_ERROR_STOP=1 < sql/init.sql >/dev/null
docker compose exec -T db psql -U edi -d edi_validation -v ON_ERROR_STOP=1 < sql/order_facts.sql >/dev/null

export DATABASE_URL="${SIM_DATABASE_URL:-postgresql://edi:edi@127.0.0.1:5433/edi_validation}"

if [[ -d validator/.venv ]]; then
  # shellcheck disable=SC1091
  source validator/.venv/bin/activate
fi

cd validator
exec python -m app.simulate "$@"
