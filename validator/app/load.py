from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

ENCODING = "iso-8859-15"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_orders(path: Path) -> tuple[ET.ElementTree | None, str | None]:
    """
    Retourne (tree, None) si XML bien formé, sinon (None, message_erreur).
    """
    try:
        parser = ET.XMLParser(encoding=ENCODING)
        tree = ET.parse(path, parser=parser)
        return tree, None
    except ET.ParseError as e:
        return None, str(e)


def orders_root(root: ET.Element) -> ET.Element | None:
    body = root.find("Body")
    if body is None:
        return None
    return body.find("ORDERS")
