import { AlertTriangle, ArrowRight, Clock, FileWarning, PackageCheck, ShieldAlert, Ship, Sparkles, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Empty, ErrorBox, PageHeader, StatusPill } from "../components/ui";
import { api, type Dashboard as D } from "../lib/api";
import { compactMoney, date, flag, label, money } from "../lib/format";

const INSIGHT_ICON: Record<string, typeof Clock> = {
  delay: Clock, classification: FileWarning, customs: PackageCheck, hold: AlertTriangle,
};

export default function Dashboard() {
  const [data, setData] = useState<D | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorBox error={`Could not load dashboard: ${error}`} />;
  if (!data) return <p className="text-slate-500">Loading…</p>;
  const { kpis } = data;

  const tiles = [
    { label: "Active shipments", value: kpis.active_shipments.toString(), sub: `${kpis.total_shipments} total`, icon: Ship },
    { label: "Value in transit", value: compactMoney(kpis.in_transit_value), sub: "Goods value, active", icon: Wallet },
    { label: "Delivered this month", value: kpis.delivered_this_month.toString(), sub: "Completed shipments", icon: PackageCheck },
    { label: "Compliance alerts", value: kpis.compliance_alerts.toString(), sub: kpis.compliance_alerts ? "Need review" : "All clear", icon: ShieldAlert, alert: kpis.compliance_alerts > 0 },
  ];

  return (
    <>
      <PageHeader
        title="Operations dashboard"
        subtitle="Live view of your import & export pipeline"
        actions={<Link to="/shipments?new=1" className="btn-primary">New shipment</Link>}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {tiles.map((t) => (
          <div key={t.label} className="card p-5">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">{t.label}</span>
              <t.icon size={18} className={t.alert ? "text-red-600" : "text-slate-400"} />
            </div>
            <div className="mono mt-2 text-3xl font-semibold tracking-tight">{t.value}</div>
            <div className={`mt-1 text-xs ${t.alert ? "font-medium text-red-600" : "text-slate-500"}`}>{t.sub}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <div className="card flex flex-col p-5 xl:col-span-2">
          <h2>Shipments by status</h2>
          <div className="mt-4 min-h-64 flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.by_status.map((s) => ({ ...s, name: label(s.status) }))} margin={{ left: -20, right: 8 }}>
                <CartesianGrid vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" tickLine={false} axisLine={{ stroke: "#CBD5E1" }} tick={{ fontSize: 12, fill: "#64748B" }} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#64748B" }} />
                <Tooltip
                  cursor={{ fill: "rgba(15,23,42,0.04)" }}
                  contentStyle={{ borderRadius: 4, border: "1px solid #E2E8F0", fontSize: 12 }}
                  formatter={(v: number) => [v, "Shipments"]}
                />
                <Bar dataKey="count" fill="#0D9488" radius={[4, 4, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-teal" />
            <h2>AI insights</h2>
          </div>
          <ul className="mt-4 space-y-3">
            {data.insights.length === 0 && <li className="text-slate-500">Nothing needs attention. 🎉</li>}
            {data.insights.map((i, n) => {
              const Icon = INSIGHT_ICON[i.type] ?? Sparkles;
              return (
                <li key={n}>
                  <Link to={`/shipments/${i.shipment_id}`} className="flex gap-3 rounded border border-line p-3 hover:border-slate-300 hover:shadow-hover">
                    <Icon size={18} className="mt-0.5 shrink-0 text-teal" />
                    <div>
                      <div className="font-medium">{i.title}</div>
                      <div className="mt-0.5 text-xs text-slate-500">{i.detail}</div>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      {data.alerts.length > 0 && (
        <div className="card mt-6 border-red-200 p-5">
          <div className="flex items-center gap-2 text-red-700">
            <ShieldAlert size={18} />
            <h2>Compliance alerts</h2>
          </div>
          <ul className="mt-3 divide-y divide-line">
            {data.alerts.map((a) => (
              <li key={a.shipment_id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <span><Link className="font-medium hover:underline" to={`/shipments/${a.shipment_id}`}>{a.reference}</Link> — {a.message}</span>
                <span className={`rounded px-2 py-0.5 text-xs font-medium ${a.status === "blocked" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-800"}`}>
                  {a.status === "blocked" ? "Blocked" : "Review"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card mt-6 overflow-hidden">
        <div className="flex items-center justify-between p-5 pb-3">
          <h2>Recent shipments</h2>
          <Link to="/shipments" className="inline-flex items-center gap-1 text-sm font-medium text-teal hover:text-teal-700">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px]">
            <thead>
              <tr><th className="th">Reference</th><th className="th">Route</th><th className="th">Mode</th><th className="th">Status</th><th className="th text-right">Value</th><th className="th">ETA</th></tr>
            </thead>
            <tbody>
              {data.recent.length === 0 && <tr><td colSpan={6}><Empty>No shipments yet.</Empty></td></tr>}
              {data.recent.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50">
                  <td className="td font-medium"><Link to={`/shipments/${s.id}`} className="hover:underline">{s.reference}</Link></td>
                  <td className="td">{flag(s.origin_country)} {s.origin_country} → {flag(s.destination_country)} {s.destination_country}</td>
                  <td className="td capitalize">{s.mode}</td>
                  <td className="td"><StatusPill status={s.status} /></td>
                  <td className="td mono text-right">{money(s.goods_value, s.currency)}</td>
                  <td className="td">{date(s.eta)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
