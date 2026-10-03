"""AI trade assistant (Claude) with an offline knowledge-base fallback."""

from pydantic import BaseModel, Field

from ..models import Shipment
from . import ai

SYSTEM = """You are TradeFlow AI, an expert assistant for importers, exporters, freight
forwarders and customs brokers. You help with Incoterms 2020, HS classification,
customs documentation, duties and taxes, trade compliance (sanctions, export
controls), shipping modes and logistics planning.

Be concise and practical: lead with the answer, then the steps or documents
needed. When a question depends on the specific country's rules, say which
authority decides (e.g. CBP, HMRC, CBIC, EU customs) and what to verify. Never
present an estimate as a binding ruling; recommend a binding tariff ruling or a
licensed broker for high-value or ambiguous cases."""

KB = {
    # Checked in order: more specific topics first.
    ("customs value", "duty", "landed", "tax", "vat", "gst"): (
        "Landed cost = goods value + freight + insurance + duty + fees + import VAT/GST. "
        "Duty is charged on the customs value (CIF in most countries, FOB in the US, Canada "
        "and Australia). VAT/GST is usually charged on customs value plus duty. Use the "
        "**Duty Calculator** for an estimate."
    ),
    ("incoterm", "fob", "cif", "exw", "ddp", "dap"): (
        "**Incoterms 2020 quick guide**\n"
        "- **EXW** – buyer handles everything from seller's premises, incl. export clearance.\n"
        "- **FCA** – seller clears export and hands goods to buyer's carrier (best for containers).\n"
        "- **FOB** – seller loads on board at the port of shipment (sea only). Risk passes on board.\n"
        "- **CFR / CIF** – seller pays main freight (CIF adds minimum insurance); risk passes on board.\n"
        "- **DAP** – seller delivers to named destination, buyer clears import and pays duties.\n"
        "- **DDP** – seller handles everything incl. import duties and taxes.\n\n"
        "Tip: for containerised cargo, prefer FCA/CPT/CIP over FOB/CFR/CIF."
    ),
    ("document", "paperwork", "docs"): (
        "**Core documents for an international shipment**\n"
        "1. Commercial invoice (value, HS codes, Incoterm, origin)\n"
        "2. Packing list (weights, dimensions, marks)\n"
        "3. Bill of lading / air waybill (contract of carriage)\n"
        "4. Certificate of origin (required to claim FTA preference)\n"
        "5. Import/export declaration filed by the broker\n"
        "6. Licences or permits for controlled goods (e.g. dual-use, pharma, food)\n\n"
        "Generate the first three from any shipment's **Documents** tab."
    ),
    ("hs", "classif", "tariff code"): (
        "HS codes are classified with the General Rules of Interpretation: GRI 1 (heading "
        "text and notes) decides most cases; GRI 3 handles mixtures and sets (essential "
        "character). The first 6 digits are global; countries add digits (US HTS 10, EU CN 8). "
        "Use the **HS Classifier** page, then confirm the national tariff line."
    ),
    ("sanction", "denied", "embargo", "export control", "dual-use"): (
        "Screen every party (buyer, consignee, end user, banks) against sanctions and "
        "denied-party lists before shipping and again before payment. Check whether the goods "
        "are dual-use (e.g. EU Annex I / US CCL) and whether the destination is embargoed. "
        "The **Compliance** page runs an indicative screen."
    ),
}


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    shipment_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    engine: str


def shipment_context(s: Shipment) -> str:
    items = "; ".join(f"{i.description} (HS {i.hs_code or '?'}, {i.quantity:g} × {i.unit_value:,.2f})" for i in s.items)
    return (
        f"Linked shipment {s.reference}: {s.direction.value} by {s.mode.value}, "
        f"{s.origin_country}→{s.destination_country}, Incoterm {s.incoterm.value}, status {s.status.value}, "
        f"exporter {s.exporter_name}, importer {s.importer_name}, ETA {s.eta or 'n/a'}. Items: {items or 'none'}."
    )


def fallback_reply(question: str) -> str:
    q = question.lower()
    for keys, answer in KB.items():
        if any(k in q for k in keys):
            return answer
    return (
        "I can help with Incoterms, documents, HS classification, duties and compliance. "
        "Try asking *“Which Incoterm should I use for a container from Shanghai?”* or "
        "*“What documents do I need to export to the EU?”*\n\n"
        "_Running in offline mode — set `ANTHROPIC_API_KEY` for full AI answers._"
    )


def reply(req: ChatRequest, shipment: Shipment | None) -> ChatResponse:
    messages = [m.model_dump() for m in req.messages]
    system = SYSTEM + (f"\n\n{shipment_context(shipment)}" if shipment else "")
    text = ai.chat(system, messages)
    if text:
        return ChatResponse(reply=text, engine="claude")
    return ChatResponse(reply=fallback_reply(req.messages[-1].content), engine="offline")
