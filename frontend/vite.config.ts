import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Build straight into the Frappe app so /portal serves it (see www/portal/index.html).
export default defineConfig({
  plugins: [react()],
  base: "/assets/equip_rental/portal/",
  build: {
    outDir: "../equip_rental/public/portal", emptyOutDir: true, cssCodeSplit: false,
    rollupOptions: { input: "src/main.tsx", output: { entryFileNames: "app.js", assetFileNames: "app.[ext]" } },
  },
  server: { proxy: { "/api": "http://equip-rental.localhost:8002" } },
});
