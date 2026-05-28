from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

ENCODING = "iso-8859-15"

SCAS = (
    ("3025690000106", "SOCAMAINE", "CHAMPAGNE", "72470"),
    ("3025690000205", "LECASUD", "MARSEILLE", "13015"),
    ("3025690000304", "SCARMOR", "RENNES", "35000"),
    ("3025690000403", "SCAPNOR", "LILLE", "59000"),
)

PRODUCTS = (
    ("3599741005964", "2PAVES SAUMON ATLANT.ASC,F,250", "5.246"),
    ("3599741001911", "4 DOS CABILLAUD MSC,FINDUS,440", "6.191"),
    ("3599741001898", "4 FILETS CABILLAUD MSC,FIN,400", "5.085"),
    ("3599741004189", "BEIGNETS A LA ROMAINE,,490G", "2.201"),
    ("3599741003380", "FILET FACON FISH/CHIPS X4,400G", "2.241"),
)

SUPPLIER_GLN = "5488888006645"
SUPPLIER_NAME = "SCABEL"

# Défauts injectés → règles R01–R10 attendues
DEFECTS: dict[str, str] = {
    "R04": "BGM référence ≠ UNH",
    "R05": "Date document DTM 137 absente",
    "R06": "GLN acheteur (BY) manquant",
    "R07": "Nom fournisseur (SU) manquant",
    "R08": "Référence UNB ≠ UNZ",
    "R09": "GTIN invalide sur une ligne",
    "R10": "Prix négatif sur une ligne",
    "R03": "Type message ≠ ORDERS",
    "PARSE": "XML mal formé (balise tronquée)",
}


@dataclass
class GeneratedOrder:
    filename: str
    content: bytes
    defect: str | None  # None = fichier valide volontaire


def _edifact_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def _line_block(
    line_no: int,
    gtin: str,
    label: str,
    price: str,
    qty: str = "384",
) -> str:
    return (
        f"<g025><LIN><e01_1082>{line_no}</e01_1082>"
        f"<cmp01><e01_7140>{gtin}</e01_7140><e02_7143>EN</e02_7143></cmp01></LIN>"
        f"<IMD><e01_7077>E</e01_7077><cmp01><e04_7008>{label}</e04_7008></cmp01></IMD>"
        f"<QTY><cmp01><e01_6063>21</e01_6063><e02_6060>{qty}</e02_6060>"
        f"<e03_6411>PCE</e03_6411></cmp01></QTY>"
        f"<g028><PRI><cmp01><e01_5125>AAA</e01_5125><e02_5118>{price}</e02_5118>"
        f"<e04_5387>NTP</e04_5387></cmp01></PRI></g028></g025>"
    )


def _build_valid_order(
    *,
    interchange_ref: str,
    msg_ref: str,
    doc_date: date,
    buyer_gln: str,
    buyer_name: str,
    buyer_city: str,
    buyer_postal: str,
    lines: list[tuple[str, str, str]],
    message_type: str = "ORDERS",
    message_version: str = "96A",
    include_dtm137: bool = True,
    buyer_gln_ok: bool = True,
    supplier_name_ok: bool = True,
    unz_ref: str | None = None,
) -> str:
    unz = unz_ref if unz_ref is not None else interchange_ref
    bgm_ref = msg_ref
    dtm137 = ""
    if include_dtm137:
        dtm137 = (
            f"<DTM><cmp01><e01_2005>137</e01_2005>"
            f"<e02_2380>{_edifact_date(doc_date)}</e02_2380><e03_2379>102</e03_2379></cmp01></DTM>"
        )
    by_gln = buyer_gln if buyer_gln_ok else ""
    su_name = SUPPLIER_NAME if supplier_name_ok else ""
    line_xml = "".join(_line_block(i + 1, g, lbl, p) for i, (g, lbl, p) in enumerate(lines))
    sent = datetime.combine(doc_date, datetime.min.time()).strftime("%Y-%m-%dT%H:%M:%S+01:00")

    return (
        '<?xml version="1.0" encoding="ISO-8859-15"?>'
        '<Envelope xmlns:env="http://www.intentia.com/MBM_Envelope_1">'
        "<Header><delivery><to><address>5488888006645</address></to>"
        f"<from><address>{buyer_gln}</address></from></delivery>"
        f"<properties><sentAt>{sent}</sentAt></properties></Header>"
        "<Body><ORDERS>"
        f"<UNB><cmp02><e01_0004>3025680000215</e01_0004></cmp02>"
        f"<cmp03><e01_0010>5488888006645</e01_0010></cmp03>"
        f"<cmp04><e01_0017>{_edifact_date(doc_date)}</e01_0017></cmp04>"
        f"<e01_0020>{interchange_ref}</e01_0020></UNB>"
        f"<UNH><e01_0062>{msg_ref}</e01_0062><cmp01>"
        f"<e01_0065>{message_type}</e01_0065><e03_0054>{message_version}</e03_0054>"
        "</cmp01></UNH>"
        f"<BGM><e01_1004>{bgm_ref}</e01_1004></BGM>"
        f"{dtm137}"
        f"<g002><NAD><e01_3035>BY</e01_3035><cmp01><e01_3039>{by_gln}</e01_3039></cmp01>"
        f"<cmp03><e01_3036>{buyer_name}</e01_3036></cmp03>"
        f"<e02_3164>{buyer_city}</e02_3164><e04_3251>{buyer_postal}</e04_3251></NAD></g002>"
        f"<g002><NAD><e01_3035>SU</e01_3035><cmp01><e01_3039>{SUPPLIER_GLN}</e01_3039></cmp01>"
        f"<cmp03><e01_3036>{su_name}</e01_3036></cmp03></NAD></g002>"
        f"{line_xml}"
        f"<UNZ><e01_0036>1</e01_0036><e02_0020>{unz}</e02_0020></UNZ>"
        "</ORDERS></Body></Envelope>"
    )


def _apply_defect(xml: str, defect: str, interchange_ref: str, msg_ref: str) -> str:
    if defect == "R04":
        return xml.replace(f"<e01_1004>{msg_ref}</e01_1004>", f"<e01_1004>{msg_ref}X</e01_1004>", 1)
    if defect == "R05":
        return xml.replace(
            "<DTM><cmp01><e01_2005>137</e01_2005>", "<DTM><cmp01><e01_2005>2</e01_2005>", 1
        )
    if defect == "R06":
        return _build_valid_order(
            interchange_ref=interchange_ref,
            msg_ref=msg_ref,
            doc_date=date.today(),
            buyer_gln=SCAS[0][0],
            buyer_name=SCAS[0][1],
            buyer_city=SCAS[0][2],
            buyer_postal=SCAS[0][3],
            lines=[PRODUCTS[0]],
            buyer_gln_ok=False,
        )
    if defect == "R07":
        return _build_valid_order(
            interchange_ref=interchange_ref,
            msg_ref=msg_ref,
            doc_date=date.today(),
            buyer_gln=SCAS[0][0],
            buyer_name=SCAS[0][1],
            buyer_city=SCAS[0][2],
            buyer_postal=SCAS[0][3],
            lines=[PRODUCTS[0]],
            supplier_name_ok=False,
        )
    if defect == "R08":
        return _build_valid_order(
            interchange_ref=interchange_ref,
            msg_ref=msg_ref,
            doc_date=date.today(),
            buyer_gln=SCAS[0][0],
            buyer_name=SCAS[0][1],
            buyer_city=SCAS[0][2],
            buyer_postal=SCAS[0][3],
            lines=[PRODUCTS[0]],
            unz_ref=f"{interchange_ref}999",
        )
    if defect == "R09":
        bad = _line_block(1, "ABC", "PRODUIT GTIN INVALIDE", "1.0")
        return xml.replace(_line_block(1, PRODUCTS[0][0], PRODUCTS[0][1], PRODUCTS[0][2]), bad, 1)
    if defect == "R10":
        bad = _line_block(1, PRODUCTS[0][0], PRODUCTS[0][1], "-1.5")
        return xml.replace(_line_block(1, PRODUCTS[0][0], PRODUCTS[0][1], PRODUCTS[0][2]), bad, 1)
    if defect == "R03":
        return xml.replace("<e01_0065>ORDERS</e01_0065>", "<e01_0065>INVOIC</e01_0065>", 1)
    if defect == "PARSE":
        return xml[:-20]  # XML tronqué
    return xml


def generate_order(
    seq: int,
    *,
    doc_date: date | None = None,
    defect: str | None = None,
    rng: random.Random | None = None,
) -> GeneratedOrder:
    r = rng or random.Random()
    doc_date = doc_date or date.today()
    buyer = r.choice(SCAS)
    n_lines = r.randint(1, min(3, len(PRODUCTS)))
    lines = r.sample(PRODUCTS, n_lines)
    interchange_ref = str(900_000_000 + seq)
    msg_ref = str(10_000_000 + seq)
    filename = f"{interchange_ref}_{msg_ref}.ORO"

    xml = _build_valid_order(
        interchange_ref=interchange_ref,
        msg_ref=msg_ref,
        doc_date=doc_date,
        buyer_gln=buyer[0],
        buyer_name=buyer[1],
        buyer_city=buyer[2],
        buyer_postal=buyer[3],
        lines=lines,
    )
    if defect:
        xml = _apply_defect(xml, defect, interchange_ref, msg_ref)

    return GeneratedOrder(filename, xml.encode(ENCODING), defect)


def pick_defects(count: int, error_rate: float, rng: random.Random) -> list[str | None]:
    n_errors = round(count * error_rate)
    n_errors = max(0, min(count, n_errors))
    keys = list(DEFECTS.keys())
    error_list = rng.choices(keys, k=n_errors) if n_errors else []
    defects = [None] * (count - n_errors) + error_list
    rng.shuffle(defects)
    return defects


def generate_batch(
    count: int,
    *,
    error_rate: float = 0.10,
    start_seq: int = 1,
    seed: int | None = None,
) -> list[GeneratedOrder]:
    rng = random.Random(seed)
    defects = pick_defects(count, error_rate, rng)
    return [
        generate_order(start_seq + i, defect=defects[i], rng=rng)
        for i in range(count)
    ]
