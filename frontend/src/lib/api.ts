export type Status = "booked" | "picked_up" | "departed" | "in_transit" | "customs" | "delivered" | "on_hold";
export type Mode = "sea" | "air" | "road" | "rail";

export interface LineItem {
  id?: number;
  description: string;
  hs_code: string | null;
  quantity: number;
  unit: string;
  unit_value: number;
  weight_kg: number;
  origin_country?: string | null;
  line_value?: number;
}

export interface ShipmentEvent {
  id: number;
  status: Status;
  location: string | null;
  message: string | null;
  created_at: string;
}

export interface ShipmentSummary {
  id: number;
  reference: string;
  direction: "import" | "export";
  mode: Mode;
  status: Status;
  origin_country: string;
  destination_country: string;
  exporter_name: string;
  importer_name: string;
  goods_value: number;
  currency: string;
  eta: string | null;
}

export interface Shipment extends ShipmentSummary {
  incoterm: string;
  origin_port: string | null;
  destination_port: string | null;
  exporter_address: string | null;
  importer_address: string | null;
  carrier: string | null;
  freight_cost: number;
  insurance_cost: number;
  etd: string | null;
  notes: string | null;
  items: LineItem[];
  events: ShipmentEvent[];
}

export interface ShipmentCreate {
  direction: "import" | "export";
  mode: Mode;
  incoterm: string;
  origin_country: string;
  destination_country: string;
  origin_port?: string;
  destination_port?: string;
  exporter_name: string;
  importer_name: string;
  carrier?: string;
  currency: string;
  freight_cost: number;
  insurance_cost: number;
  etd?: string | null;
  eta?: string | null;
  items: Omit<LineItem, "id" | "line_value">[];
}

export interface HSCandidate {
  hs_code: string;
  description: string;
  chapter: string;
  confidence: number;
  duty_rate: number | null;
  reasoning: string;
  restricted: string | null;
}

export interface ClassifyResponse { candidates: HSCandidate[]; engine: string; notes: string | null }

export interface DutyLine { description?: string; hs_code: string; value: number }
export interface DutyRequest {
  origin_country: string;
  destination_country: string;
  incoterm: string;
  mode: string;
  freight_cost: number;
  insurance_cost: number;
  claim_preference: boolean;
  currency: string;
  lines: DutyLine[];
}
export interface DutyResponse {
  currency: string;
  valuation_basis: string;
  goods_value: number;
  customs_value: number;
  lines: { description: string; hs_code: string; customs_value: number; duty_rate: number; duty: number; rate_source: string }[];
  total_duty: number;
  fees: { name: string; amount: number }[];
  import_tax_name: string;
  import_tax_rate: number;
  import_tax: number;
  total_taxes_and_duties: number;
  landed_cost: number;
  fta_applied: string | null;
  warnings: string[];
}

export interface Finding { severity: "block" | "review" | "info"; category: string; subject: string; message: string }
export interface ScreenResponse { status: "clear" | "review" | "blocked"; risk_score: number; findings: Finding[] }

export interface Insight { type: string; shipment_id: number; title: string; detail: string }
export interface Dashboard {
  kpis: { active_shipments: number; in_transit_value: number; delivered_this_month: number; compliance_alerts: number; total_shipments: number };
  by_status: { status: Status; count: number }[];
  by_mode: { mode: Mode; count: number }[];
  top_lanes: { lane: string; count: number }[];
  recent: ShipmentSummary[];
  alerts: { shipment_id: number; reference: string; status: string; message: string }[];
  insights: Insight[];
}

export interface Extracted {
  exporter_name: string | null;
  importer_name: string | null;
  origin_country: string | null;
  destination_country: string | null;
  incoterm: string | null;
  currency: string | null;
  items: { description: string; quantity: number; unit_value: number; hs_code: string | null }[];
  engine: string;
}

export interface ChatMessage { role: "user" | "assistant"; content: string }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch { /* not JSON */ }
    throw new Error(detail);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

const post = <T,>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  health: () => request<{ status: string; ai_enabled: boolean }>("/api/health"),
  dashboard: () => request<Dashboard>("/api/dashboard"),
  shipments: (params: Record<string, string> = {}) =>
    request<ShipmentSummary[]>(`/api/shipments?${new URLSearchParams(params)}`),
  shipment: (id: number) => request<Shipment>(`/api/shipments/${id}`),
  createShipment: (body: ShipmentCreate) => post<Shipment>("/api/shipments", body),
  updateShipment: (id: number, body: Partial<Shipment>) =>
    request<Shipment>(`/api/shipments/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteShipment: (id: number) => request<void>(`/api/shipments/${id}`, { method: "DELETE" }),
  addEvent: (id: number, body: { status: Status; location?: string; message?: string }) =>
    post<Shipment>(`/api/shipments/${id}/events`, body),
  shipmentDuty: (id: number) => request<DutyResponse>(`/api/shipments/${id}/duty`),
  shipmentCompliance: (id: number) => request<ScreenResponse>(`/api/shipments/${id}/compliance`),
  documentUrl: (id: number, type: string) => `/api/shipments/${id}/documents/${type}`,
  classify: (body: { description: string; origin_country?: string; destination_country: string; material?: string; intended_use?: string }) =>
    post<ClassifyResponse>("/api/classify", body),
  duty: (body: DutyRequest) => post<DutyResponse>("/api/duty/estimate", body),
  screen: (body: { parties: { name: string; country?: string }[]; origin_country?: string; destination_country?: string; hs_codes: string[] }) =>
    post<ScreenResponse>("/api/compliance/screen", body),
  extract: (text: string) => post<Extracted>("/api/documents/extract", { text }),
  chat: (messages: ChatMessage[], shipment_id?: number) =>
    post<{ reply: string; engine: string }>("/api/assistant/chat", { messages, shipment_id }),
};
