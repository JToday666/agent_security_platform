import { fileURLToPath, URL } from "node:url";

import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import viteCompression from "vite-plugin-compression";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget = env.VITE_BACKEND_TARGET || "http://127.0.0.1:8000";

  return {
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            const normalizedId = id.replace(/\\/g, "/");

            if (normalizedId.includes("/node_modules/")) {
              if (
                normalizedId.includes("/node_modules/echarts/") ||
                normalizedId.includes("/node_modules/vue-echarts/")
              ) {
                return "charts-vendor";
              }
              if (normalizedId.includes("/node_modules/@iconify/")) {
                return "iconify-vendor";
              }
              if (normalizedId.includes("/node_modules/axios/")) {
                return "http-vendor";
              }
              if (
                normalizedId.includes("/node_modules/vue/") ||
                normalizedId.includes("/node_modules/@vue/") ||
                normalizedId.includes("/node_modules/pinia/") ||
                normalizedId.includes("/node_modules/vue-router/")
              ) {
                return "vue-vendor";
              }
              if (normalizedId.includes("/node_modules/element-plus/")) {
                return "element-plus";
              }
              if (normalizedId.includes("/node_modules/lucide")) {
                return "lucide-icons";
              }
              return "vendor";
            }
          },
        },
      },
    },
    plugins: [vue(), viteCompression()],
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
