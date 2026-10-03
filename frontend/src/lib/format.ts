export const money = (v: number, currency = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: v >= 10000 ? 0 : 2 }).format(v);

export const compactMoney = (v: number, currency = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency, notation: "compact", maximumFractionDigits: 1 }).format(v);

export const pct = (v: number) => `${(v * 100).toFixed(v * 100 % 1 === 0 ? 0 : 1)}%`;

export const date = (v: string | null | undefined) =>
  v ? new Date(v.length === 10 ? v + "T00:00:00" : v).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "—";

export const flag = (cc: string) =>
  cc && cc.length === 2 ? String.fromCodePoint(...[...cc.toUpperCase()].map((c) => 0x1f1a5 + c.charCodeAt(0))) : "";

export const label = (s: string) => s.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

export const COUNTRIES: [string, string][] = [
  ["AE", "United Arab Emirates"], ["AU", "Australia"], ["BR", "Brazil"], ["CA", "Canada"], ["CN", "China"],
  ["DE", "Germany"], ["ES", "Spain"], ["FR", "France"], ["GB", "United Kingdom"], ["IN", "India"],
  ["IT", "Italy"], ["JP", "Japan"], ["KR", "South Korea"], ["MX", "Mexico"], ["NL", "Netherlands"],
  ["RU", "Russia"], ["SG", "Singapore"], ["TR", "Türkiye"], ["TW", "Taiwan"], ["US", "United States"],
  ["VN", "Vietnam"], ["IR", "Iran"], ["KP", "North Korea"], ["CU", "Cuba"], ["SY", "Syria"],
];

export const INCOTERMS = ["EXW", "FCA", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"];
