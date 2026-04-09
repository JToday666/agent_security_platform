import { fileURLToPath, URL } from "node:url";

import { defineConfig, loadEnv, type PluginOption } from "vite";
import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import vueDevTools from "vite-plugin-vue-devtools";

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget = env.VITE_BACKEND_TARGET || "http://127.0.0.1:8001";
  const plugins: PluginOption[] = [vue(), vueJsx()];

  if (command === "serve") {
    plugins.push(vueDevTools());
  }

  return {
    plugins,
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
