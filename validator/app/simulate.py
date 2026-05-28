from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from .db import connect_with_retry, persist_result
from .engine import validate_file
from .generator import DEFECTS, generate_batch


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_state(state_path: Path) -> dict:
    if not state_path.is_file():
        return {"date": "", "generated_today": 0, "last_seq": 900_000_000}
    return json.loads(state_path.read_text(encoding="utf-8"))


def _save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_trace(trace_path: Path, entry: dict) -> None:
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _daily_count(state: dict, today: str) -> int:
    if state.get("date") != today:
        return 0
    return int(state.get("generated_today", 0))


def main() -> int:
    p = argparse.ArgumentParser(
        description="Génère des commandes .ORO simulées (~100/jour, ~10%% d'erreurs) puis valide."
    )
    p.add_argument("--output-dir", type=Path, default=Path(os.environ.get("SIM_OUTPUT_DIR", "in/simulated")))
    p.add_argument("--count", type=int, default=int(os.environ.get("SIM_BATCH_COUNT", "0")))
    p.add_argument("--daily-quota", type=int, default=int(os.environ.get("SIM_DAILY_QUOTA", "100")))
    p.add_argument("--error-rate", type=float, default=float(os.environ.get("SIM_ERROR_RATE", "0.10")))
    p.add_argument("--validate", action="store_true", default=True)
    p.add_argument("--skip-db", action="store_true")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    today = date.today().isoformat()
    state_path = args.output_dir / ".scheduler_state.json"
    trace_path = args.output_dir / "generation_trace.jsonl"
    state = _load_state(state_path)

    if state.get("date") != today:
        state["date"] = today
        state["generated_today"] = 0

    remaining = max(0, args.daily_quota - _daily_count(state, today))
    if args.count > 0:
        to_gen = min(args.count, remaining) if args.daily_quota > 0 else args.count
    else:
        # Répartition horaire : ~quota/24 par exécution (cron toutes les heures)
        to_gen = max(1, remaining // max(1, 24 - datetime.now().hour)) if remaining else 0

    if to_gen <= 0:
        print(f"Quota journalier atteint ({args.daily_quota} fichiers pour {today}).")
        return 0

    start_seq = int(state.get("last_seq", 900_000_000)) + 1
    batch = generate_batch(to_gen, error_rate=args.error_rate, start_seq=start_seq, seed=args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    run_id = _utc_now()
    written: list[Path] = []
    for order in batch:
        path = args.output_dir / order.filename
        path.write_bytes(order.content)
        written.append(path)
        _append_trace(
            trace_path,
            {
                "ts": _utc_now(),
                "run_id": run_id,
                "filename": order.filename,
                "intentional_defect": order.defect,
                "expected_rule": DEFECTS.get(order.defect or "", "OK"),
            },
        )

    state["generated_today"] = _daily_count(state, today) + len(batch)
    state["last_seq"] = start_seq + len(batch) - 1
    _save_state(state_path, state)

    n_defects = sum(1 for o in batch if o.defect)
    print(
        f"Génération : {len(batch)} fichier(s) → {args.output_dir} "
        f"({n_defects} avec défaut intentionnel, quota jour {state['generated_today']}/{args.daily_quota})"
    )
    print(f"Trace : {trace_path}")

    if not args.validate:
        return 0

    conn = None
    if not args.skip_db:
        try:
            conn = connect_with_retry()
        except RuntimeError as e:
            print(e, file=sys.stderr)
            return 1

    ok = ko = pe = 0
    try:
        for fp in written:
            r = validate_file(fp)
            if r.status == "OK":
                ok += 1
            elif r.status == "KO":
                ko += 1
            else:
                pe += 1
            if conn is not None:
                persist_result(conn, r)
                conn.commit()
    finally:
        if conn is not None:
            conn.close()

    print(f"Validation : OK={ok} KO={ko} PARSE_ERROR={pe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
