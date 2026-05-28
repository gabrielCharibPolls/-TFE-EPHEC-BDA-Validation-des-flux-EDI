#!/usr/bin/env bash
# Vérification rapide avant soutenance (oral 18–19 juin)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== TFE Scabel — vérification démo ==="

echo "[1/4] Tests pytest..."
make test

echo "[2/4] Validation batch (skip-db, max 3 fichiers)..."
cd validator
. .venv/bin/activate
export EDI_INPUT_DIR="$ROOT/in"
python -m app.main --input-dir "$ROOT/in" --skip-db --max-files 3 --no-alert
cd "$ROOT"

echo "[3/4] Fichiers figures..."
for f in figures/figure3_qlik_kpi.png figures/figure4_erreurs_regles.png figures/figure_schema_postgresql.png; do
  if [[ -f "$f" ]]; then
    echo "  OK $f"
  else
    echo "  MANQUANT $f — make figures-preview ou captures Qlik"
  fi
done

echo "[4/4] Docker (optionnel)..."
if command -v docker &>/dev/null; then
  docker compose ps 2>/dev/null || echo "  Docker non démarré — make docker-up si besoin"
else
  echo "  Docker non installé — démo native OK"
fi

echo "=== Fin — voir PREP_SOUTENANCE_ORAL.md ==="
