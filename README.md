# TradeFlow AI — AI Import-Export Platform

An end-to-end platform for importers, exporters and freight forwarders: track shipments from
booking to delivery, classify goods with AI, estimate duties and landed cost, screen for
sanctions and export controls, generate trade documents, and ask an AI trade assistant.

The UI was designed with **Google Stitch** through its MCP server (see [`design/stitch`](design/stitch)),
and the AI features run on **Claude** through the Anthropic API.

| Module | What it does |
|---|---|
| **Dashboard** | KPIs, shipments by status, compliance alerts, rule-based insights (delays, unclassified items, holds, upcoming clearances) |
| **Shipments** | Create, track and update import/export shipments with a route timeline and event history. **Smart import** pulls parties, terms and line items out of pasted invoice text |
| **HS Classifier** | Top 3 HS codes with confidence, GRI reasoning, destination duty rate and regulatory flags |
| **Duty Calculator** | Customs value (CIF or FOB basis by country), MFN or FTA duty, US MPF/HMF fees, import VAT/GST, landed cost |
| **Compliance** | Screens for embargoed or high-risk countries, fuzzy-matches denied parties, flags controlled HS codes |
| **Documents** | Printable commercial invoice, packing list and certificate of origin for any shipment |
| **AI Assistant** | Chat about Incoterms, paperwork, duties and compliance, with an optional linked shipment as context |

## AI engines

Every AI feature has a deterministic fallback, so the app works fully **without an API key**:

| Feature | With `ANTHROPIC_API_KEY` | Without |
|---|---|---|
| HS classification | Claude, structured JSON output | Keyword match against the reference tariff |
| Invoice extraction | Claude, structured JSON output | Regex parser |
| Trade assistant | Claude chat | Built-in knowledge base |

Claude calls use `claude-opus-5-5` by default (set `CLAUDE_MODEL` to change it), with adaptive thinking
and server-side refusal fallbacks (`fallbacks: "default"`). See `backend/app/services/ai.py`.

> ⚠️ Tariff rates, FTA rules and sanctions lists in `backend/app/data/` are a curated **demo subset**.
> They are not legal advice. In production, connect official tariff schedules and a licensed
> screening provider (OFAC SDN, EU, UK HMT, UN, BIS Entity List).

## Quick start

### Docker (single container)

```bash
cp .env.example .env          # optionally add ANTHROPIC_API_KEY
docker compose up --build     # http://localhost:8000
```

### Local development

```bash
# API (http://localhost:8000, docs at /docs)
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-ant-... .venv/bin/uvicorn app.main:app --reload

# Web (http://localhost:5173, proxies /api to :8000)
cd frontend
npm install && npm run dev
```

Demo shipments are seeded on first start. Set `SEED_DEMO_DATA=false` to turn this off.

### Tests

```bash
cd backend && .venv/bin/python -m pytest -q     # API tests
cd frontend && npm run build                    # type-check + production build
```

CI runs both on every push (`.github/workflows/ci.yml`).

## Stitch MCP (UI design)

`.mcp.json` registers the Stitch MCP server for Claude Code. The API key comes from the
environment and is **never committed**:

```bash
export STITCH_API_KEY=your-key        # or put it in your shell profile
claude                                 # the "stitch" server loads from .mcp.json
```

This is equivalent to running
`claude mcp add stitch --transport http --header "X-Goog-Api-Key: $STITCH_API_KEY" https://stitch.googleapis.com/mcp`.

The Stitch project **"AI Import-Export Platform"** has four generated screens (dashboard, shipment
detail, HS classifier, AI assistant). Its design system is in [`design/stitch/DESIGN.md`](design/stitch/DESIGN.md),
and its tokens (navy `#0F172A`, teal `#0D9488` for AI actions, Inter, 4px radius) are in
`frontend/tailwind.config.js`.

## Architecture

```
frontend/   React 18 + TypeScript + Vite + Tailwind + Recharts
  src/pages/        Dashboard, Shipments, ShipmentDetail, Classifier, DutyCalculator, Compliance, Assistant
  src/lib/api.ts    Typed API client
backend/    FastAPI + SQLModel (SQLite by default; any SQLAlchemy URL works via DATABASE_URL)
  app/routers/      shipments, dashboard, tools (classify, duty, compliance, extract, chat)
  app/services/     ai (Claude wrapper), classifier, duty, compliance, documents, assistant
  app/data/         reference tariff, FTA groups, VAT rates, demo sanctions lists
design/stitch/      Stitch design system and screen index
```

### API overview

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Status and whether Claude is enabled |
| GET | `/api/dashboard` | KPIs, charts, alerts, insights |
| GET/POST | `/api/shipments` | List (filters: `status`, `direction`, `q`) / create |
| GET/PATCH/DELETE | `/api/shipments/{id}` | Read / update / delete |
| POST | `/api/shipments/{id}/events` | Add a tracking event and advance status |
| GET | `/api/shipments/{id}/duty` | Duty estimate for the shipment |
| GET | `/api/shipments/{id}/compliance` | Screen the shipment |
| GET | `/api/shipments/{id}/documents/{type}` | `commercial-invoice`, `packing-list`, `certificate-of-origin` (HTML) |
| POST | `/api/classify` | AI HS classification |
| GET | `/api/hs-codes?q=` | Search the reference tariff |
| POST | `/api/duty/estimate` | Standalone landed-cost calculation |
| POST | `/api/compliance/screen` | Standalone screening |
| POST | `/api/documents/extract` | Extract shipment data from invoice text |
| POST | `/api/assistant/chat` | Trade assistant |

Interactive OpenAPI docs are at `http://localhost:8000/docs`.
