#!/usr/bin/env bash
# Prépare l'environnement natif (Mac ou Linux) : venv Python + dépendances validateur
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== TFE Scabel — setup natif ==="

missing=()
command -v python3 >/dev/null 2>&1 || missing+=("python3")
command -v pip3 >/dev/null 2>&1 || command -v python3 -m pip >/dev/null 2>&1 || missing+=("pip (python3 -m pip)")
command -v psql >/dev/null 2>&1 || missing+=("psql (client PostgreSQL)")

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Prérequis manquants : ${missing[*]}" >&2
  echo "" >&2
  echo "Mac (Homebrew) :" >&2
  echo "  brew install python@3 postgresql@16" >&2
  echo "  brew services start postgresql@16" >&2
  echo "" >&2
  echo "Debian 12 :" >&2
  echo "  sudo ./deploy/debian-setup.sh" >&2
  exit 1
fi

if ! pg_isready -q 2>/dev/null; then
  echo "Attention : PostgreSQL ne répond pas (pg_isready). Démarrez le service avant init-db."
  echo "  Mac : brew services start postgresql@16"
  echo "  Debian : sudo systemctl start postgresql"
fi

cd validator
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  echo "Environnement virtuel créé : validator/.venv"
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "Dépendances Python installées dans validator/.venv"

cd "$ROOT"
if [[ ! -f .env ]]; then
  cp env.example .env
  echo "Fichier .env créé depuis env.example"
fi

echo ""
echo "Étapes suivantes :"
echo "  1. Vérifier .env (DATABASE_URL, EDI_INPUT_DIR, alerting)"
echo "  2. ./scripts/init-db.sh     # schéma + vues KPI"
echo "  3. ./scripts/run-validator.sh   # ou : make run"
echo "  4. cd validator && source .venv/bin/activate && python -m pytest tests/ -v"
