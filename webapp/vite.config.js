import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // WebApp توسط بک‌اند FastAPI روی Railway، زیر مسیر /webapp سرو می‌شود
  // (backend/main.py -> StaticFiles mount)، پس مسیر assetهای build شده هم
  // باید به همین زیرمسیر اشاره کند.
  base: "/webapp/",
  server: {
    host: true,
    port: 5173,
  },
  build: {
    outDir: "dist",
  },
});
