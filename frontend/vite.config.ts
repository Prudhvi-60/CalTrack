import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],

    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },

    server: {
      port: 5173,
      host: "0.0.0.0",

      allowedHosts: [
        "frontend-production-15c16.up.railway.app",
      ],

      proxy: {
        "/api": {
          target:
            env.VITE_DEV_PROXY_TARGET ||
            "http://127.0.0.1:8001",
          changeOrigin: true,
          secure: false,
        },
      },
    },

    preview: {
      host: "0.0.0.0",
      port: 4173,

      allowedHosts: [
        "frontend-production-15c16.up.railway.app",
      ],
    },

    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: "./src/test/setup.ts",
    },
  };
});
