"""Sanctions, denied-party and controlled-goods screening."""

from difflib import SequenceMatcher
from typing import Literal

from pydantic import BaseModel, Field

from ..data.compliance_lists import (
    CONTROLLED_PREFIXES,
    DENIED_PARTIES,
    EMBARGOED_COUNTRIES,
    HIGH_RISK_COUNTRIES,
)
from ..data.tariffs import lookup

Severity = Literal["block", "review", "info"]


class Party(BaseModel):
    name: str
    country: str | None = Field(default=None, min_length=2, max_length=2)


class ScreenRequest(BaseModel):
    parties: list[Party] = []
    origin_country: str | None = None
    destination_country: str | None = None
    hs_codes: list[str] = []


class Finding(BaseModel):
    severity: Severity
    category: str
    subject: str
    message: str


class ScreenResponse(BaseModel):
    status: Literal["clear", "review", "blocked"]
    risk_score: int
    findings: list[Finding]


def _norm(name: str) -> str:
    drop = {"llc", "ltd", "inc", "co", "corp", "gmbh", "sa", "plc", "limited", "company", "the"}
    return " ".join(w for w in name.lower().replace(".", " ").replace(",", " ").split() if w not in drop)


def _country(code: str | None, label: str, findings: list[Finding]) -> None:
    if not code:
        return
    code = code.upper()
    if code in EMBARGOED_COUNTRIES:
        findings.append(Finding(severity="block", category="Embargo", subject=f"{label}: {code}",
                                message=f"{EMBARGOED_COUNTRIES[code]} is under comprehensive sanctions."))
    elif code in HIGH_RISK_COUNTRIES:
        findings.append(Finding(severity="review", category="Sanctions", subject=f"{label}: {code}",
                                message=HIGH_RISK_COUNTRIES[code]))


def screen(req: ScreenRequest) -> ScreenResponse:
    findings: list[Finding] = []
    _country(req.origin_country, "Origin", findings)
    _country(req.destination_country, "Destination", findings)

    for party in req.parties:
        _country(party.country, party.name, findings)
        n = _norm(party.name)
        for dp in DENIED_PARTIES:
            ratio = SequenceMatcher(None, n, _norm(dp["name"])).ratio()
            if ratio >= 0.92:
                findings.append(Finding(severity="block", category="Denied party", subject=party.name,
                                        message=f"Matches '{dp['name']}' on {dp['list']} ({ratio:.0%})."))
            elif ratio >= 0.75:
                findings.append(Finding(severity="review", category="Possible denied party", subject=party.name,
                                        message=f"Similar to '{dp['name']}' on {dp['list']} ({ratio:.0%}). Verify identity."))

    for code in req.hs_codes:
        digits = "".join(c for c in code if c.isdigit())
        for prefix, note in CONTROLLED_PREFIXES.items():
            p = prefix.replace(".", "")
            if digits.startswith(p):
                findings.append(Finding(severity="review", category="Controlled goods", subject=f"HS {code}", message=note))
                break
        else:
            ref = lookup(code)
            if ref and ref.restricted:
                findings.append(Finding(severity="info", category="Regulatory", subject=f"HS {ref.code}", message=ref.restricted))

    weights = {"block": 60, "review": 20, "info": 5}
    score = min(100, sum(weights[f.severity] for f in findings))
    status = "blocked" if any(f.severity == "block" for f in findings) else (
        "review" if any(f.severity == "review" for f in findings) else "clear")
    return ScreenResponse(status=status, risk_score=score, findings=findings)
