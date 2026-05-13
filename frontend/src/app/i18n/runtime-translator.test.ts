import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  resetRuntimeTranslator,
  setRuntimeTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";

describe("runtime translator", () => {
  afterEach(() => {
    resetRuntimeTranslator();
    vi.restoreAllMocks();
  });

  it("does not statically import zh-CN message JSON", () => {
    const source = readFileSync(
      join(process.cwd(), "src", "app", "i18n", "runtime-translator.ts"),
      "utf8",
    );

    expect(source).not.toContain("messages/zh-cn");
  });

  it("returns the key and warns once before the i18n runtime is installed", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(translateRuntimeMessage("agent.display.status.active")).toBe(
      "agent.display.status.active",
    );
    expect(translateRuntimeMessage("agent.display.status.draft")).toBe(
      "agent.display.status.draft",
    );
    expect(warn).toHaveBeenCalledTimes(1);
  });

  it("can reset a custom runtime translator", () => {
    setRuntimeTranslator((key) => `translated:${key}`);

    expect(translateRuntimeMessage("common.actions.confirm")).toBe(
      "translated:common.actions.confirm",
    );

    resetRuntimeTranslator();

    expect(translateRuntimeMessage("common.actions.confirm")).toBe(
      "common.actions.confirm",
    );
  });
});
