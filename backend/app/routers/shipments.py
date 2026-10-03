from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlmodel import Session, col, func, or_, select

from ..db import get_session
from ..models import (
    EventCreate,
    LineItem,
    Shipment,
    ShipmentCreate,
    ShipmentEvent,
    ShipmentRead,
    ShipmentStatus,
    ShipmentSummary,
    ShipmentUpdate,
)
from ..services import compliance, documents, duty

router = APIRouter(prefix="/api/shipments", tags=["shipments"])


def goods_value(s: Shipment) -> float:
    return round(sum(i.quantity * i.unit_value for i in s.items), 2)


def to_read(s: Shipment) -> ShipmentRead:
    data = s.model_dump()
    data["goods_value"] = goods_value(s)
    data["items"] = [{**i.model_dump(), "line_value": round(i.quantity * i.unit_value, 2)} for i in s.items]
    data["events"] = [e.model_dump() for e in s.events]
    return ShipmentRead.model_validate(data)


def to_summary(s: Shipment) -> ShipmentSummary:
    return ShipmentSummary(**s.model_dump(include=set(ShipmentSummary.model_fields) - {"goods_value"}),
                           goods_value=goods_value(s))


def next_reference(session: Session) -> str:
    year = date.today().year
    count = session.exec(select(func.count()).select_from(Shipment)).one()
    ref = f"TF-{year}-{count + 1:04d}"
    while session.exec(select(Shipment).where(Shipment.reference == ref)).first():
        count += 1
        ref = f"TF-{year}-{count + 1:04d}"
    return ref


def get_or_404(session: Session, shipment_id: int) -> Shipment:
    s = session.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Shipment not found")
    return s


@router.get("", response_model=list[ShipmentSummary])
def list_shipments(
    session: Session = Depends(get_session),
    status: ShipmentStatus | None = None,
    direction: str | None = None,
    q: str | None = Query(default=None, max_length=100),
):
    stmt = select(Shipment).order_by(col(Shipment.created_at).desc())
    if status:
        stmt = stmt.where(Shipment.status == status)
    if direction:
        stmt = stmt.where(Shipment.direction == direction)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(col(Shipment.reference).ilike(like), col(Shipment.exporter_name).ilike(like),
                              col(Shipment.importer_name).ilike(like)))
    return [to_summary(s) for s in session.exec(stmt).all()]


@router.post("", response_model=ShipmentRead, status_code=201)
def create_shipment(payload: ShipmentCreate, session: Session = Depends(get_session)):
    data = payload.model_dump(exclude={"items"})
    data["origin_country"] = data["origin_country"].upper()
    data["destination_country"] = data["destination_country"].upper()
    s = Shipment(**data, reference=next_reference(session))
    s.items = [LineItem(**i.model_dump()) for i in payload.items]
    s.events = [ShipmentEvent(status=ShipmentStatus.booked, message="Shipment booked")]
    session.add(s)
    session.commit()
    session.refresh(s)
    return to_read(s)


@router.get("/{shipment_id}", response_model=ShipmentRead)
def get_shipment(shipment_id: int, session: Session = Depends(get_session)):
    return to_read(get_or_404(session, shipment_id))


@router.patch("/{shipment_id}", response_model=ShipmentRead)
def update_shipment(shipment_id: int, payload: ShipmentUpdate, session: Session = Depends(get_session)):
    s = get_or_404(session, shipment_id)
    changes = payload.model_dump(exclude_unset=True)
    new_status = changes.get("status")
    for k, v in changes.items():
        setattr(s, k, v)
    if new_status:
        s.events.append(ShipmentEvent(status=new_status, message=f"Status changed to {new_status.value.replace('_', ' ')}"))
    s.updated_at = datetime.now(timezone.utc)
    session.add(s)
    session.commit()
    session.refresh(s)
    return to_read(s)


@router.delete("/{shipment_id}", status_code=204)
def delete_shipment(shipment_id: int, session: Session = Depends(get_session)):
    session.delete(get_or_404(session, shipment_id))
    session.commit()


@router.post("/{shipment_id}/events", response_model=ShipmentRead, status_code=201)
def add_event(shipment_id: int, payload: EventCreate, session: Session = Depends(get_session)):
    s = get_or_404(session, shipment_id)
    s.events.append(ShipmentEvent(**payload.model_dump()))
    s.status = payload.status
    s.updated_at = datetime.now(timezone.utc)
    session.add(s)
    session.commit()
    session.refresh(s)
    return to_read(s)


@router.get("/{shipment_id}/duty", response_model=duty.DutyResponse)
def shipment_duty(shipment_id: int, session: Session = Depends(get_session)):
    s = get_or_404(session, shipment_id)
    if not s.items:
        raise HTTPException(400, "Shipment has no line items")
    return duty.estimate(duty.DutyRequest(
        origin_country=s.origin_country, destination_country=s.destination_country,
        incoterm=s.incoterm.value, mode=s.mode.value, freight_cost=s.freight_cost,
        insurance_cost=s.insurance_cost, currency=s.currency,
        lines=[duty.DutyLine(description=i.description, hs_code=i.hs_code or "",
                             value=i.quantity * i.unit_value) for i in s.items],
    ))


@router.get("/{shipment_id}/compliance", response_model=compliance.ScreenResponse)
def shipment_compliance(shipment_id: int, session: Session = Depends(get_session)):
    s = get_or_404(session, shipment_id)
    return compliance.screen(compliance.ScreenRequest(
        parties=[compliance.Party(name=s.exporter_name, country=s.origin_country),
                 compliance.Party(name=s.importer_name, country=s.destination_country)],
        origin_country=s.origin_country, destination_country=s.destination_country,
        hs_codes=[i.hs_code for i in s.items if i.hs_code],
    ))


@router.get("/{shipment_id}/documents/{doc_type}", response_class=HTMLResponse)
def shipment_document(shipment_id: int, doc_type: str, session: Session = Depends(get_session)):
    if doc_type not in documents.DOC_TYPES:
        raise HTTPException(404, f"Unknown document type. Choose one of: {', '.join(documents.DOC_TYPES)}")
    return HTMLResponse(documents.render(get_or_404(session, shipment_id), doc_type))
