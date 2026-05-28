from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import xml.etree.ElementTree as ET

from .models import OrderFacts, OrderLineFact


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    s = el.text.strip()
    return s if s else None


def _parse_edifact_date(raw: str | None) -> date | None:
    if not raw or len(raw) < 8 or not raw[:8].isdigit():
        return None
    y, m, d = int(raw[:4]), int(raw[4:6]), int(raw[6:8])
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _nad_party(orders: ET.Element, qualifier: str) -> tuple[str | None, str | None]:
    for nad in orders.iter("NAD"):
        if _text(nad.find("e01_3035")) != qualifier:
            continue
        cmp1 = nad.find("cmp01")
        cmp3 = nad.find("cmp03")
        gln = _text(cmp1.find("e01_3039")) if cmp1 is not None else None
        name = _text(cmp3.find("e01_3036")) if cmp3 is not None else None
        return gln, name
    return None, None


def extract_order_facts(orders: ET.Element) -> OrderFacts:
    document_date: date | None = None
    for dtm in orders.iter("DTM"):
        cmp1 = dtm.find("cmp01")
        if cmp1 is None:
            continue
        if _text(cmp1.find("e01_2005")) == "137":
            document_date = _parse_edifact_date(_text(cmp1.find("e02_2380")))
            if document_date:
                break

    sca_gln, sca_name = _nad_party(orders, "BY")
    supplier_gln, supplier_name = _nad_party(orders, "SU")

    lines: list[OrderLineFact] = []
    for g25 in orders.iter("g025"):
        lin = g25.find("LIN")
        line_no = 0
        if lin is not None:
            raw_no = _text(lin.find("e01_1082"))
            if raw_no and raw_no.isdigit():
                line_no = int(raw_no)
        cmp1 = lin.find("cmp01") if lin is not None else None
        gtin = _text(cmp1.find("e01_7140")) if cmp1 is not None else None

        description: str | None = None
        imd = g25.find("IMD")
        if imd is not None:
            imd_cmp = imd.find("cmp01")
            if imd_cmp is not None:
                description = _text(imd_cmp.find("e04_7008"))

        qty: str | None = None
        qty_el = g25.find("QTY")
        if qty_el is not None:
            qty_cmp = qty_el.find("cmp01")
            if qty_cmp is not None:
                qty = _text(qty_cmp.find("e02_6060"))

        price_amount: str | None = None
        for g28 in g25.iter("g028"):
            pri = g28.find("PRI")
            if pri is None:
                continue
            pri_cmp = pri.find("cmp01")
            if pri_cmp is not None:
                price_amount = _text(pri_cmp.find("e02_5118"))
                break

        lines.append(
            OrderLineFact(
                line_no=line_no,
                gtin=gtin,
                description=description,
                qty=qty,
                price_amount=price_amount,
            )
        )

    return OrderFacts(
        document_date=document_date,
        sca_gln=sca_gln,
        sca_name=sca_name,
        supplier_gln=supplier_gln,
        supplier_name=supplier_name,
        lines=lines,
    )
