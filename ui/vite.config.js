import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  preview: {
    allowedHosts: [process.env.VITE_APP_HOST]
  },
  server: {
    fs: {
      // Permitir importar módulos fuera de /ui, específicamente ui5-components
      allow: [
        "..",
        resolve(__dirname, "../ui5-components")
      ]
    }
  }
});
