/** Design tokens from the Stitch "TradeFlow AI" design system (design/stitch/DESIGN.md). */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      colors: {
        navy: { DEFAULT: "#0F172A", 800: "#1E293B", 950: "#020617" },
        teal: { DEFAULT: "#0D9488", 700: "#0F766E", 50: "#F0FDFA", 100: "#CCFBF1" },
        sky: { DEFAULT: "#0284C7" },
        canvas: "#F8FAFC",
        line: "#E2E8F0",
      },
      borderRadius: { DEFAULT: "4px", md: "6px", lg: "8px" },
      boxShadow: {
        card: "0 1px 3px 0 rgba(15,23,42,.04), 0 1px 2px -1px rgba(15,23,42,.03)",
        hover: "0 4px 6px -1px rgba(15,23,42,.07), 0 2px 4px -2px rgba(15,23,42,.05)",
        drawer: "0 10px 15px -3px rgba(15,23,42,.08), 0 4px 6px -4px rgba(15,23,42,.04)",
      },
    },
  },
  plugins: [],
};
