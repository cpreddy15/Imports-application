import { AlertTriangle } from "lucide-react";
import type { DutyResponse } from "../lib/api";
import { money, pct } from "../lib/format";

export default function DutyBreakdown({ d }: { d: DutyResponse }) {
  const c = d.currency;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <Stat label="Customs value" value={money(d.customs_value, c)} sub={`${d.valuation_basis} basis`} />
        <Stat label="Duties & taxes" value={money(d.total_taxes_and_duties, c)} sub={d.fta_applied ? `FTA: ${d.fta_applied}` : "MFN rates"} />
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-line text-left text-[11px] uppercase tracking-wider text-slate-500">
            <th className="py-2 font-semibold">HS code</th><th className="py-2 text-right font-semibold">Value</th>
            <th className="py-2 text-right font-semibold">Rate</th><th className="py-2 text-right font-semibold">Duty</th>
          </tr>
        </thead>
        <tbody>
          {d.lines.map((l, i) => (
            <tr key={i} className="border-b border-line" title={`${l.description} — ${l.rate_source}`}>
              <td className="py-2 font-medium">{l.hs_code}{l.rate_source.startsWith("preferential") && <span className="ml-1 text-teal">FTA</span>}</td>
              <td className="mono py-2 text-right">{money(l.customs_value, c)}</td>
              <td className="mono py-2 text-right">{pct(l.duty_rate)}</td>
              <td className="mono py-2 text-right">{money(l.duty, c)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <dl className="space-y-1.5 text-sm">
        <Row k="Total duty" v={money(d.total_duty, c)} />
        {d.fees.map((f) => <Row key={f.name} k={f.name} v={money(f.amount, c)} />)}
        <Row k={`${d.import_tax_name} (${pct(d.import_tax_rate)})`} v={money(d.import_tax, c)} />
        <div className="flex justify-between border-t-2 border-navy pt-2 text-base font-semibold">
          <dt>Landed cost</dt><dd className="mono">{money(d.landed_cost, c)}</dd>
        </div>
      </dl>
      {d.warnings.length > 0 && (
        <ul className="space-y-1 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          {d.warnings.map((w) => <li key={w} className="flex gap-2"><AlertTriangle size={14} className="mt-0.5 shrink-0" />{w}</li>)}
        </ul>
      )}
      <p className="text-[11px] text-slate-400">Indicative estimate from a reference tariff. Confirm with the official schedule or your customs broker.</p>
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded border border-line bg-slate-50 p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mono text-lg font-semibold">{value}</div>
      <div className="text-xs text-slate-500">{sub}</div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return <div className="flex justify-between gap-3"><dt className="text-slate-600">{k}</dt><dd className="mono shrink-0">{v}</dd></div>;
}
