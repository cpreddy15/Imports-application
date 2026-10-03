import { ArrowLeft, Bot, Check, FileText, MapPin, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import DutyBreakdown from "../components/DutyBreakdown";
import ScreenResult from "../components/ScreenResult";
import { ErrorBox, PageHeader, StatusPill } from "../components/ui";
import { api, type DutyResponse, type ScreenResponse, type Shipment, type Status } from "../lib/api";
import { date, flag, label, money } from "../lib/format";

const FLOW: Status[] = ["booked", "picked_up", "departed", "in_transit", "customs", "delivered"];
const DOCS = [
  ["commercial-invoice", "Commercial invoice"],
  ["packing-list", "Packing list"],
  ["certificate-of-origin", "Certificate of origin"],
];

export default function ShipmentDetail() {
  const id = Number(useParams().id);
  const navigate = useNavigate();
  const [s, setS] = useState<Shipment | null>(null);
  const [duty, setDuty] = useState<DutyResponse | null>(null);
  const [screen, setScreen] = useState<ScreenResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState("");

  const load = useCallback(() => {
    api.shipment(id).then(setS).catch((e) => setError(e.message));
    api.shipmentDuty(id).then(setDuty).catch(() => setDuty(null));
    api.shipmentCompliance(id).then(setScreen).catch(() => setScreen(null));
  }, [id]);
  useEffect(load, [load]);

  if (error) return <ErrorBox error={error} />;
  if (!s) return <p className="text-slate-500">Loading…</p>;

  const current = FLOW.indexOf(s.status);
  const advance = async (status: Status) => {
    try {
      setS(await api.addEvent(id, { status, location: location || undefined }));
      setLocation("");
      load();
    } catch (e) { setError((e as Error).message); }
  };
  const remove = async () => {
    if (!confirm(`Delete shipment ${s.reference}? This cannot be undone.`)) return;
    await api.deleteShipment(id);
    navigate("/shipments");
  };
  const next = current >= 0 && current < FLOW.length - 1 ? FLOW[current + 1] : s.status === "on_hold" ? "in_transit" : null;

  return (
    <>
      <Link to="/shipments" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-navy"><ArrowLeft size={14} /> Shipments</Link>
      <PageHeader
        title={s.reference}
        subtitle={`${label(s.direction)} · ${label(s.mode)} · ${s.incoterm} · ${s.origin_port ?? s.origin_country} → ${s.destination_port ?? s.destination_country}`}
        actions={<>
          <Link to={`/assistant?shipment=${s.id}`} className="btn-ai"><Bot size={16} /> Ask AI</Link>
          <button onClick={remove} className="btn-outline text-red-600" aria-label="Delete shipment"><Trash2 size={16} /></button>
        </>}
      />

      <div className="card p-5">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3"><h2>Route timeline</h2><StatusPill status={s.status} /></div>
          <div className="flex flex-wrap gap-2">
            {next && <input className="input w-48" placeholder="Location (optional)" value={location} onChange={(e) => setLocation(e.target.value)} />}
            {next && <button className="btn-primary" onClick={() => advance(next)}>Mark {label(next).toLowerCase()}</button>}
            {s.status !== "on_hold" && s.status !== "delivered" && <button className="btn-outline" onClick={() => advance("on_hold")}>Put on hold</button>}
          </div>
        </div>
        <ol className="grid grid-cols-3 gap-y-4 sm:grid-cols-6">
          {FLOW.map((st, i) => {
            const done = current >= 0 ? i <= current : i < 2;
            const active = i === current;
            return (
              <li key={st} className="relative flex flex-col items-center text-center">
                {i > 0 && <span className={`absolute right-1/2 top-3.5 h-0.5 w-full ${done ? "bg-teal" : "bg-slate-200"}`} />}
                <span className={`relative z-10 flex h-7 w-7 items-center justify-center rounded-full border-2 ${
                  active ? "border-teal bg-white text-teal ring-4 ring-teal/15" : done ? "border-teal bg-teal text-white" : "border-slate-300 bg-white text-slate-300"}`}>
                  {done && !active ? <Check size={14} /> : <span className="h-2 w-2 rounded-full bg-current" />}
                </span>
                <span className={`mt-2 text-xs font-medium ${done ? "text-navy" : "text-slate-400"}`}>{label(st)}</span>
              </li>
            );
          })}
        </ol>
        {s.notes && <p className="mt-4 rounded bg-amber-50 px-3 py-2 text-sm text-amber-800">{s.notes}</p>}
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <div className="card overflow-x-auto">
            <h2 className="p-5 pb-3">Cargo</h2>
            <table className="w-full min-w-[600px]">
              <thead><tr><th className="th">Description</th><th className="th">HS code</th><th className="th text-right">Qty</th><th className="th text-right">Unit value</th><th className="th text-right">Line value</th></tr></thead>
              <tbody>
                {s.items.map((i) => (
                  <tr key={i.id}>
                    <td className="td">{i.description}</td>
                    <td className="td mono">{i.hs_code ?? <Link to={`/classifier?q=${encodeURIComponent(i.description)}`} className="text-teal hover:underline">Classify →</Link>}</td>
                    <td className="td mono text-right">{i.quantity.toLocaleString()} {i.unit}</td>
                    <td className="td mono text-right">{money(i.unit_value, s.currency)}</td>
                    <td className="td mono text-right">{money(i.line_value ?? 0, s.currency)}</td>
                  </tr>
                ))}
                <tr><td className="td font-semibold" colSpan={4}>Goods value</td><td className="td mono text-right font-semibold">{money(s.goods_value, s.currency)}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Party title="Exporter" name={s.exporter_name} addr={s.exporter_address} cc={s.origin_country} />
            <Party title="Importer" name={s.importer_name} addr={s.importer_address} cc={s.destination_country} />
          </div>

          <div className="card p-5">
            <h2 className="mb-3">Compliance screening</h2>
            {screen ? <ScreenResult r={screen} /> : <p className="text-slate-500">Screening…</p>}
          </div>

          <div className="card p-5">
            <h2 className="mb-3">Event history</h2>
            <ul className="space-y-3">
              {[...s.events].reverse().map((e) => (
                <li key={e.id} className="flex gap-3 text-sm">
                  <MapPin size={16} className="mt-0.5 shrink-0 text-slate-400" />
                  <div>
                    <div className="font-medium">{e.message ?? label(e.status)}</div>
                    <div className="text-xs text-slate-500">{date(e.created_at)}{e.location && ` · ${e.location}`}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-5">
            <h2 className="mb-3">Schedule</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Carrier</dt><dd>{s.carrier ?? "—"}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">ETD</dt><dd>{date(s.etd)}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">ETA</dt><dd>{date(s.eta)}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Freight</dt><dd className="mono">{money(s.freight_cost, s.currency)}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Insurance</dt><dd className="mono">{money(s.insurance_cost, s.currency)}</dd></div>
            </dl>
          </div>
          <div className="card p-5">
            <h2 className="mb-3">Duty estimate</h2>
            {duty ? <DutyBreakdown d={duty} /> : <p className="text-slate-500">Add line items to estimate duties.</p>}
          </div>
          <div className="card p-5">
            <h2 className="mb-3">Documents</h2>
            <ul className="space-y-2">
              {DOCS.map(([type, name]) => (
                <li key={type}>
                  <a href={api.documentUrl(s.id, type)} target="_blank" rel="noreferrer" className="flex items-center gap-3 rounded border border-line p-3 text-sm hover:border-slate-300 hover:shadow-hover">
                    <FileText size={16} className="text-teal" /> {name}
                    <span className="ml-auto text-xs text-slate-400">Open & print</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}

function Party({ title, name, addr, cc }: { title: string; name: string; addr: string | null; cc: string }) {
  return (
    <div className="card p-5">
      <div className="text-xs font-medium uppercase tracking-wider text-slate-500">{title}</div>
      <div className="mt-2 font-medium">{name}</div>
      <div className="text-sm text-slate-500">{addr ?? "—"}</div>
      <div className="mt-1 text-sm">{flag(cc)} {cc}</div>
    </div>
  );
}
