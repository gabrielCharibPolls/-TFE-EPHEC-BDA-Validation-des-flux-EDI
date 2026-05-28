#!/usr/bin/env python3
"""Sync Docker local (5433) → PostgreSQL Railway."""
from __future__ import annotations

import io
import os
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
TABLES = ("validation_runs", "validation_errors", "order_facts", "order_lines")


def load_env() -> None:
    for name in (".env.railway", ".env"):
        p = ROOT / name
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def remote_url() -> str:
    url = os.environ.get("DATABASE_PUBLIC_URL", "")
    if not url:
        raise SystemExit("DATABASE_PUBLIC_URL manquant dans .env.railway")
    return url if "sslmode=" in url else f"{url}?sslmode=require"


def copy_table(local, remote, table: str) -> int:
    with local.cursor() as cur:
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=%s)",
            (table,),
        )
        if not cur.fetchone()[0]:
            print(f"  {table}: absente en local, ignorée")
            return 0
        buf = io.StringIO()
        cur.copy_expert(f"COPY {table} TO STDOUT WITH (FORMAT CSV)", buf)
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = int(cur.fetchone()[0])
    if not buf.getvalue().strip():
        return 0
    buf.seek(0)
    with remote.cursor() as cur:
        cur.copy_expert(f"COPY {table} FROM STDIN WITH (FORMAT CSV)", buf)
    remote.commit()
    return count


def truncate_remote(remote, tables: tuple[str, ...]) -> None:
    with remote.cursor() as cur:
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = ANY(%s)",
            (list(tables),),
        )
        existing = [row[0] for row in cur.fetchall()]
        if existing:
            cur.execute(f"TRUNCATE {', '.join(existing)} RESTART IDENTITY CASCADE")
    remote.commit()


def main() -> int:
    load_env()
    local = psycopg2.connect(
        os.environ.get("LOCAL_DATABASE_URL", "postgresql://edi:edi@127.0.0.1:5433/edi_validation")
    )
    remote = psycopg2.connect(remote_url())

    for sql in ("sql/init.sql", "sql/order_facts.sql", "sql/views.sql"):
        p = ROOT / sql
        if not p.is_file():
            continue
        print(f"Schéma distant : {sql}")
        with remote.cursor() as cur:
            cur.execute(p.read_text(encoding="utf-8"))
        remote.commit()

    truncate_remote(remote, TABLES)

    for table in TABLES:
        print(f"  {table}: {copy_table(local, remote, table)} lignes")

    with remote.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM validation_runs")
        print(f"OK Railway — runs={cur.fetchone()[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
