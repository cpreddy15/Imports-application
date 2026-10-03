import { Plus, ShieldCheck, Trash2 } from "lucide-react";
import { useState } from "react";
import ScreenResult from "../components/ScreenResult";
import { CountrySelect, ErrorBox, PageHeader, Spinner } from "../components/ui";
import { api, type ScreenResponse } from "../lib/api";

export default function Compliance() {
  const [parties, setParties] = useState([
    { name: "Global Dual-Use Trading LLC", country: "AE" },
    { name: "Kerala Spice Traders", country: "IN" },
  ]);
  const [origin, setOrigin] = useState("IN");
  const [dest, setDest] = useState("AE");
  const [hs, setHs] = useState("0904.11, 8542.31");
  const [result, setResult] = useState<ScreenResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      setResult(await api.screen({
        parties: parties.filter((p) => p.name.trim()),
        origin_country: origin || undefined,
        destination_country: dest || undefined,
        hs_codes: hs.split(/[,\s]+/).filter(Boolean),
      }));
    } catch (err) { setError((err as Error).message); }
    setLoading(false);
  };

  return (
    <>
      <PageHeader title="Trade compliance screening" subtitle="Screen parties, countries and goods against sanctions, denied-party and export-control lists" />
      <div className="grid gap-6 lg:grid-cols-5">
        <form onSubmit={run} className="card space-y-4 p-5 lg:col-span-3">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="label mb-0">Parties (buyer, consignee, end user, agents)</span>
              <button type="button" className="btn-outline h-8" onClick={() => setParties([...parties, { name: "", country: "US" }])}><Plus size={14} /> Party</button>
            </div>
            <div className="space-y-2">
              {parties.map((p, i) => (
                <div key={i} className="grid grid-cols-12 gap-2">
                  <input className="input col-span-6" placeholder="Company or person name" value={p.name}
                    onChange={(e) => setParties(parties.map((x, n) => (n === i ? { ...x, name: e.target.value } : x)))} />
                  <div className="col-span-5"><CountrySelect value={p.country} onChange={(v) => setParties(parties.map((x, n) => (n === i ? { ...x, country: v } : x)))} /></div>
                  <button type="button" className="btn-outline col-span-1 px-0" aria-label="Remove party" onClick={() => setParties(parties.filter((_, n) => n !== i))}><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div><span className="label">Origin country</span><CountrySelect allowEmpty value={origin} onChange={setOrigin} /></div>
            <div><span className="label">Destination country</span><CountrySelect allowEmpty value={dest} onChange={setDest} /></div>
          </div>
          <div><span className="label">HS codes (comma separated)</span><input className="input" value={hs} onChange={(e) => setHs(e.target.value)} /></div>
          <button className="btn-primary" disabled={loading}>{loading ? <Spinner /> : <ShieldCheck size={16} />} Run screening</button>
          <ErrorBox error={error} />
          <p className="text-[11px] text-slate-400">Demo lists only. Production screening must use live OFAC, EU, UK, UN and BIS lists via a licensed provider.</p>
        </form>
        <div className="card p-5 lg:col-span-2">
          <h2 className="mb-3">Result</h2>
          {result ? <ScreenResult r={result} /> : <p className="text-slate-500">Run a screening to see findings.</p>}
        </div>
      </div>
    </>
  );
}
