import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Brauzer va SSR bir xil manzildan foydalanishi uchun API
      // shu origin ostida proksilanadi — CORS muammosi tug'ilmaydi.
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/media": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Yirik kutubxonalarni alohida chunkga ajratamiz: ular kamdan-kam
        // o'zgaradi va brauzer keshida uzoq turadi.
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          if (id.includes("react-router")) return "router";
          if (id.includes("react-dom") || id.includes("/react/")) return "react";
          if (id.includes("@tanstack")) return "query";
          if (id.includes("lucide-react")) return "icons";
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test-setup.js",
  },
});
