#!/usr/bin/env bash
# Lance le batch de validation (Python natif + PostgreSQL local)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp env.example .env
  echo "Fichier .env créé depuis env.example — adapter si besoin."
fi
# shellcheck disable=SC1091
set -a
source .env
set +a

export DATABASE_URL="${DATABASE_URL:-postgresql://${POSTGRES_USER:-edi}:${POSTGRES_PASSWORD:-edi}@localhost:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-edi_validation}}"
export EDI_INPUT_DIR="${EDI_INPUT_DIR:-./in}"

if [[ ! -d validator/.venv ]]; then
  echo "Exécuter d'abord : ./scripts/setup-native.sh" >&2
  exit 1
fi

# shellcheck disable=SC1091
source validator/.venv/bin/activate
cd validator
exec python -m app.main "$@"
