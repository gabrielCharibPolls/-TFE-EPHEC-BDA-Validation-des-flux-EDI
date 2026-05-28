#!/bin/sh
set -e
INPUT="${EDI_INPUT_DIR:-/data/in}"
if [ ! -d "$INPUT" ]; then
  echo "Répertoire EDI introuvable : ${INPUT}" >&2
  echo "Utilisez : make docker-run" >&2
  exit 1
fi
exec "$@"
