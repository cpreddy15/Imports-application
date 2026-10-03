import { Bot, Calculator, FileSearch, LayoutDashboard, Menu, Ship, ShieldCheck, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { api } from "../lib/api";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/shipments", label: "Shipments", icon: Ship },
  { to: "/classifier", label: "HS Classifier", icon: FileSearch },
  { to: "/duty", label: "Duty Calculator", icon: Calculator },
  { to: "/compliance", label: "Compliance", icon: ShieldCheck },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
];

export default function Layout() {
  const [aiEnabled, setAiEnabled] = useState<boolean | null>(null);
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    api.health().then((h) => setAiEnabled(h.ai_enabled)).catch(() => setAiEnabled(null));
  }, []);
  useEffect(() => setOpen(false), [location.pathname]);

  return (
    <div className="min-h-screen lg:flex">
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-navy-800 bg-navy px-4 text-white lg:hidden">
        <Brand />
        <button onClick={() => setOpen(!open)} aria-label="Toggle navigation">{open ? <X /> : <Menu />}</button>
      </header>

      <aside className={`${open ? "block" : "hidden"} fixed inset-x-0 top-14 z-20 bg-navy text-slate-300 lg:sticky lg:top-0 lg:block lg:h-screen lg:w-60 lg:shrink-0`}>
        <div className="hidden h-16 items-center px-5 lg:flex"><Brand /></div>
        <nav className="space-y-0.5 px-3 py-3">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-white/10 text-white" : "hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mx-3 mt-4 rounded border border-white/10 p-3 text-xs lg:absolute lg:bottom-4 lg:left-0 lg:right-0">
          <div className="flex items-center gap-2 font-medium text-white">
            <span className={`h-2 w-2 rounded-full ${aiEnabled ? "bg-teal-400" : "bg-amber-400"}`} />
            {aiEnabled ? "Claude AI connected" : "Offline AI mode"}
          </div>
          <p className="mt-1 text-slate-400">
            {aiEnabled ? "Classification, extraction and chat use Claude." : "Set ANTHROPIC_API_KEY on the API to enable Claude."}
          </p>
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-4 py-6 sm:px-8 lg:py-8">
        <div className="mx-auto max-w-7xl"><Outlet /></div>
      </main>
    </div>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5 text-white">
      <img src="/favicon.svg" alt="" className="h-7 w-7" />
      <span className="text-[15px] font-semibold tracking-tight">TradeFlow <span className="text-teal-400">AI</span></span>
    </div>
  );
}
