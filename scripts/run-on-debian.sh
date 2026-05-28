#!/usr/bin/env bash
# Lance la chaîne TFE sur Debian (PostgreSQL natif + batch validateur Python)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp env.example .env
  echo "Fichier .env créé depuis env.example — adapter POSTGRES_* et alerting si besoin."
fi

if ! systemctl is-active --quiet postgresql 2>/dev/null; then
  echo "Démarrage du service PostgreSQL..."
  sudo systemctl start postgresql || true
fi

if ! pg_isready -q 2>/dev/null; then
  echo "PostgreSQL n'est pas prêt. Exécuter : sudo ./deploy/debian-setup.sh" >&2
  exit 1
fi

./scripts/setup-native.sh
./scripts/init-db.sh
./scripts/run-validator.sh
echo "Batch terminé."
