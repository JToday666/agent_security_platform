import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

const stripVueStylesForTests = () => ({
  name: "strip-vue-styles-for-tests",
  enforce: "pre" as const,
  transform(code: string, id: string) {
    if (!id.endsWith(".vue")) {
      return null;
    }

    return code.replace(/<style\b[\s\S]*?<\/style>/g, "");
  },
});

export default defineConfig({
  plugins: [stripVueStylesForTests(), vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts"],
    passWithNoTests: true,
    pool: "threads",
    maxWorkers: 1,
    fileParallelism: false,
  },
});
