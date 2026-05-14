import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const currentDir = dirname(fileURLToPath(import.meta.url));

describe("agent register step indicator accessibility semantics", () => {
  it("keeps the visual tooltip hidden from ARIA when it is not associated with the trigger", () => {
    const source = readFileSync(
      resolve(currentDir, "AgentRegisterStepIndicator.vue"),
      "utf8",
    );

    expect(source).not.toContain('role="tooltip"');
    expect(source).toContain('aria-hidden="true"');
  });
});
