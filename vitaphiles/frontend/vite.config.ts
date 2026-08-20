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
      port: 5174,
      host: "0.0.0.0",
      proxy: {
        "/api": {
          target: env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8002",
          changeOrigin: true,
          secure: false,
        },
        "/health": {
          target: env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8002",
          changeOrigin: true,
          secure: false,
        },
      },
    },
    preview: {
      host: "0.0.0.0",
      port: 4174,
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: "./src/test/setup.ts",
    },
  };
});
