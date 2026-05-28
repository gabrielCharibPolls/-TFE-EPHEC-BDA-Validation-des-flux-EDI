from __future__ import annotations

import xml.etree.ElementTree as ET

from .models import Violation

# Dix règles métier (contrat TFE) — identifiants stables pour logs / PostgreSQL / Qlik


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    s = el.text.strip()
    return s if s else None


def _first_cmp_text(parent: ET.Element, tag: str, child_tag: str) -> str | None:
    node = parent.find(tag)
    if node is None:
        return None
    return _text(node.find(child_tag))


def rule_r01_envelope_and_orders(root: ET.Element) -> list[Violation]:
    if root.tag != "Envelope":
        return [Violation("R01", "La racine doit être <Envelope>.")]
    orders = root.find("Body")
    if orders is None:
        return [Violation("R01", "Élément <Body> manquant.")]
    ord_el = orders.find("ORDERS")
    if ord_el is None:
        return [Violation("R01", "Élément <Body><ORDERS> manquant.")]
    return []


def rule_r02_unb_mandatory(orders: ET.Element) -> list[Violation]:
    unb = orders.find("UNB")
    if unb is None:
        return [Violation("R02", "Segment UNB (en-tête d'échange) manquant.")]
    out: list[Violation] = []
    if _first_cmp_text(unb, "cmp02", "e01_0004") is None:
        out.append(Violation("R02", "UNB : cmp02/e01_0004 (émetteur) manquant ou vide."))
    if _first_cmp_text(unb, "cmp03", "e01_0010") is None:
        out.append(Violation("R02", "UNB : cmp03/e01_0010 (destinataire) manquant ou vide."))
    if _text(unb.find("e01_0020")) is None:
        out.append(Violation("R02", "UNB : e01_0020 (référence contrôle échange) manquant ou vide."))
    return out


def rule_r03_unh_orders_message(orders: ET.Element) -> list[Violation]:
    unh = orders.find("UNH")
    if unh is None:
        return [Violation("R03", "Segment UNH (en-tête message) manquant.")]
    cmp1 = unh.find("cmp01")
    if cmp1 is None:
        return [Violation("R03", "UNH : cmp01 manquant.")]
    t = _text(cmp1.find("e01_0065"))
    ver = _text(cmp1.find("e03_0054"))
    if t != "ORDERS":
        return [Violation("R03", f"UNH : type message attendu ORDERS, obtenu {t!r}.")]
    if ver != "96A":
        return [Violation("R03", f"UNH : version EDIFACT attendue 96A, obtenue {ver!r}.")]
    return []


def rule_r04_bgm_matches_unh(orders: ET.Element) -> list[Violation]:
    unh = orders.find("UNH")
    bgm = orders.find("BGM")
    if bgm is None:
        return [Violation("R04", "Segment BGM manquant.")]
    if unh is None:
        return [Violation("R04", "Impossible de comparer BGM à UNH : UNH manquant.")]
    unh_ref = _text(unh.find("e01_0062"))
    bgm_ref = _text(bgm.find("e01_1004"))
    if not unh_ref or not bgm_ref:
        return [Violation("R04", "BGM/e01_1004 ou UNH/e01_0062 manquant pour contrôle de cohérence.")]
    if unh_ref != bgm_ref:
        return [
            Violation(
                "R04",
                f"Référence document : UNH/e01_0062={unh_ref!r} ≠ BGM/e01_1004={bgm_ref!r}.",
            )
        ]
    return []


def rule_r05_dtm_document_date(orders: ET.Element) -> list[Violation]:
    for dtm in orders.iter("DTM"):
        cmp1 = dtm.find("cmp01")
        if cmp1 is None:
            continue
        q = _text(cmp1.find("e01_2005"))
        v = _text(cmp1.find("e02_2380"))
        if q == "137" and v:
            return []
    return [Violation("R05", "Aucun segment DTM avec qualificateur 137 (date document) et valeur renseignée.")]


def rule_r06_nad_by(orders: ET.Element) -> list[Violation]:
    for nad in orders.iter("NAD"):
        if _text(nad.find("e01_3035")) == "BY":
            cmp1 = nad.find("cmp01")
            gln = _text(cmp1.find("e01_3039")) if cmp1 is not None else None
            if gln:
                return []
            return [Violation("R06", "NAD BY présent mais cmp01/e01_3039 (GLN acheteur) manquant ou vide.")]
    return [Violation("R06", "Aucun segment NAD avec qualificateur BY (acheteur).")]


def rule_r07_nad_su(orders: ET.Element) -> list[Violation]:
    for nad in orders.iter("NAD"):
        if _text(nad.find("e01_3035")) == "SU":
            cmp1 = nad.find("cmp01")
            cmp3 = nad.find("cmp03")
            gln = _text(cmp1.find("e01_3039")) if cmp1 is not None else None
            name = _text(cmp3.find("e01_3036")) if cmp3 is not None else None
            if gln and name:
                return []
            missing = []
            if not gln:
                missing.append("GLN (cmp01/e01_3039)")
            if not name:
                missing.append("nom (cmp03/e01_3036)")
            return [Violation("R07", f"NAD SU incomplet : {', '.join(missing)} manquant(s).")]
    return [Violation("R07", "Aucun segment NAD avec qualificateur SU (fournisseur).")]


def rule_r08_unb_unz_control_ref(orders: ET.Element) -> list[Violation]:
    unb = orders.find("UNB")
    unz = orders.find("UNZ")
    if unb is None:
        return []
    if unz is None:
        return [Violation("R08", "Segment UNZ (fin d'échange) manquant.")]
    a = _text(unb.find("e01_0020"))
    b = _text(unz.find("e02_0020"))
    if not a or not b:
        return [Violation("R08", "UNB/e01_0020 ou UNZ/e02_0020 manquant pour contrôle de cohérence.")]
    if a != b:
        return [Violation("R08", f"Référence échange : UNB/e01_0020={a!r} ≠ UNZ/e02_0020={b!r}.")]
    return []


def rule_r09_lin_gtin(orders: ET.Element) -> list[Violation]:
    g25_blocks = list(orders.iter("g025"))
    if not g25_blocks:
        return [Violation("R09", "Aucune ligne de commande (g025) trouvée.")]
    violations: list[Violation] = []
    for g25 in g25_blocks:
        lin = g25.find("LIN")
        if lin is None:
            violations.append(Violation("R09", "Ligne (g025) sans segment LIN."))
            continue
        cmp1 = lin.find("cmp01")
        gtin = _text(cmp1.find("e01_7140")) if cmp1 is not None else None
        if not gtin or not gtin.isdigit():
            violations.append(Violation("R09", f"LIN : GTIN e01_7140 manquant ou non numérique ({gtin!r})."))
            continue
        if not (8 <= len(gtin) <= 14):
            violations.append(
                Violation("R09", f"LIN : longueur GTIN attendue entre 8 et 14, obtenu {len(gtin)} ({gtin}).")
            )
    return violations


def rule_r10_pri_amount(orders: ET.Element) -> list[Violation]:
    violations: list[Violation] = []
    for pri in orders.iter("PRI"):
        cmp1 = pri.find("cmp01")
        price_el = cmp1.find("e02_5118") if cmp1 is not None else None
        raw = _text(price_el)
        if raw is None:
            violations.append(Violation("R10", "PRI : montant e02_5118 manquant."))
            continue
        try:
            val = float(raw.replace(",", "."))
        except ValueError:
            violations.append(Violation("R10", f"PRI : montant e02_5118 non numérique ({raw!r})."))
            continue
        if val < 0:
            violations.append(Violation("R10", f"PRI : montant ne peut être négatif ({raw})."))
    return violations


ALL_RULES = [
    ("R01", lambda root, orders: rule_r01_envelope_and_orders(root)),
    ("R02", lambda root, orders: rule_r02_unb_mandatory(orders) if orders is not None else []),
    ("R03", lambda root, orders: rule_r03_unh_orders_message(orders) if orders is not None else []),
    ("R04", lambda root, orders: rule_r04_bgm_matches_unh(orders) if orders is not None else []),
    ("R05", lambda root, orders: rule_r05_dtm_document_date(orders) if orders is not None else []),
    ("R06", lambda root, orders: rule_r06_nad_by(orders) if orders is not None else []),
    ("R07", lambda root, orders: rule_r07_nad_su(orders) if orders is not None else []),
    ("R08", lambda root, orders: rule_r08_unb_unz_control_ref(orders) if orders is not None else []),
    ("R09", lambda root, orders: rule_r09_lin_gtin(orders) if orders is not None else []),
    ("R10", lambda root, orders: rule_r10_pri_amount(orders) if orders is not None else []),
]


def run_all_rules(root: ET.Element, orders: ET.Element | None) -> list[Violation]:
    all_v: list[Violation] = []
    for _rid, fn in ALL_RULES:
        all_v.extend(fn(root, orders))
    return all_v
