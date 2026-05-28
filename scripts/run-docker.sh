#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp env.example .env
fi

docker compose up -d db
echo "Attente PostgreSQL..."
until docker compose exec -T db pg_isready -U "${POSTGRES_USER:-edi}" -d "${POSTGRES_DB:-edi_validation}" >/dev/null 2>&1; do
  sleep 1
done

docker compose run --rm validator
