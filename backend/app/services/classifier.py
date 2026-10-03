import re

from pydantic import BaseModel, Field

from ..data.tariffs import HS_CODES, lookup
from . import ai


class HSCandidate(BaseModel):
    hs_code: str
    description: str
    chapter: str
    confidence: float = Field(ge=0, le=1)
    duty_rate: float | None = None
    reasoning: str
    restricted: str | None = None


class ClassifyRequest(BaseModel):
    description: str = Field(min_length=3, max_length=4000)
    origin_country: str | None = Field(default=None, min_length=2, max_length=2)
    destination_country: str = Field(default="US", min_length=2, max_length=2)
    material: str | None = None
    intended_use: str | None = None


class ClassifyResponse(BaseModel):
    candidates: list[HSCandidate]
    engine: str  # "claude" or "keyword"
    notes: str | None = None


_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hs_code": {"type": "string", "description": "6-digit HS subheading formatted XXXX.XX"},
                    "description": {"type": "string"},
                    "chapter": {"type": "string"},
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                },
                "required": ["hs_code", "description", "chapter", "confidence", "reasoning"],
                "additionalProperties": False,
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["candidates", "notes"],
    "additionalProperties": False,
}

_SYSTEM = (
    "You are a licensed customs classification specialist. Classify goods under the "
    "Harmonized System using the General Rules of Interpretation (GRI 1-6). Return the "
    "three most likely 6-digit HS subheadings, ordered by likelihood, with confidences "
    "that sum to at most 1. Cite the heading text and the GRI that decides the case in "
    "the reasoning. In `notes`, say what extra product facts would change the result."
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9\-']+", text.lower()))


def keyword_classify(req: ClassifyRequest) -> ClassifyResponse:
    text = " ".join(filter(None, [req.description, req.material, req.intended_use])).lower()
    words = _tokens(text)
    scored = []
    for hs in HS_CODES:
        score = 0.0
        for kw in hs.keywords:
            if " " in kw or "-" in kw:
                if kw in text:
                    score += 2.0
            elif kw in words or kw + "s" in words or kw.rstrip("s") in words:
                score += 1.0
        if score:
            scored.append((score, hs))
    scored.sort(key=lambda x: -x[0])
    top = scored[:3]
    total = sum(s for s, _ in top) or 1
    candidates = [
        HSCandidate(
            hs_code=hs.code,
            description=hs.description,
            chapter=hs.chapter,
            confidence=round(min(0.95, s / total * (0.9 if len(top) > 1 else 0.7)), 2),
            duty_rate=hs.rate_for(req.destination_country.upper()),
            reasoning=f"Matched keywords: {', '.join(k for k in hs.keywords if k in text)}.",
            restricted=hs.restricted,
        )
        for s, hs in top
    ]
    notes = (
        "Keyword match against the built-in reference tariff. Set ANTHROPIC_API_KEY for "
        "AI classification with GRI reasoning."
        if candidates
        else "No match in the reference tariff. Add material, function and use, or enable AI classification."
    )
    return ClassifyResponse(candidates=candidates, engine="keyword", notes=notes)


def classify(req: ClassifyRequest) -> ClassifyResponse:
    prompt = (
        f"Product description: {req.description}\n"
        f"Material/composition: {req.material or 'not stated'}\n"
        f"Intended use: {req.intended_use or 'not stated'}\n"
        f"Country of origin: {req.origin_country or 'not stated'}\n"
        f"Importing country: {req.destination_country}"
    )
    result = ai.structured(_SYSTEM, prompt, _SCHEMA)
    if not result or not result.get("candidates"):
        return keyword_classify(req)

    dest = req.destination_country.upper()
    candidates = []
    for c in result["candidates"][:3]:
        ref = lookup(c["hs_code"])
        candidates.append(
            HSCandidate(
                hs_code=c["hs_code"],
                description=c["description"],
                chapter=c["chapter"],
                confidence=max(0.0, min(1.0, float(c["confidence"]))),
                duty_rate=ref.rate_for(dest) if ref else None,
                reasoning=c["reasoning"],
                restricted=ref.restricted if ref else None,
            )
        )
    return ClassifyResponse(candidates=candidates, engine="claude", notes=result.get("notes"))
