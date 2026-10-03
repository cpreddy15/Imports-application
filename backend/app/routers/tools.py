from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..data.tariffs import HS_CODES
from ..db import get_session
from ..models import Shipment
from ..services import ai, assistant, classifier, compliance, documents, duty

router = APIRouter(prefix="/api", tags=["ai & tools"])


@router.get("/health")
def health():
    return {"status": "ok", "ai_enabled": ai.enabled()}


@router.post("/classify", response_model=classifier.ClassifyResponse)
def classify(req: classifier.ClassifyRequest):
    return classifier.classify(req)


@router.get("/hs-codes")
def hs_codes(q: str = ""):
    q = q.lower()
    return [
        {"code": h.code, "description": h.description, "chapter": h.chapter}
        for h in HS_CODES
        if not q or q in h.code or q in h.description.lower() or any(q in k for k in h.keywords)
    ]


@router.post("/duty/estimate", response_model=duty.DutyResponse)
def estimate_duty(req: duty.DutyRequest):
    return duty.estimate(req)


@router.post("/compliance/screen", response_model=compliance.ScreenResponse)
def screen(req: compliance.ScreenRequest):
    return compliance.screen(req)


class ExtractRequest(BaseModel):
    text: str = Field(min_length=10, max_length=50000)


@router.post("/documents/extract", response_model=documents.ExtractedInvoice)
def extract(req: ExtractRequest):
    return documents.extract_invoice(req.text)


@router.post("/assistant/chat", response_model=assistant.ChatResponse)
def chat(req: assistant.ChatRequest, session: Session = Depends(get_session)):
    shipment = session.get(Shipment, req.shipment_id) if req.shipment_id else None
    return assistant.reply(req, shipment)
