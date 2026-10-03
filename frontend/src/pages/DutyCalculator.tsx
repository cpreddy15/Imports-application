import { Calculator, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import DutyBreakdown from "../components/DutyBreakdown";
import { CountrySelect, ErrorBox, PageHeader, Spinner } from "../components/ui";
import { api, type DutyRequest, type DutyResponse } from "../lib/api";
import { INCOTERMS, label } from "../lib/format";

export default function DutyCalculator() {
  const [req, setReq] = useState<DutyRequest>({
    origin_country: "CN", destination_country: "US", incoterm: "FOB", mode: "sea",
    freight_cost: 1200, insurance_cost: 80, claim_preference: false, currency: "USD",
    lines: [{ description: "Cotton t-shirts", hs_code: "6109.10", value: 15000 }, { description: "LED lamps", hs_code: "9405.42", value: 8000 }],
  });
  const [result, setResult] = useState<DutyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof DutyRequest>(k: K, v: DutyRequest[K]) => setReq((r) => ({ ...r, [k]: v }));
  const setLine = (i: number, patch: Partial<DutyRequest["lines"][number]>) =>
    setReq((r) => ({ ...r, lines: r.lines.map((l, n) => (n === i ? { ...l, ...patch } : l)) }));

  const run = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try { setResult(await api.duty(req)); } catch (err) { setError((err as Error).message); }
    setLoading(false);
  };

  return (
    <>
      <PageHeader title="Duty & landed cost calculator" subtitle="Estimate customs value, duties, fees and import VAT/GST" />
      <div className="grid gap-6 lg:grid-cols-5">
        <form onSubmit={run} className="card space-y-4 p-5 lg:col-span-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <div><span className="label">Origin</span><CountrySelect value={req.origin_country} onChange={(v) => set("origin_country", v)} /></div>
            <div><span className="label">Destination</span><CountrySelect value={req.destination_country} onChange={(v) => set("destination_country", v)} /></div>
            <div><span className="label">Incoterm</span>
              <select className="input" value={req.incoterm} onChange={(e) => set("incoterm", e.target.value)}>{INCOTERMS.map((i) => <option key={i}>{i}</option>)}</select></div>
            <div><span className="label">Mode</span>
              <select className="input" value={req.mode} onChange={(e) => set("mode", e.target.value)}>{["sea", "air", "road", "rail"].map((m) => <option key={m} value={m}>{label(m)}</option>)}</select></div>
            <div><span className="label">Freight</span><input type="number" min={0} step="0.01" className="input" value={req.freight_cost} onChange={(e) => set("freight_cost", +e.target.value)} /></div>
            <div><span className="label">Insurance</span><input type="number" min={0} step="0.01" className="input" value={req.insurance_cost} onChange={(e) => set("insurance_cost", +e.target.value)} /></div>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="accent-teal" checked={req.claim_preference} onChange={(e) => set("claim_preference", e.target.checked)} />
            Claim preferential (FTA) origin — certificate of origin available
          </label>
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="label mb-0">Goods (invoice value per line, {req.currency})</span>
              <button type="button" className="btn-outline h-8" onClick={() => set("lines", [...req.lines, { description: "", hs_code: "", value: 0 }])}><Plus size={14} /> Line</button>
            </div>
            <div className="space-y-2">
              {req.lines.map((l, i) => (
                <div key={i} className="grid grid-cols-12 gap-2">
                  <input className="input col-span-5" placeholder="Description" value={l.description} onChange={(e) => setLine(i, { description: e.target.value })} />
                  <input required className="input col-span-3" placeholder="HS code" value={l.hs_code} onChange={(e) => setLine(i, { hs_code: e.target.value })} />
                  <input type="number" min={0} step="0.01" className="input col-span-3" value={l.value} onChange={(e) => setLine(i, { value: +e.target.value })} />
                  <button type="button" disabled={req.lines.length === 1} className="btn-outline col-span-1 px-0" aria-label="Remove line" onClick={() => set("lines", req.lines.filter((_, n) => n !== i))}><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          </div>
          <button className="btn-primary" disabled={loading}>{loading ? <Spinner /> : <Calculator size={16} />} Calculate</button>
          <ErrorBox error={error} />
        </form>
        <div className="card p-5 lg:col-span-2">
          <h2 className="mb-3">Estimate</h2>
          {result ? <DutyBreakdown d={result} /> : <p className="text-slate-500">Fill in the shipment and press Calculate.</p>}
        </div>
      </div>
    </>
  );
}
