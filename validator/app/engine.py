from __future__ import annotations

from pathlib import Path

from .extract import extract_order_facts
from .load import orders_root, parse_orders, sha256_file
from .models import FileResult, Violation
from .rules import run_all_rules


def validate_file(path: Path) -> FileResult:
    sha = sha256_file(path)
    tree, parse_err = parse_orders(path)
    if parse_err:
        return FileResult(
            path.name,
            sha,
            "PARSE_ERROR",
            [Violation("PARSE", parse_err)],
        )
    root = tree.getroot()
    orders = orders_root(root)
    violations = run_all_rules(root, orders)
    status = "OK" if not violations else "KO"
    facts = extract_order_facts(orders) if orders is not None else None
    return FileResult(path.name, sha, status, violations, order_facts=facts)
