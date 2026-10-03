from collections import Counter
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..db import get_session
from ..models import Shipment, ShipmentStatus
from ..services import compliance
from .shipments import goods_value, to_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

ACTIVE = {ShipmentStatus.booked, ShipmentStatus.picked_up, ShipmentStatus.departed,
          ShipmentStatus.in_transit, ShipmentStatus.customs, ShipmentStatus.on_hold}


@router.get("")
def dashboard(session: Session = Depends(get_session)):
    shipments = session.exec(select(Shipment)).all()
    today = date.today()
    active = [s for s in shipments if s.status in ACTIVE]
    in_transit_value = sum(goods_value(s) for s in active)

    alerts, insights = [], []
    for s in active:
        result = compliance.screen(compliance.ScreenRequest(
            parties=[compliance.Party(name=s.exporter_name, country=s.origin_country),
                     compliance.Party(name=s.importer_name, country=s.destination_country)],
            origin_country=s.origin_country, destination_country=s.destination_country,
            hs_codes=[i.hs_code for i in s.items if i.hs_code]))
        if result.status != "clear":
            alerts.append({"shipment_id": s.id, "reference": s.reference, "status": result.status,
                           "message": result.findings[0].message})
        if s.eta and s.eta < today and s.status != ShipmentStatus.delivered:
            insights.append({"type": "delay", "shipment_id": s.id,
                             "title": f"{s.reference} is past its ETA",
                             "detail": f"ETA was {s.eta.isoformat()}; contact {s.carrier or 'the carrier'} for a revised arrival."})
        if any(not i.hs_code for i in s.items):
            insights.append({"type": "classification", "shipment_id": s.id,
                             "title": f"{s.reference} has unclassified items",
                             "detail": "Run the AI HS Classifier before filing the customs entry."})
        if s.status == ShipmentStatus.customs and s.eta and s.eta <= today + timedelta(days=3):
            insights.append({"type": "customs", "shipment_id": s.id,
                             "title": f"Prepare clearance for {s.reference}",
                             "detail": "Arrives within 3 days — confirm duty payment and broker instructions."})
        if s.status == ShipmentStatus.on_hold:
            insights.append({"type": "hold", "shipment_id": s.id,
                             "title": f"{s.reference} is on hold",
                             "detail": s.notes or "Resolve the hold reason to avoid demurrage charges."})

    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    recent = sorted(shipments, key=lambda s: s.created_at, reverse=True)[:8]
    by_status = Counter(s.status.value for s in shipments)
    by_mode = Counter(s.mode.value for s in shipments)
    lanes = Counter(f"{s.origin_country}→{s.destination_country}" for s in shipments)

    return {
        "kpis": {
            "active_shipments": len(active),
            "in_transit_value": round(in_transit_value, 2),
            "delivered_this_month": sum(
                1 for s in shipments if s.status == ShipmentStatus.delivered
                and s.updated_at.replace(tzinfo=s.updated_at.tzinfo or timezone.utc) >= month_start),
            "compliance_alerts": len(alerts),
            "total_shipments": len(shipments),
        },
        "by_status": [{"status": st.value, "count": by_status.get(st.value, 0)} for st in ShipmentStatus],
        "by_mode": [{"mode": m, "count": c} for m, c in by_mode.most_common()],
        "top_lanes": [{"lane": l, "count": c} for l, c in lanes.most_common(5)],
        "recent": [to_summary(s) for s in recent],
        "alerts": alerts,
        "insights": insights[:6],
    }
