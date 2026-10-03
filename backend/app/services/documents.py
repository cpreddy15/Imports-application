"""Trade document generation (printable HTML) and AI invoice extraction."""

import html
import re
from datetime import date

from pydantic import BaseModel

from ..models import Shipment
from . import ai

DOC_TYPES = {
    "commercial-invoice": "Commercial Invoice",
    "packing-list": "Packing List",
    "certificate-of-origin": "Certificate of Origin",
}

_CSS = """
body{font-family:Inter,Arial,sans-serif;color:#0f172a;margin:40px;font-size:13px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:-.02em}
.muted{color:#64748b}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:20px 0}
.box{border:1px solid #e2e8f0;border-radius:4px;padding:12px}
.box h3{margin:0 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#64748b}
table{width:100%;border-collapse:collapse;margin-top:16px}
th,td{border-bottom:1px solid #e2e8f0;padding:8px;text-align:left}
th{background:#f8fafc;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#475569}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.total td{font-weight:600;border-top:2px solid #0f172a}
.sign{margin-top:48px;display:flex;justify-content:space-between}
.sign div{border-top:1px solid #94a3b8;width:40%;padding-top:6px}
@media print{body{margin:16mm}}
"""


def _e(v: object) -> str:
    return html.escape("" if v is None else str(v))


def render(shipment: Shipment, doc_type: str) -> str:
    title = DOC_TYPES[doc_type]
    s = shipment
    head = f"""<!doctype html><html><head><meta charset="utf-8"><title>{title} {_e(s.reference)}</title>
<style>{_CSS}</style></head><body>
<h1>{title}</h1><div class="muted">No. {_e(s.reference)} · Date {date.today().isoformat()}</div>
<div class="grid">
<div class="box"><h3>Exporter / Seller</h3><b>{_e(s.exporter_name)}</b><br>{_e(s.exporter_address)}<br>{_e(s.origin_country)}</div>
<div class="box"><h3>Importer / Consignee</h3><b>{_e(s.importer_name)}</b><br>{_e(s.importer_address)}<br>{_e(s.destination_country)}</div>
<div class="box"><h3>Shipment</h3>Mode: {_e(s.mode.value.title())}<br>Carrier: {_e(s.carrier or '—')}<br>
Route: {_e(s.origin_port or s.origin_country)} → {_e(s.destination_port or s.destination_country)}</div>
<div class="box"><h3>Terms</h3>Incoterm: {_e(s.incoterm.value)}<br>Currency: {_e(s.currency)}<br>ETD: {_e(s.etd or '—')} · ETA: {_e(s.eta or '—')}</div>
</div>"""

    if doc_type == "commercial-invoice":
        rows = "".join(
            f"<tr><td>{i}</td><td>{_e(it.description)}</td><td>{_e(it.hs_code or '—')}</td>"
            f"<td>{_e(it.origin_country or s.origin_country)}</td><td class='num'>{it.quantity:g} {_e(it.unit)}</td>"
            f"<td class='num'>{it.unit_value:,.2f}</td><td class='num'>{it.quantity * it.unit_value:,.2f}</td></tr>"
            for i, it in enumerate(s.items, 1)
        )
        goods = sum(it.quantity * it.unit_value for it in s.items)
        body = f"""<table><tr><th>#</th><th>Description</th><th>HS code</th><th>Origin</th><th class='num'>Qty</th>
<th class='num'>Unit price</th><th class='num'>Amount</th></tr>{rows}
<tr><td colspan=6 class='num'>Goods total</td><td class='num'>{goods:,.2f}</td></tr>
<tr><td colspan=6 class='num'>Freight</td><td class='num'>{s.freight_cost:,.2f}</td></tr>
<tr><td colspan=6 class='num'>Insurance</td><td class='num'>{s.insurance_cost:,.2f}</td></tr>
<tr class='total'><td colspan=6 class='num'>Invoice total ({_e(s.currency)})</td>
<td class='num'>{goods + s.freight_cost + s.insurance_cost:,.2f}</td></tr></table>
<p class="muted">We certify that this invoice is true and correct and that the goods originate as stated.</p>"""
    elif doc_type == "packing-list":
        rows = "".join(
            f"<tr><td>{i}</td><td>{_e(it.description)}</td><td>{_e(it.hs_code or '—')}</td>"
            f"<td class='num'>{it.quantity:g} {_e(it.unit)}</td><td class='num'>{it.weight_kg:,.1f}</td></tr>"
            for i, it in enumerate(s.items, 1)
        )
        weight = sum(it.weight_kg for it in s.items)
        body = f"""<table><tr><th>#</th><th>Description</th><th>HS code</th><th class='num'>Quantity</th>
<th class='num'>Gross weight (kg)</th></tr>{rows}
<tr class='total'><td colspan=4 class='num'>Total gross weight</td><td class='num'>{weight:,.1f}</td></tr></table>"""
    else:
        rows = "".join(
            f"<tr><td>{i}</td><td>{_e(it.description)}</td><td>{_e(it.hs_code or '—')}</td>"
            f"<td>{_e(it.origin_country or s.origin_country)}</td></tr>"
            for i, it in enumerate(s.items, 1)
        )
        body = f"""<table><tr><th>#</th><th>Description of goods</th><th>HS code</th><th>Country of origin</th></tr>{rows}</table>
<p>The undersigned hereby declares that the goods described above originate in
<b>{_e(s.origin_country)}</b> and comply with the origin requirements for export to <b>{_e(s.destination_country)}</b>.</p>"""

    return head + body + """<div class="sign"><div>Authorised signature</div><div>Name, title &amp; company stamp</div></div>
</body></html>"""


# ---- AI extraction ---------------------------------------------------------

class ExtractedItem(BaseModel):
    description: str
    quantity: float = 1
    unit_value: float = 0
    hs_code: str | None = None


class ExtractedInvoice(BaseModel):
    exporter_name: str | None = None
    importer_name: str | None = None
    origin_country: str | None = None
    destination_country: str | None = None
    incoterm: str | None = None
    currency: str | None = None
    items: list[ExtractedItem] = []
    engine: str


_EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "exporter_name": {"type": ["string", "null"]},
        "importer_name": {"type": ["string", "null"]},
        "origin_country": {"type": ["string", "null"], "description": "ISO alpha-2"},
        "destination_country": {"type": ["string", "null"], "description": "ISO alpha-2"},
        "incoterm": {"type": ["string", "null"]},
        "currency": {"type": ["string", "null"], "description": "ISO 4217"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_value": {"type": "number"},
                    "hs_code": {"type": ["string", "null"]},
                },
                "required": ["description", "quantity", "unit_value", "hs_code"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["exporter_name", "importer_name", "origin_country", "destination_country",
                 "incoterm", "currency", "items"],
    "additionalProperties": False,
}

_INCOTERMS = r"\b(EXW|FCA|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b"
_CURRENCIES = r"\b(USD|EUR|GBP|INR|CNY|JPY|AUD|CAD|AED|SGD)\b"


def _regex_extract(text: str) -> ExtractedInvoice:
    def field(*labels: str) -> str | None:
        for label in labels:
            m = re.search(rf"{label}\s*[:\-]\s*(.+)", text, re.I)
            if m:
                return m.group(1).strip()
        return None

    items = []
    # Lines like: "Cotton T-shirts  500 pcs  @ 4.20" or "Cotton T-shirts | 500 | 4.20"
    for line in text.splitlines():
        m = re.match(r"\s*(?:\d+[.)]\s*)?([A-Za-z][^|@\d]{2,}?)\s*[|,\s]\s*(\d+(?:\.\d+)?)\s*(?:pcs|units|kg|cartons|sets)?\s*[|,@x\s]\s*\$?(\d+(?:\.\d+)?)\s*$", line)
        if m:
            items.append(ExtractedItem(description=m.group(1).strip(" -:"), quantity=float(m.group(2)),
                                       unit_value=float(m.group(3))))
    inco = re.search(_INCOTERMS, text)
    cur = re.search(_CURRENCIES, text)
    return ExtractedInvoice(
        exporter_name=field("exporter", "seller", "shipper"),
        importer_name=field("importer", "buyer", "consignee"),
        origin_country=(field("origin", "country of origin") or "")[:2].upper() or None,
        destination_country=(field("destination") or "")[:2].upper() or None,
        incoterm=inco.group(1) if inco else None,
        currency=cur.group(1) if cur else None,
        items=items,
        engine="regex",
    )


def extract_invoice(text: str) -> ExtractedInvoice:
    result = ai.structured(
        "You extract structured data from commercial invoices, proforma invoices and "
        "purchase orders for customs filing. Use ISO country and currency codes. Use null "
        "for anything the document does not state; never invent values.",
        text,
        _EXTRACT_SCHEMA,
        effort="low",
    )
    if result:
        return ExtractedInvoice(**result, engine="claude")
    return _regex_extract(text)
