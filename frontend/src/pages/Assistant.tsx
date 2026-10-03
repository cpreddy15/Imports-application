import { Bot, Send, Ship, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { EngineBadge, ErrorBox, Markdown, PageHeader, Spinner, StatusPill } from "../components/ui";
import { api, type ChatMessage, type Shipment, type ShipmentSummary } from "../lib/api";
import { flag } from "../lib/format";

const PROMPTS = [
  "Which Incoterm should I use for an FCL from Shanghai to Los Angeles?",
  "What documents do I need to export pharmaceuticals from India to Germany?",
  "How is customs value calculated under CIF vs FOB?",
  "What should I check before shipping lithium batteries by air?",
];

export default function Assistant() {
  const [params, setParams] = useSearchParams();
  const shipmentId = params.get("shipment") ? Number(params.get("shipment")) : undefined;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [engine, setEngine] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [shipments, setShipments] = useState<ShipmentSummary[]>([]);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => { api.shipments().then(setShipments).catch(() => {}); }, []);
  useEffect(() => {
    if (shipmentId) api.shipment(shipmentId).then(setShipment).catch(() => setShipment(null));
    else setShipment(null);
  }, [shipmentId]);
  useEffect(() => end.current?.scrollIntoView({ behavior: "smooth" }), [messages, loading]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const next: ChatMessage[] = [...messages, { role: "user", content: text.trim() }];
    setMessages(next); setInput(""); setLoading(true); setError(null);
    try {
      const r = await api.chat(next, shipmentId);
      setEngine(r.engine);
      setMessages([...next, { role: "assistant", content: r.reply }]);
    } catch (e) { setError((e as Error).message); }
    setLoading(false);
  };

  return (
    <>
      <PageHeader title="AI trade assistant" subtitle="Ask about Incoterms, customs paperwork, duties, compliance and logistics" actions={engine && <EngineBadge engine={engine} />} />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card flex h-[calc(100vh-14rem)] min-h-[480px] flex-col lg:col-span-2">
          <div className="flex-1 space-y-4 overflow-y-auto p-5">
            {messages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-teal-50 text-teal"><Bot /></div>
                <p className="mt-3 font-medium">How can I help with your trade operations?</p>
                <div className="mt-4 flex max-w-xl flex-wrap justify-center gap-2">
                  {PROMPTS.map((p) => (
                    <button key={p} onClick={() => send(p)} className="rounded-full border border-line px-3 py-1.5 text-xs text-slate-600 hover:border-teal hover:text-teal">{p}</button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${m.role === "user" ? "bg-navy text-white" : "bg-teal-50 text-teal"}`}>
                  {m.role === "user" ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className={`max-w-[80%] rounded px-4 py-3 text-sm ${m.role === "user" ? "bg-navy text-white" : "border border-line bg-slate-50"}`}>
                  {m.role === "user" ? m.content : <Markdown text={m.content} />}
                </div>
              </div>
            ))}
            {loading && <div className="flex items-center gap-2 text-sm text-slate-500"><Spinner /> Thinking…</div>}
            <ErrorBox error={error} />
            <div ref={end} />
          </div>
          <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex gap-2 border-t border-line p-3">
            <input className="input flex-1" placeholder="Ask a trade question…" value={input} onChange={(e) => setInput(e.target.value)} />
            <button className="btn-ai" disabled={!input.trim() || loading} aria-label="Send"><Send size={16} /></button>
          </form>
        </div>

        <aside className="space-y-4">
          <div className="card p-5">
            <h2 className="mb-3 flex items-center gap-2"><Ship size={16} /> Shipment context</h2>
            <select className="input" value={shipmentId ?? ""} onChange={(e) => setParams(e.target.value ? { shipment: e.target.value } : {})}>
              <option value="">No shipment linked</option>
              {shipments.map((s) => <option key={s.id} value={s.id}>{s.reference} · {s.origin_country}→{s.destination_country}</option>)}
            </select>
            {shipment && (
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <Link to={`/shipments/${shipment.id}`} className="font-medium hover:underline">{shipment.reference}</Link>
                  <StatusPill status={shipment.status} />
                </div>
                <div className="text-slate-600">{flag(shipment.origin_country)} {shipment.origin_port ?? shipment.origin_country} → {flag(shipment.destination_country)} {shipment.destination_port ?? shipment.destination_country}</div>
                <div className="text-slate-500">{shipment.incoterm} · {shipment.mode} · {shipment.items.length} line items</div>
                <p className="text-xs text-slate-400">The assistant sees this shipment's parties, route, terms and cargo.</p>
              </div>
            )}
          </div>
          <div className="card p-5">
            <h2 className="mb-3">Pre-shipment checklist</h2>
            <ul className="space-y-2 text-sm text-slate-600">
              {["HS codes confirmed for every line", "Parties screened against sanctions lists", "Incoterm agreed and on the invoice",
                "Certificate of origin for FTA claims", "Licences for controlled goods", "Dangerous-goods declaration if applicable"].map((c) => (
                <li key={c} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-teal" />{c}</li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </>
  );
}
