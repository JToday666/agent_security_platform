import { fileURLToPath, URL } from "node:url";

import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

const normalizeModuleId = (id: string) => id.replace(/\\/g, "/");

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget = env.VITE_BACKEND_TARGET || "http://127.0.0.1:8000";

  return {
    build: {
      rolldownOptions: {
        preserveEntrySignatures: "allow-extension",
        output: {
          strictExecutionOrder: true,
          codeSplitting: {
            includeDependenciesRecursively: false,
            groups: [
              {
                name: "charts-vendor",
                test: (id) => {
                  const normalizedId = normalizeModuleId(id);
                  return (
                    normalizedId.includes("/node_modules/echarts/") ||
                    normalizedId.includes("/node_modules/vue-echarts/")
                  );
                },
              },
              {
                name: "http-vendor",
                test: (id) =>
                  normalizeModuleId(id).includes("/node_modules/axios/"),
              },
              {
                name: "vue-vendor",
                test: (id) => {
                  const normalizedId = normalizeModuleId(id);
                  return (
                    normalizedId.includes("/node_modules/vue/") ||
                    normalizedId.includes("/node_modules/@vue/") ||
                    normalizedId.includes("/node_modules/pinia/") ||
                    normalizedId.includes("/node_modules/vue-router/")
                  );
                },
              },
              {
                name: "lucide-icons",
                test: (id) =>
                  normalizeModuleId(id).includes("/node_modules/lucide"),
              },
            ],
          },
        },
      },
    },
    plugins: [vue()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      proxy: {
        "/api": {
          target: backendTarget,
          changeOrigin: true,
        },
        "/uploads": {
          target: backendTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
