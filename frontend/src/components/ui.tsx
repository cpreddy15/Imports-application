import { Bot, Cpu } from "lucide-react";
import type { ReactNode } from "react";
import { COUNTRIES, label } from "../lib/format";
import type { Status } from "../lib/api";

const STATUS_STYLE: Record<Status, string> = {
  booked: "bg-slate-100 text-slate-700",
  picked_up: "bg-sky-50 text-sky-700",
  departed: "bg-sky-50 text-sky-700",
  in_transit: "bg-blue-50 text-blue-700",
  customs: "bg-amber-50 text-amber-700",
  delivered: "bg-emerald-50 text-emerald-700",
  on_hold: "bg-red-50 text-red-700",
};

export function StatusPill({ status }: { status: Status }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      {label(status)}
    </span>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="mt-1 text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

export function EngineBadge({ engine }: { engine: string }) {
  const ai = engine === "claude";
  return (
    <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-medium ${ai ? "bg-teal-50 text-teal-700" : "bg-slate-100 text-slate-600"}`}>
      {ai ? <Bot size={12} /> : <Cpu size={12} />}
      {ai ? "Claude AI" : `${label(engine)} engine`}
    </span>
  );
}

export function CountrySelect({ value, onChange, allowEmpty }: { value: string; onChange: (v: string) => void; allowEmpty?: boolean }) {
  return (
    <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>
      {allowEmpty && <option value="">— Any —</option>}
      {COUNTRIES.map(([c, n]) => (
        <option key={c} value={c}>{c} · {n}</option>
      ))}
    </select>
  );
}

export function ErrorBox({ error }: { error: string | null }) {
  if (!error) return null;
  return <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>;
}

export function Spinner() {
  return <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="px-4 py-10 text-center text-slate-500">{children}</div>;
}

/** Minimal markdown: **bold**, *italic*, `code`, bullet / numbered lists, paragraphs. */
export function Markdown({ text }: { text: string }) {
  const inline = (s: string) =>
    s
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*(?!\s)(.+?)\*/g, "$1<em>$2</em>")
      .replace(/_(.+?)_/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, '<code class="rounded bg-slate-100 px-1 text-[12px]">$1</code>');
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-2 leading-relaxed">
      {blocks.map((b, i) => {
        const lines = b.split("\n");
        if (lines.every((l) => /^\s*([-*]|\d+\.)\s/.test(l))) {
          const ordered = /^\s*\d+\./.test(lines[0]);
          const Tag = ordered ? "ol" : "ul";
          return (
            <Tag key={i} className={`${ordered ? "list-decimal" : "list-disc"} space-y-1 pl-5`}>
              {lines.map((l, j) => <li key={j} dangerouslySetInnerHTML={{ __html: inline(l.replace(/^\s*([-*]|\d+\.)\s/, "")) }} />)}
            </Tag>
          );
        }
        return <p key={i} dangerouslySetInnerHTML={{ __html: lines.map(inline).join("<br/>") }} />;
      })}
    </div>
  );
}
