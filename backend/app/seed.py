"""Demo data so the platform is useful on first launch."""

from datetime import date, timedelta

from sqlmodel import Session, func, select

from .models import (
    STATUS_FLOW,
    Direction,
    Incoterm,
    LineItem,
    Shipment,
    ShipmentEvent,
    ShipmentStatus,
    TransportMode,
)

T = date.today()

DEMO = [
    dict(direction=Direction.import_, mode=TransportMode.sea, incoterm=Incoterm.FOB, origin_country="CN", destination_country="US",
         origin_port="Shanghai (CNSHA)", destination_port="Los Angeles (USLAX)", exporter_name="Shenzhen Brightway Electronics Ltd",
         exporter_address="88 Keji Rd, Nanshan, Shenzhen", importer_name="Pacific Gadgets Inc", importer_address="1200 Harbor Blvd, Long Beach, CA",
         carrier="COSCO Shipping", freight_cost=3200, insurance_cost=180, etd=T - timedelta(days=18), eta=T + timedelta(days=2),
         status=ShipmentStatus.customs,
         items=[("Wireless charging power banks 10000mAh", "8504.40", 2000, 6.5, 640), ("Lithium-ion battery packs 18650", "8507.60", 1500, 3.2, 450),
                ("LED desk lamps", "9405.42", 800, 9.8, 1200)]),
    dict(direction=Direction.export, mode=TransportMode.air, incoterm=Incoterm.CIP, origin_country="IN", destination_country="DE",
         origin_port="Mumbai (BOM)", destination_port="Frankfurt (FRA)", exporter_name="Mumbai Pharma Exports Pvt Ltd",
         exporter_address="Andheri East, Mumbai 400069", importer_name="Rhein Apotheken GmbH", importer_address="Mainzer Landstr. 50, Frankfurt",
         carrier="Lufthansa Cargo", freight_cost=1850, insurance_cost=95, etd=T - timedelta(days=2), eta=T + timedelta(days=1),
         status=ShipmentStatus.in_transit,
         items=[("Paracetamol 500mg tablets, retail packs", "3004.90", 12000, 0.85, 900)]),
    dict(direction=Direction.import_, mode=TransportMode.sea, incoterm=Incoterm.CIF, origin_country="VN", destination_country="GB",
         origin_port="Ho Chi Minh (VNSGN)", destination_port="Felixstowe (GBFXT)", exporter_name="Saigon Garment Co",
         exporter_address="District 7, Ho Chi Minh City", importer_name="Northern Threads Ltd", importer_address="Ancoats, Manchester",
         carrier="Maersk", freight_cost=2600, insurance_cost=140, etd=T - timedelta(days=30), eta=T - timedelta(days=3),
         status=ShipmentStatus.in_transit, notes="Vessel delayed at Port Klang transshipment",
         items=[("Men's cotton t-shirts, knitted", "6109.10", 6000, 2.4, 1500), ("Men's denim jeans", "6203.42", 2500, 7.9, 1650)]),
    dict(direction=Direction.export, mode=TransportMode.sea, incoterm=Incoterm.FCA, origin_country="US", destination_country="MX",
         origin_port="Houston (USHOU)", destination_port="Veracruz (MXVER)", exporter_name="Lone Star Solar LLC",
         exporter_address="2200 Energy Pkwy, Houston, TX", importer_name="EnerSol de México SA de CV", importer_address="Monterrey, NL",
         carrier="Hapag-Lloyd", freight_cost=1900, insurance_cost=110, etd=T + timedelta(days=4), eta=T + timedelta(days=11),
         status=ShipmentStatus.booked,
         items=[("Monocrystalline solar panels 450W", "8541.43", 600, 92, 13800), ("Grid-tie solar inverters", "8504.40", 40, 480, 900)]),
    dict(direction=Direction.import_, mode=TransportMode.road, incoterm=Incoterm.DAP, origin_country="DE", destination_country="FR",
         origin_port="Stuttgart", destination_port="Lyon", exporter_name="Schwarzwald Möbelwerk GmbH",
         exporter_address="Freiburg im Breisgau", importer_name="Maison & Bois SARL", importer_address="Lyon 69003",
         carrier="DB Schenker", freight_cost=780, insurance_cost=40, etd=T - timedelta(days=6), eta=T - timedelta(days=4),
         status=ShipmentStatus.delivered,
         items=[("Solid oak dining tables", "9403.60", 24, 640, 1800), ("Oak dining chairs", "9403.60", 96, 120, 720)]),
    dict(direction=Direction.export, mode=TransportMode.sea, incoterm=Incoterm.CFR, origin_country="IN", destination_country="AE",
         origin_port="Nhava Sheva (INNSA)", destination_port="Jebel Ali (AEJEA)", exporter_name="Kerala Spice Traders",
         exporter_address="Kochi, Kerala", importer_name="Global Dual-Use Trading LLC", importer_address="JAFZA, Dubai",
         carrier="MSC", freight_cost=950, insurance_cost=0, etd=T - timedelta(days=1), eta=T + timedelta(days=6),
         status=ShipmentStatus.on_hold, notes="Held for compliance review: consignee screening hit",
         items=[("Black pepper, whole, 25kg bags", "0904.11", 800, 6.2, 20000), ("Assam black tea, 1kg packs", "0902.30", 1200, 4.1, 1250)]),
    dict(direction=Direction.import_, mode=TransportMode.air, incoterm=Incoterm.EXW, origin_country="TW", destination_country="US",
         origin_port="Taipei (TPE)", destination_port="San Francisco (SFO)", exporter_name="Formosa Silicon Corp",
         exporter_address="Hsinchu Science Park", importer_name="Bay Area Robotics Inc", importer_address="Fremont, CA",
         carrier="EVA Air Cargo", freight_cost=2400, insurance_cost=210, etd=T - timedelta(days=1), eta=T + timedelta(days=1),
         status=ShipmentStatus.departed,
         items=[("Microcontroller chips (MCU) 32-bit", "8542.31", 20000, 2.75, 120), ("Brushless DC motors 400W", "8501.31", 500, 38, 900),
                ("Robot arm controller housings, aluminium", None, 300, 22, 450)]),
    dict(direction=Direction.export, mode=TransportMode.sea, incoterm=Incoterm.FOB, origin_country="IT", destination_country="CN",
         origin_port="Genoa (ITGOA)", destination_port="Shanghai (CNSHA)", exporter_name="Cantine Toscane SpA",
         exporter_address="Montalcino, Siena", importer_name="Shanghai Fine Wines Co", importer_address="Pudong, Shanghai",
         carrier="CMA CGM", freight_cost=2100, insurance_cost=160, etd=T - timedelta(days=12), eta=T + timedelta(days=20),
         status=ShipmentStatus.in_transit,
         items=[("Brunello di Montalcino DOCG, 750ml bottles", "2204.21", 3600, 18.5, 4800)]),
]


def seed(session: Session) -> None:
    if session.exec(select(func.count()).select_from(Shipment)).one() > 0:
        return
    for n, d in enumerate(DEMO, 1):
        d = dict(d)
        items = d.pop("items")
        status = d.pop("status")
        s = Shipment(**d, status=status, reference=f"TF-{T.year}-{n:04d}")
        s.items = [LineItem(description=a, hs_code=b, quantity=c, unit_value=v, weight_kg=w, origin_country=d["origin_country"])
                   for a, b, c, v, w in items]
        flow = STATUS_FLOW[: STATUS_FLOW.index(status) + 1] if status in STATUS_FLOW else STATUS_FLOW[:2] + [status]
        locations = {ShipmentStatus.booked: None, ShipmentStatus.picked_up: d["origin_port"],
                     ShipmentStatus.departed: d["origin_port"], ShipmentStatus.customs: d["destination_port"],
                     ShipmentStatus.delivered: d["destination_port"]}
        s.events = [ShipmentEvent(status=st, location=locations.get(st),
                                  message=(d.get("notes") if st == ShipmentStatus.on_hold else st.value.replace("_", " ").capitalize()))
                    for st in flow]
        session.add(s)
    session.commit()
