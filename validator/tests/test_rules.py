from __future__ import annotations

import xml.etree.ElementTree as ET

from app.load import orders_root
from app.rules import (
    rule_r01_envelope_and_orders,
    rule_r09_lin_gtin,
    rule_r10_pri_amount,
    run_all_rules,
)


def test_r01_ok(minimal_orders_xml: ET.Element) -> None:
    orders = orders_root(minimal_orders_xml)
    assert rule_r01_envelope_and_orders(minimal_orders_xml) == []
    assert orders is not None


def test_r01_missing_envelope() -> None:
    root = ET.fromstring("<root/>")
    v = rule_r01_envelope_and_orders(root)
    assert len(v) == 1
    assert v[0].rule_id == "R01"


def test_r09_invalid_gtin(minimal_orders_xml: ET.Element) -> None:
    orders = orders_root(minimal_orders_xml)
    assert orders is not None
    for g25 in orders.iter("g025"):
        lin = g25.find("LIN")
        if lin is not None:
            el = lin.find("cmp01/e01_7140")
            if el is not None:
                el.text = "ABC"
    v = rule_r09_lin_gtin(orders)
    assert any(x.rule_id == "R09" for x in v)


def test_r10_negative_price(minimal_orders_xml: ET.Element) -> None:
    orders = orders_root(minimal_orders_xml)
    assert orders is not None
    for pri in orders.iter("PRI"):
        el = pri.find("cmp01/e02_5118")
        if el is not None:
            el.text = "-1"
    v = rule_r10_pri_amount(orders)
    assert any(x.rule_id == "R10" for x in v)


def test_run_all_rules_ok(minimal_orders_xml: ET.Element) -> None:
    orders = orders_root(minimal_orders_xml)
    assert run_all_rules(minimal_orders_xml, orders) == []


def test_engine_validate_file_ok(tmp_oro_file) -> None:
    from app.engine import validate_file

    r = validate_file(tmp_oro_file)
    assert r.status == "OK"
    assert r.order_facts is not None
