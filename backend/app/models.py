from datetime import date, datetime, timezone
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Direction(str, Enum):
    import_ = "import"
    export = "export"


class TransportMode(str, Enum):
    sea = "sea"
    air = "air"
    road = "road"
    rail = "rail"


class ShipmentStatus(str, Enum):
    booked = "booked"
    picked_up = "picked_up"
    departed = "departed"
    in_transit = "in_transit"
    customs = "customs"
    delivered = "delivered"
    on_hold = "on_hold"


STATUS_FLOW = [
    ShipmentStatus.booked,
    ShipmentStatus.picked_up,
    ShipmentStatus.departed,
    ShipmentStatus.in_transit,
    ShipmentStatus.customs,
    ShipmentStatus.delivered,
]


class Incoterm(str, Enum):
    EXW = "EXW"
    FCA = "FCA"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"


class ShipmentBase(SQLModel):
    direction: Direction = Direction.import_
    mode: TransportMode = TransportMode.sea
    incoterm: Incoterm = Incoterm.FOB
    origin_country: str = Field(min_length=2, max_length=2, description="ISO-3166 alpha-2")
    destination_country: str = Field(min_length=2, max_length=2)
    origin_port: str | None = None
    destination_port: str | None = None
    exporter_name: str
    exporter_address: str | None = None
    importer_name: str
    importer_address: str | None = None
    carrier: str | None = None
    currency: str = "USD"
    freight_cost: float = 0
    insurance_cost: float = 0
    etd: date | None = None
    eta: date | None = None
    notes: str | None = None


class Shipment(ShipmentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reference: str = Field(index=True, unique=True)
    status: ShipmentStatus = ShipmentStatus.booked
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    items: list["LineItem"] = Relationship(
        back_populates="shipment", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    events: list["ShipmentEvent"] = Relationship(
        back_populates="shipment",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "ShipmentEvent.created_at"},
    )


class LineItemBase(SQLModel):
    description: str
    hs_code: str | None = None
    quantity: float = Field(default=1, gt=0)
    unit: str = "pcs"
    unit_value: float = Field(default=0, ge=0)
    weight_kg: float = Field(default=0, ge=0)
    origin_country: str | None = None


class LineItem(LineItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    shipment_id: int = Field(foreign_key="shipment.id", index=True)
    shipment: Shipment | None = Relationship(back_populates="items")


class ShipmentEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    shipment_id: int = Field(foreign_key="shipment.id", index=True)
    status: ShipmentStatus
    location: str | None = None
    message: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    shipment: Shipment | None = Relationship(back_populates="events")


# ---- API schemas -----------------------------------------------------------

class LineItemCreate(LineItemBase):
    pass


class LineItemRead(LineItemBase):
    id: int
    line_value: float


class ShipmentCreate(ShipmentBase):
    items: list[LineItemCreate] = []


class ShipmentUpdate(SQLModel):
    status: ShipmentStatus | None = None
    carrier: str | None = None
    eta: date | None = None
    notes: str | None = None
    freight_cost: float | None = None
    insurance_cost: float | None = None


class EventCreate(SQLModel):
    status: ShipmentStatus
    location: str | None = None
    message: str | None = None


class EventRead(SQLModel):
    id: int
    status: ShipmentStatus
    location: str | None
    message: str | None
    created_at: datetime


class ShipmentRead(ShipmentBase):
    id: int
    reference: str
    status: ShipmentStatus
    created_at: datetime
    updated_at: datetime
    goods_value: float
    items: list[LineItemRead]
    events: list[EventRead]


class ShipmentSummary(SQLModel):
    id: int
    reference: str
    direction: Direction
    mode: TransportMode
    status: ShipmentStatus
    origin_country: str
    destination_country: str
    exporter_name: str
    importer_name: str
    goods_value: float
    currency: str
    eta: date | None
