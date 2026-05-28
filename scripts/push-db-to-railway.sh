#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose up -d db >/dev/null
until docker compose exec -T db pg_isready -U edi -d edi_validation >/dev/null 2>&1; do sleep 1; done

cd validator
[[ -d .venv ]] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
source .venv/bin/activate
exec python ../scripts/sync_railway.py
