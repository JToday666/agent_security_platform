import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const currentDir = dirname(fileURLToPath(import.meta.url));

const readShellComponent = (fileName: string) =>
  readFileSync(resolve(currentDir, fileName), "utf8");

describe("shell popup accessibility semantics", () => {
  it.each(["LanguageSwitcher.vue", "DesktopNavOverflowMenu.vue"])(
    "%s uses plain popup semantics instead of incomplete ARIA menu semantics",
    (fileName) => {
      const source = readShellComponent(fileName);

      expect(source).not.toContain('aria-haspopup="menu"');
      expect(source).not.toContain('role="menu"');
      expect(source).not.toContain('role="menuitem"');
      expect(source).toContain(":aria-expanded=");
      expect(source).toContain(":aria-controls=");
    },
  );
});
