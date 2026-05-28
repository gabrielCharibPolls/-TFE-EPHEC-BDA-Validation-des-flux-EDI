from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


@pytest.fixture
def minimal_orders_xml() -> ET.Element:
    xml = """<?xml version="1.0" encoding="ISO-8859-15"?>
<Envelope>
  <Body>
    <ORDERS>
      <UNB>
        <cmp02><e01_0004>SCABEL</e01_0004></cmp02>
        <cmp03><e01_0010>PARTNER</e01_0010></cmp03>
        <e01_0020>REF001</e01_0020>
      </UNB>
      <UNH><e01_0062>DOC001</e01_0062><cmp01><e01_0065>ORDERS</e01_0065><e03_0054>96A</e03_0054></cmp01></UNH>
      <BGM><e01_1004>DOC001</e01_1004></BGM>
      <DTM><cmp01><e01_2005>137</e01_2005><e02_2380>20260101</e02_2380></cmp01></DTM>
      <NAD><e01_3035>BY</e01_3035><cmp01><e01_3039>1234567890123</e01_3039></cmp01></NAD>
      <NAD><e01_3035>SU</e01_3035><cmp01><e01_3039>9876543210987</e01_3039></cmp01><cmp03><e01_3036>FOURNISSEUR TEST</e01_3036></cmp03></NAD>
      <g025>
        <LIN><cmp01><e01_7140>5410041000000</e01_7140></cmp01></LIN>
      </g025>
      <g028><PRI><cmp01><e02_5118>12.50</e02_5118></cmp01></PRI></g028>
      <UNZ><e02_0020>REF001</e02_0020></UNZ>
    </ORDERS>
  </Body>
</Envelope>"""
    return ET.fromstring(xml)


@pytest.fixture
def tmp_oro_file(tmp_path: Path, minimal_orders_xml: ET.Element) -> Path:
    p = tmp_path / "test.ORO"
    tree = ET.ElementTree(minimal_orders_xml)
    tree.write(p, encoding="ISO-8859-15", xml_declaration=True)
    return p
