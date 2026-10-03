import { Plus, Search, Sparkles, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { CountrySelect, EngineBadge, Empty, ErrorBox, PageHeader, Spinner, StatusPill } from "../components/ui";
import { api, type ShipmentCreate, type ShipmentSummary, type Status } from "../lib/api";
import { date, flag, INCOTERMS, label, money } from "../lib/format";

const STATUSES: Status[] = ["booked", "picked_up", "departed", "in_transit", "customs", "delivered", "on_hold"];

export default function Shipments() {
  const [params, setParams] = useSearchParams();
  const [rows, setRows] = useState<ShipmentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const status = params.get("status") ?? "";
  const creating = params.get("new") === "1";

  useEffect(() => {
    const t = setTimeout(() => {
      const p: Record<string, string> = {};
      if (status) p.status = status;
      if (q) p.q = q;
      api.shipments(p).then(setRows).catch((e) => setError(e.message));
    }, 200);
    return () => clearTimeout(t);
  }, [status, q]);

  const setParam = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next);
  };

  return (
    <>
      <PageHeader
        title="Shipments"
        subtitle="Track every import and export from booking to delivery"
        actions={<button className="btn-primary" onClick={() => setParam("new", "1")}><Plus size={16} /> New shipment</button>}
      />
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative w-full sm:w-72">
          <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input className="input pl-9" placeholder="Search reference, exporter, importer" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <select className="input w-full sm:w-48" value={status} onChange={(e) => setParam("status", e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{label(s)}</option>)}
        </select>
      </div>
      <ErrorBox error={error} />
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[900px]">
          <thead>
            <tr>
              <th className="th">Reference</th><th className="th">Type</th><th className="th">Route</th><th className="th">Parties</th>
              <th className="th">Status</th><th className="th text-right">Goods value</th><th className="th">ETA</th>
            </tr>
          </thead>
          <tbody>
            {rows === null && <tr><td colSpan={7}><Empty>Loading…</Empty></td></tr>}
            {rows?.length === 0 && <tr><td colSpan={7}><Empty>No shipments match.</Empty></td></tr>}
            {rows?.map((s) => (
              <tr key={s.id} className="hover:bg-slate-50">
                <td className="td font-medium"><Link to={`/shipments/${s.id}`} className="hover:underline">{s.reference}</Link></td>
                <td className="td"><span className="capitalize">{s.direction}</span> <span className="text-slate-400">· {s.mode}</span></td>
                <td className="td whitespace-nowrap">{flag(s.origin_country)} {s.origin_country} → {flag(s.destination_country)} {s.destination_country}</td>
                <td className="td text-xs"><div>{s.exporter_name}</div><div className="text-slate-500">→ {s.importer_name}</div></td>
                <td className="td"><StatusPill status={s.status} /></td>
                <td className="td mono text-right">{money(s.goods_value, s.currency)}</td>
                <td className="td whitespace-nowrap">{date(s.eta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {creating && <NewShipment onClose={() => setParam("new", "")} />}
    </>
  );
}

type Item = ShipmentCreate["items"][number];
const blankItem = (): Item => ({ description: "", hs_code: "", quantity: 1, unit: "pcs", unit_value: 0, weight_kg: 0 });

function NewShipment({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const [form, setForm] = useState<ShipmentCreate>({
    direction: "import", mode: "sea", incoterm: "FOB", origin_country: "CN", destination_country: "US",
    exporter_name: "", importer_name: "", currency: "USD", freight_cost: 0, insurance_cost: 0, eta: null, items: [blankItem()],
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invoiceText, setInvoiceText] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [engine, setEngine] = useState<string | null>(null);
  const [classifying, setClassifying] = useState<number | null>(null);

  const set = <K extends keyof ShipmentCreate>(k: K, v: ShipmentCreate[K]) => setForm((f) => ({ ...f, [k]: v }));
  const setItem = (i: number, patch: Partial<Item>) =>
    setForm((f) => ({ ...f, items: f.items.map((it, n) => (n === i ? { ...it, ...patch } : it)) }));

  const extract = async () => {
    setExtracting(true); setError(null);
    try {
      const x = await api.extract(invoiceText);
      setEngine(x.engine);
      setForm((f) => ({
        ...f,
        exporter_name: x.exporter_name ?? f.exporter_name,
        importer_name: x.importer_name ?? f.importer_name,
        origin_country: x.origin_country ?? f.origin_country,
        destination_country: x.destination_country ?? f.destination_country,
        incoterm: x.incoterm && INCOTERMS.includes(x.incoterm) ? x.incoterm : f.incoterm,
        currency: x.currency ?? f.currency,
        items: x.items.length
          ? x.items.map((i) => ({ ...blankItem(), description: i.description, quantity: i.quantity, unit_value: i.unit_value, hs_code: i.hs_code ?? "" }))
          : f.items,
      }));
    } catch (e) { setError((e as Error).message); }
    setExtracting(false);
  };

  const classify = async (i: number) => {
    setClassifying(i);
    try {
      const r = await api.classify({ description: form.items[i].description, origin_country: form.origin_country, destination_country: form.destination_country });
      if (r.candidates[0]) setItem(i, { hs_code: r.candidates[0].hs_code });
      else setError(`No HS match for "${form.items[i].description}". Add more detail.`);
    } catch (e) { setError((e as Error).message); }
    setClassifying(null);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setError(null);
    try {
      const s = await api.createShipment({
        ...form,
        eta: form.eta || null,
        items: form.items.filter((i) => i.description.trim()).map((i) => ({ ...i, hs_code: i.hs_code || null })),
      });
      navigate(`/shipments/${s.id}`);
    } catch (e) { setError((e as Error).message); setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-navy/40" onClick={onClose}>
      <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="h-full w-full max-w-3xl overflow-y-auto bg-white shadow-drawer">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-white px-6 py-4">
          <h2 className="text-lg">New shipment</h2>
          <button type="button" onClick={onClose} aria-label="Close"><X /></button>
        </div>
        <div className="space-y-6 p-6">
          <section className="rounded border border-teal/30 bg-teal-50 p-4">
            <div className="flex items-center gap-2 font-medium text-teal-700"><Sparkles size={16} /> Smart import from invoice</div>
            <p className="mt-1 text-xs text-slate-600">Paste a commercial or proforma invoice and AI fills in parties, terms and line items.</p>
            <textarea className="input mt-3 h-28 py-2" placeholder={"Exporter: Saigon Garment Co\nImporter: Northern Threads Ltd\nTerms: CIF  Currency: USD\nCotton T-shirts | 500 | 4.20"} value={invoiceText} onChange={(e) => setInvoiceText(e.target.value)} />
            <div className="mt-2 flex items-center gap-3">
              <button type="button" className="btn-ai" disabled={invoiceText.length < 10 || extracting} onClick={extract}>
                {extracting ? <Spinner /> : <Sparkles size={16} />} Extract
              </button>
              {engine && <EngineBadge engine={engine} />}
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-3">
            <div><span className="label">Direction</span>
              <select className="input" value={form.direction} onChange={(e) => set("direction", e.target.value as "import" | "export")}>
                <option value="import">Import</option><option value="export">Export</option>
              </select></div>
            <div><span className="label">Mode</span>
              <select className="input" value={form.mode} onChange={(e) => set("mode", e.target.value as ShipmentCreate["mode"])}>
                {["sea", "air", "road", "rail"].map((m) => <option key={m} value={m}>{label(m)}</option>)}
              </select></div>
            <div><span className="label">Incoterm</span>
              <select className="input" value={form.incoterm} onChange={(e) => set("incoterm", e.target.value)}>
                {INCOTERMS.map((i) => <option key={i}>{i}</option>)}
              </select></div>
            <div><span className="label">Origin country</span><CountrySelect value={form.origin_country} onChange={(v) => set("origin_country", v)} /></div>
            <div><span className="label">Destination country</span><CountrySelect value={form.destination_country} onChange={(v) => set("destination_country", v)} /></div>
            <div><span className="label">ETA</span><input type="date" className="input" value={form.eta ?? ""} onChange={(e) => set("eta", e.target.value)} /></div>
            <div className="sm:col-span-3 grid gap-4 sm:grid-cols-2">
              <div><span className="label">Exporter *</span><input required className="input" value={form.exporter_name} onChange={(e) => set("exporter_name", e.target.value)} /></div>
              <div><span className="label">Importer *</span><input required className="input" value={form.importer_name} onChange={(e) => set("importer_name", e.target.value)} /></div>
            </div>
            <div><span className="label">Currency</span><input className="input" maxLength={3} value={form.currency} onChange={(e) => set("currency", e.target.value.toUpperCase())} /></div>
            <div><span className="label">Freight cost</span><input type="number" min={0} step="0.01" className="input" value={form.freight_cost} onChange={(e) => set("freight_cost", +e.target.value)} /></div>
            <div><span className="label">Insurance cost</span><input type="number" min={0} step="0.01" className="input" value={form.insurance_cost} onChange={(e) => set("insurance_cost", +e.target.value)} /></div>
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h2>Line items</h2>
              <button type="button" className="btn-outline h-8" onClick={() => set("items", [...form.items, blankItem()])}><Plus size={14} /> Add item</button>
            </div>
            <div className="space-y-3">
              {form.items.map((it, i) => (
                <div key={i} className="grid gap-2 rounded border border-line p-3 sm:grid-cols-12">
                  <input className="input sm:col-span-5" placeholder="Description" value={it.description} onChange={(e) => setItem(i, { description: e.target.value })} />
                  <div className="flex gap-1 sm:col-span-3">
                    <input className="input" placeholder="HS code" value={it.hs_code ?? ""} onChange={(e) => setItem(i, { hs_code: e.target.value })} />
                    <button type="button" title="Classify with AI" className="btn-ai h-9 w-9 shrink-0 px-0" disabled={!it.description || classifying === i} onClick={() => classify(i)}>
                      {classifying === i ? <Spinner /> : <Sparkles size={14} />}
                    </button>
                  </div>
                  <input type="number" min={0} step="any" className="input sm:col-span-1" title="Quantity" value={it.quantity} onChange={(e) => setItem(i, { quantity: +e.target.value })} />
                  <input type="number" min={0} step="0.01" className="input sm:col-span-2" title="Unit value" value={it.unit_value} onChange={(e) => setItem(i, { unit_value: +e.target.value })} />
                  <button type="button" className="btn-outline h-9 px-0 sm:col-span-1" aria-label="Remove item" onClick={() => set("items", form.items.filter((_, n) => n !== i))}><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          </section>
          <ErrorBox error={error} />
        </div>
        <div className="sticky bottom-0 flex justify-end gap-2 border-t border-line bg-white px-6 py-4">
          <button type="button" className="btn-outline" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={saving}>{saving && <Spinner />} Create shipment</button>
        </div>
      </form>
    </div>
  );
}
