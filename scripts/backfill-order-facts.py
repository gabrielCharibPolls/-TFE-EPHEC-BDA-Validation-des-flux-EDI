#!/usr/bin/env python3
"""Remplit order_facts / order_lines pour les runs déjà en base (fichiers .ORO locaux)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "validator"))

import psycopg2

from app.db import _persist_order_facts
from app.engine import validate_file


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input-dir",
        type=Path,
        action="append",
        default=[ROOT / "in" / "simulated", ROOT / "in"],
    )
    p.add_argument(
        "--database-url",
        default=os.environ.get(
            "DATABASE_URL",
            "postgresql://edi:edi@127.0.0.1:5433/edi_validation",
        ),
    )
    args = p.parse_args()

    dirs = [d for d in args.input_dir if d.is_dir()]
    if not dirs:
        print("Aucun répertoire .ORO trouvé.", file=sys.stderr)
        return 1

    by_name: dict[str, Path] = {}
    for d in dirs:
        for fp in d.glob("*.ORO"):
            by_name[fp.name] = fp

    conn = psycopg2.connect(args.database_url)
    conn.autocommit = False
    updated = skipped = missing = 0

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, filename FROM validation_runs ORDER BY id")
            rows = cur.fetchall()

        for run_id, filename in rows:
            fp = by_name.get(filename)
            if fp is None:
                missing += 1
                continue
            result = validate_file(fp)
            if result.order_facts is None:
                skipped += 1
                continue
            with conn.cursor() as cur:
                _persist_order_facts(cur, int(run_id), result.order_facts)
            conn.commit()
            updated += 1

        print(f"Backfill terminé : {updated} enrichi(s), {skipped} ignoré(s), {missing} fichier(s) absent(s).")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
