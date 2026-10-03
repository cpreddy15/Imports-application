"""Landed-cost / duty estimation."""

from pydantic import BaseModel, Field

from ..data.tariffs import (
    EU,
    FOB_VALUATION,
    FTA_GROUPS,
    IMPORT_TAX,
    US_HMF_RATE,
    US_MPF_MAX,
    US_MPF_MIN,
    US_MPF_RATE,
    lookup,
)

# What the invoice price already includes, per Incoterm.
_INCLUDES_FREIGHT = {"CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"}
_INCLUDES_INSURANCE = {"CIF", "CIP", "DAP", "DPU", "DDP"}


class DutyLine(BaseModel):
    description: str = ""
    hs_code: str
    value: float = Field(ge=0, description="Invoice value of the line")
    duty_rate_override: float | None = Field(default=None, ge=0, le=5)


class DutyRequest(BaseModel):
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(min_length=2, max_length=2)
    incoterm: str = "FOB"
    mode: str = "sea"
    freight_cost: float = Field(default=0, ge=0)
    insurance_cost: float = Field(default=0, ge=0)
    claim_preference: bool = Field(default=False, description="Proof of preferential origin available")
    currency: str = "USD"
    lines: list[DutyLine] = Field(min_length=1)


class DutyLineResult(BaseModel):
    description: str
    hs_code: str
    customs_value: float
    duty_rate: float
    duty: float
    rate_source: str


class Fee(BaseModel):
    name: str
    amount: float


class DutyResponse(BaseModel):
    currency: str
    valuation_basis: str
    goods_value: float
    customs_value: float
    lines: list[DutyLineResult]
    total_duty: float
    fees: list[Fee]
    import_tax_name: str
    import_tax_rate: float
    import_tax: float
    total_taxes_and_duties: float
    landed_cost: float
    fta_applied: str | None
    warnings: list[str]


def fta_for(origin: str, dest: str) -> str | None:
    for name, members in FTA_GROUPS.items():
        if origin in members and dest in members and origin != dest:
            return name
    return None


def estimate(req: DutyRequest) -> DutyResponse:
    origin, dest = req.origin_country.upper(), req.destination_country.upper()
    inco = req.incoterm.upper()
    warnings: list[str] = []

    goods_value = sum(l.value for l in req.lines)
    basis = "FOB" if dest in FOB_VALUATION else "CIF"

    # Normalise the invoice to an FOB figure, then build the customs value.
    fob = goods_value
    if inco in _INCLUDES_FREIGHT:
        fob -= req.freight_cost
    if inco in _INCLUDES_INSURANCE:
        fob -= req.insurance_cost
    if fob < 0:
        warnings.append("Freight/insurance exceed invoice value; check Incoterm and costs.")
        fob = max(fob, 0)
    customs_value = fob if basis == "FOB" else fob + req.freight_cost + req.insurance_cost
    ratio = customs_value / goods_value if goods_value else 0

    fta = fta_for(origin, dest) if req.claim_preference else None
    if origin in EU and dest in EU:
        fta = "EU Single Market"  # intra-EU: no customs duty at all
    if req.claim_preference and not fta:
        warnings.append(f"No preferential agreement on file for {origin}→{dest}; MFN rates used.")

    lines: list[DutyLineResult] = []
    for l in req.lines:
        ref = lookup(l.hs_code)
        if l.duty_rate_override is not None:
            rate, source = l.duty_rate_override, "manual override"
        elif fta:
            rate, source = 0.0, f"preferential ({fta})"
        elif ref:
            rate, source = ref.rate_for(dest), "reference tariff (MFN)"
        elif not l.hs_code.strip():
            rate, source = 0.05, "unclassified — default estimate"
            warnings.append(f"'{l.description or 'Line item'}' has no HS code; 5% assumed. Classify it first.")
        else:
            rate, source = 0.05, "default estimate"
            warnings.append(f"HS {l.hs_code} not in reference tariff; 5% assumed.")
        if ref and ref.restricted:
            warnings.append(f"HS {ref.code}: {ref.restricted}")
        cv = round(l.value * ratio, 2)
        lines.append(
            DutyLineResult(
                description=l.description or (ref.description if ref else ""),
                hs_code=ref.code if ref else (l.hs_code or "—"),
                customs_value=cv,
                duty_rate=rate,
                duty=round(cv * rate, 2),
                rate_source=source,
            )
        )

    total_duty = round(sum(l.duty for l in lines), 2)

    fees: list[Fee] = []
    if dest == "US" and not (origin in {"CA", "MX"} and fta):
        mpf = min(max(customs_value * US_MPF_RATE, US_MPF_MIN), US_MPF_MAX)
        fees.append(Fee(name="Merchandise Processing Fee (MPF)", amount=round(mpf, 2)))
    if dest == "US" and req.mode == "sea":
        fees.append(Fee(name="Harbor Maintenance Fee (HMF)", amount=round(customs_value * US_HMF_RATE, 2)))
    total_fees = round(sum(f.amount for f in fees), 2)

    tax_name, tax_rate = IMPORT_TAX.get(dest, ("Import VAT/GST (estimate)", 0.0))
    if origin in EU and dest in EU:
        tax_name, tax_rate = "VAT (reverse-charged intra-EU)", 0.0
    import_tax = round((customs_value + total_duty) * tax_rate, 2)

    total = round(total_duty + total_fees + import_tax, 2)
    landed = round(fob + req.freight_cost + req.insurance_cost + total, 2)
    return DutyResponse(
        currency=req.currency,
        valuation_basis=basis,
        goods_value=round(goods_value, 2),
        customs_value=round(customs_value, 2),
        lines=lines,
        total_duty=total_duty,
        fees=fees,
        import_tax_name=tax_name,
        import_tax_rate=tax_rate,
        import_tax=import_tax,
        total_taxes_and_duties=total,
        landed_cost=landed,
        fta_applied=fta,
        warnings=list(dict.fromkeys(warnings)),
    )
