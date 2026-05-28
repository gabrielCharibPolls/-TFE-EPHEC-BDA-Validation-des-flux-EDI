from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Violation:
    rule_id: str
    message: str


@dataclass
class OrderLineFact:
    line_no: int
    gtin: str | None
    description: str | None
    qty: str | None
    price_amount: str | None


@dataclass
class OrderFacts:
    document_date: date | None
    sca_gln: str | None
    sca_name: str | None
    supplier_gln: str | None
    supplier_name: str | None
    lines: list[OrderLineFact]


@dataclass
class FileResult:
    filename: str
    file_sha256: str
    status: str  # OK | KO | PARSE_ERROR
    violations: list[Violation] = field(default_factory=list)
    order_facts: OrderFacts | None = None
