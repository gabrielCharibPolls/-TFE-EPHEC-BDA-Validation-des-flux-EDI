from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from .alerting import notify_validation_failure
from .db import connect_with_retry, persist_result
from .engine import validate_file
from .logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> int:
    configure_logging()
    p = argparse.ArgumentParser(description="Validation batch des fichiers ORDERS (.ORO)")
    p.add_argument(
        "--input-dir",
        type=Path,
        default=Path(os.environ.get("EDI_INPUT_DIR", "/data/in")),
        help="Répertoire des fichiers .ORO",
    )
    p.add_argument(
        "--skip-db",
        action="store_true",
        help="Ne pas écrire dans PostgreSQL (tests locaux)",
    )
    p.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="Limite le nombre de fichiers (0 = illimité). Surcharge possible via VALIDATOR_MAX_FILES.",
    )
    p.add_argument(
        "--no-alert",
        action="store_true",
        help="Désactiver Teams/SMTP même si configuré",
    )
    args = p.parse_args()

    max_files = args.max_files
    if max_files == 0 and os.environ.get("VALIDATOR_MAX_FILES"):
        max_files = int(os.environ["VALIDATOR_MAX_FILES"])

    if not args.input_dir.is_dir():
        logger.error("Répertoire introuvable : %s", args.input_dir)
        return 1

    files = sorted(args.input_dir.glob("*.ORO"))
    if max_files > 0:
        files = files[:max_files]

    if not files:
        logger.info("Aucun fichier .ORO à traiter.")
        return 0

    conn = None
    if not args.skip_db:
        try:
            conn = connect_with_retry()
        except RuntimeError as e:
            logger.error("%s", e)
            return 1

    ok = ko = pe = 0
    try:
        for fp in files:
            r = validate_file(fp)
            if r.status == "OK":
                ok += 1
            elif r.status == "KO":
                ko += 1
            else:
                pe += 1

            logger.info(
                "validation file=%s status=%s violations=%d",
                r.filename,
                r.status,
                len(r.violations),
                extra={
                    "event": "file_validated",
                    "oro_file": r.filename,
                    "run_status": r.status,
                    "violation_count": len(r.violations),
                },
            )

            if conn is not None:
                persist_result(conn, r)
                conn.commit()

            if r.status != "OK" and not args.no_alert:
                notify_validation_failure(r)
                for v in r.violations[:5]:
                    logger.warning("%s: %s", v.rule_id, v.message)
                if len(r.violations) > 5:
                    logger.warning("... +%d autre(s) violation(s)", len(r.violations) - 5)
    finally:
        if conn is not None:
            conn.close()

    logger.info(
        "Résumé batch OK=%d KO=%d PARSE_ERROR=%d (total %d)",
        ok,
        ko,
        pe,
        len(files),
        extra={"event": "batch_complete", "ok": ok, "ko": ko, "parse_error": pe, "total": len(files)},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
