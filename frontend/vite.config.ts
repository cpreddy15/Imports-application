import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: { output: { manualChunks: { charts: ["recharts"], vendor: ["react", "react-dom", "react-router-dom"] } } },
  },
  server: {
    port: 5173,
    proxy: { "/api": process.env.VITE_API_URL ?? "http://localhost:8000" },
  },
});
