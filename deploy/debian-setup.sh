#!/usr/bin/env bash
# Installation PostgreSQL 16 + Python 3 (venv) sur Debian 12 (bookworm) — sans Docker
# Usage (root ou sudo) : sudo ./deploy/debian-setup.sh
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Exécuter ce script avec sudo." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  postgresql \
  postgresql-contrib \
  python3 \
  python3-venv \
  python3-pip \
  ca-certificates

systemctl enable --now postgresql

psql --version
python3 --version
echo ""
echo "PostgreSQL et Python prêts. Depuis la racine du projet :"
echo "  cp env.example .env"
echo "  ./scripts/setup-native.sh"
echo "  ./scripts/init-db.sh"
echo "  ./scripts/run-validator.sh"
