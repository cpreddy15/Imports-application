import { CheckCircle2, Info, OctagonX, TriangleAlert } from "lucide-react";
import type { ScreenResponse } from "../lib/api";

const STATUS = {
  clear: { cls: "border-emerald-200 bg-emerald-50 text-emerald-800", icon: CheckCircle2, text: "Clear — no issues found" },
  review: { cls: "border-amber-200 bg-amber-50 text-amber-800", icon: TriangleAlert, text: "Manual review required" },
  blocked: { cls: "border-red-200 bg-red-50 text-red-800", icon: OctagonX, text: "Blocked — do not proceed" },
};
const SEV = {
  block: { icon: OctagonX, cls: "text-red-600", label: "Block" },
  review: { icon: TriangleAlert, cls: "text-amber-600", label: "Review" },
  info: { icon: Info, cls: "text-sky", label: "Info" },
};

export default function ScreenResult({ r }: { r: ScreenResponse }) {
  const s = STATUS[r.status];
  return (
    <div className="space-y-3">
      <div className={`flex items-center justify-between rounded border p-3 ${s.cls}`}>
        <span className="flex items-center gap-2 font-medium"><s.icon size={18} />{s.text}</span>
        <span className="mono text-sm">Risk {r.risk_score}/100</span>
      </div>
      {r.findings.length > 0 && (
        <ul className="divide-y divide-line rounded border border-line">
          {r.findings.map((f, i) => {
            const v = SEV[f.severity];
            return (
              <li key={i} className="flex gap-3 p-3">
                <v.icon size={16} className={`mt-0.5 shrink-0 ${v.cls}`} />
                <div className="text-sm">
                  <div className="font-medium">{f.category} <span className="font-normal text-slate-500">· {f.subject}</span></div>
                  <div className="text-slate-600">{f.message}</div>
                </div>
                <span className={`ml-auto shrink-0 text-xs font-medium ${v.cls}`}>{v.label}</span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
