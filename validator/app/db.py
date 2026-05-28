from __future__ import annotations

import os
import time
from typing import Any

import psycopg2
from psycopg2.extensions import connection as PgConnection

from .extract import OrderFacts
from .models import FileResult


def connect_with_retry(max_attempts: int = 30, delay_sec: float = 1.0) -> PgConnection:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL non défini.")
    last: Exception | None = None
    for _ in range(max_attempts):
        try:
            conn = psycopg2.connect(url)
            conn.autocommit = False
            return conn
        except Exception as e:
            last = e
            time.sleep(delay_sec)
    raise RuntimeError(f"Impossible de joindre PostgreSQL après {max_attempts} tentatives : {last}")


def _persist_order_facts(cur: Any, run_id: int, facts: OrderFacts) -> None:
    gtins = {line.gtin for line in facts.lines if line.gtin}
    cur.execute(
        """
        INSERT INTO order_facts (
            run_id, document_date, buyer_gln, buyer_name,
            supplier_gln, supplier_name, line_count, distinct_gtin_count
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO UPDATE SET
            document_date = EXCLUDED.document_date,
            buyer_gln = EXCLUDED.buyer_gln,
            buyer_name = EXCLUDED.buyer_name,
            supplier_gln = EXCLUDED.supplier_gln,
            supplier_name = EXCLUDED.supplier_name,
            line_count = EXCLUDED.line_count,
            distinct_gtin_count = EXCLUDED.distinct_gtin_count
        """,
        (
            run_id,
            facts.document_date,
            facts.sca_gln,
            facts.sca_name,
            facts.supplier_gln,
            facts.supplier_name,
            len(facts.lines),
            len(gtins),
        ),
    )
    cur.execute("DELETE FROM order_lines WHERE run_id = %s", (run_id,))
    for line in facts.lines:
        cur.execute(
            """
            INSERT INTO order_lines (
                run_id, line_number, gtin, description, qty_ordered, price_amount
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                str(line.line_no) if line.line_no else None,
                line.gtin,
                line.description,
                line.qty,
                line.price_amount,
            ),
        )


def persist_result(conn: PgConnection, result: FileResult) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO validation_runs (filename, file_sha256, status, error_count, finished_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
            """,
            (
                result.filename,
                result.file_sha256,
                result.status,
                len(result.violations),
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("INSERT validation_runs sans id retourné.")
        run_id: int = int(row[0])
        for v in result.violations:
            cur.execute(
                """
                INSERT INTO validation_errors (run_id, rule_id, message)
                VALUES (%s, %s, %s)
                """,
                (run_id, v.rule_id, v.message),
            )
        if result.order_facts is not None:
            _persist_order_facts(cur, run_id, result.order_facts)
