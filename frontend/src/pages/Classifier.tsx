import { AlertTriangle, Sparkles } from "lucide-react";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CountrySelect, EngineBadge, ErrorBox, PageHeader, Spinner } from "../components/ui";
import { api, type ClassifyResponse } from "../lib/api";
import { pct } from "../lib/format";

const EXAMPLES = [
  "Men's crew-neck t-shirt, 100% cotton jersey knit",
  "Rechargeable lithium-ion battery pack, 48V 20Ah for e-bikes",
  "Stainless steel cooking pot with lid, 5 litre",
  "Roasted arabica coffee beans in 1kg bags",
];

export default function Classifier() {
  const [params] = useSearchParams();
  const [description, setDescription] = useState(params.get("q") ?? "");
  const [material, setMaterial] = useState("");
  const [use, setUse] = useState("");
  const [origin, setOrigin] = useState("CN");
  const [dest, setDest] = useState("US");
  const [result, setResult] = useState<ClassifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setLoading(true); setError(null);
    try {
      setResult(await api.classify({ description, material: material || undefined, intended_use: use || undefined, origin_country: origin, destination_country: dest }));
    } catch (err) { setError((err as Error).message); }
    setLoading(false);
  };

  return (
    <>
      <PageHeader title="AI HS code classifier" subtitle="Describe a product and get ranked Harmonized System codes with reasoning and duty rates" />
      <div className="grid gap-6 lg:grid-cols-5">
        <form onSubmit={run} className="card space-y-4 p-5 lg:col-span-2">
          <div>
            <span className="label">Product description *</span>
            <textarea required minLength={3} className="input h-32 py-2" placeholder="What is it, what is it made of, what does it do?" value={description} onChange={(e) => setDescription(e.target.value)} />
            <div className="mt-2 flex flex-wrap gap-1.5">
              {EXAMPLES.map((x) => (
                <button type="button" key={x} onClick={() => setDescription(x)} className="rounded-full border border-line px-2.5 py-1 text-xs text-slate-600 hover:border-teal hover:text-teal">
                  {x.split(",")[0]}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><span className="label">Material</span><input className="input" placeholder="e.g. cotton" value={material} onChange={(e) => setMaterial(e.target.value)} /></div>
            <div><span className="label">Intended use</span><input className="input" placeholder="e.g. retail apparel" value={use} onChange={(e) => setUse(e.target.value)} /></div>
            <div><span className="label">Origin</span><CountrySelect value={origin} onChange={setOrigin} /></div>
            <div><span className="label">Destination</span><CountrySelect value={dest} onChange={setDest} /></div>
          </div>
          <button className="btn-ai w-full" disabled={loading || description.length < 3}>
            {loading ? <Spinner /> : <Sparkles size={16} />} Classify with AI
          </button>
          <ErrorBox error={error} />
        </form>

        <div className="space-y-4 lg:col-span-3">
          {!result && !loading && (
            <div className="card flex h-full min-h-60 items-center justify-center p-8 text-center text-slate-500">
              Results appear here: the top three HS candidates with confidence, reasoning and the destination duty rate.
            </div>
          )}
          {loading && <div className="card p-8 text-center text-slate-500">Analysing product against the General Rules of Interpretation…</div>}
          {result && !loading && (
            <>
              <div className="flex items-center justify-between">
                <h2>{result.candidates.length ? "Top candidates" : "No candidates"}</h2>
                <EngineBadge engine={result.engine} />
              </div>
              {result.candidates.map((c, i) => (
                <div key={c.hs_code + i} className={`card p-5 ${i === 0 ? "border-teal/50" : ""}`}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="mono text-xl font-semibold">{c.hs_code}</span>
                        {i === 0 && <span className="rounded bg-teal-50 px-2 py-0.5 text-[11px] font-medium text-teal-700">Best match</span>}
                      </div>
                      <div className="mt-1 font-medium">{c.description}</div>
                      <div className="text-xs text-slate-500">Chapter {c.chapter}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-slate-500">Duty into {dest}</div>
                      <div className="mono text-lg font-semibold">{c.duty_rate == null ? "—" : pct(c.duty_rate)}</div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-slate-500"><span>Confidence</span><span className="mono">{pct(c.confidence)}</span></div>
                    <div className="mt-1 h-1.5 rounded-full bg-slate-100">
                      <div className="h-1.5 rounded-full bg-teal" style={{ width: `${Math.round(c.confidence * 100)}%` }} />
                    </div>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">{c.reasoning}</p>
                  {c.restricted && (
                    <p className="mt-3 flex gap-2 rounded bg-amber-50 px-3 py-2 text-xs text-amber-800"><AlertTriangle size={14} className="mt-0.5 shrink-0" />{c.restricted}</p>
                  )}
                </div>
              ))}
              {result.notes && <p className="text-sm text-slate-500">{result.notes}</p>}
            </>
          )}
        </div>
      </div>
    </>
  );
}
