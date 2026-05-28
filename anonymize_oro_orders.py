#!/usr/bin/env python3
"""
Anonymise les commandes ORDERS au format Envelope Intentia (.ORO) :
- montants de prix (élément e02_5118 dans les segments PRI)
- noms du fournisseur qualifié SU (NAD / cmp03 / e01_3036)

Les originaux dans le dossier d'entrée ne sont pas modifiés ; les fichiers
traités sont écrits dans le dossier de sortie.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ENCODING = "iso-8859-15"
_ENVELOPE_OPEN = re.compile(
    r"<Envelope(\s[^>]*)?>",
    flags=re.DOTALL,
)
_ENVELOPE_REPLACEMENT = (
    '<Envelope xmlns:env="http://www.intentia.com/MBM_Envelope_1" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
)


def _write_oro(tree: ET.ElementTree, dest: Path) -> None:
    """Écrit le XML en ISO-8859-15 et rétablit l’en-tête Envelope Intentia."""
    buf = io.BytesIO()
    tree.write(
        buf,
        encoding=ENCODING.upper(),
        xml_declaration=True,
        short_empty_elements=False,
    )
    text = buf.getvalue().decode(ENCODING)
    fixed = _ENVELOPE_OPEN.sub(_ENVELOPE_REPLACEMENT, text, count=1)
    dest.write_bytes(fixed.encode(ENCODING))


def _iter_oro_files(input_dir: Path) -> list[Path]:
    return sorted(input_dir.glob("*.ORO"))


def _parse_tree(path: Path) -> ET.ElementTree:
    parser = ET.XMLParser(encoding=ENCODING)
    return ET.parse(path, parser=parser)


def _collect_supplier_names(paths: list[Path]) -> dict[str, str]:
    """Construit une table stable nom réel -> pseudonyme FOURNISSEUR_NNN."""
    seen: set[str] = set()
    for path in paths:
        tree = _parse_tree(path)
        for nad in tree.iter("NAD"):
            qual = nad.find("e01_3035")
            if qual is None or (qual.text or "").strip() != "SU":
                continue
            for cmp03 in nad.findall("cmp03"):
                el = cmp03.find("e01_3036")
                if el is not None and el.text and el.text.strip():
                    seen.add(el.text.strip())
    ordered = sorted(seen)
    return {name: f"FOURNISSEUR_{i:03d}" for i, name in enumerate(ordered, start=1)}


def _obfuscate_price(text: str, seed_bytes: bytes, counter: list[int]) -> str:
    """Remplace le montant par une valeur numérique fictive (reproductible)."""
    raw = (text or "").strip().replace(",", ".")
    try:
        value = float(raw)
    except ValueError:
        return text
    counter[0] += 1
    h = hashlib.sha256(seed_bytes + str(counter[0]).encode()).digest()
    # Facteur entre ~0.25 et ~1.75 pour garder un ordre de grandeur plausible
    factor = 0.25 + (int.from_bytes(h[:4], "big") % 15000) / 10000.0
    out = round(value * factor, 3)
    s = f"{out:.3f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _anonymize_tree(
    tree: ET.ElementTree,
    supplier_map: dict[str, str],
    seed_bytes: bytes,
) -> None:
    price_counter = [0]

    for el in tree.iter("e02_5118"):
        if el.text and el.text.strip():
            el.text = _obfuscate_price(el.text, seed_bytes, price_counter)

    for nad in tree.iter("NAD"):
        qual = nad.find("e01_3035")
        if qual is None or (qual.text or "").strip() != "SU":
            continue
        for cmp03 in nad.findall("cmp03"):
            name_el = cmp03.find("e01_3036")
            if name_el is None or not name_el.text or not name_el.text.strip():
                continue
            key = name_el.text.strip()
            if key in supplier_map:
                name_el.text = supplier_map[key]


def process_files(
    input_dir: Path,
    output_dir: Path,
    seed: int,
) -> tuple[int, int]:
    paths = _iter_oro_files(input_dir)
    if not paths:
        return 0, 0

    supplier_map = _collect_supplier_names(paths)
    output_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for path in paths:
        rel_seed = f"{seed}:{path.name}".encode()
        seed_bytes = hashlib.sha256(rel_seed).digest()
        try:
            tree = _parse_tree(path)
            _anonymize_tree(tree, supplier_map, seed_bytes)
            dest = output_dir / path.name
            _write_oro(tree, dest)
            ok += 1
        except ET.ParseError as e:
            print(f"Erreur XML {path.name}: {e}", file=sys.stderr)

    return ok, len(paths)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Anonymise prix (PRI) et noms fournisseur (NAD SU) dans les .ORO"
    )
    p.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("in"),
        help="Dossier contenant les fichiers .ORO (défaut: in)",
    )
    p.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("out_anonymized"),
        help="Dossier de sortie (défaut: out_anonymized)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Graine pour reproductibilité des montants (défaut: 42)",
    )
    args = p.parse_args()

    if not args.input_dir.is_dir():
        print(f"Dossier introuvable: {args.input_dir}", file=sys.stderr)
        return 1

    ok, total = process_files(args.input_dir, args.output_dir, args.seed)
    print(f"Terminé : {ok}/{total} fichier(s) écrit(s) dans {args.output_dir.resolve()}")
    return 0 if ok == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
