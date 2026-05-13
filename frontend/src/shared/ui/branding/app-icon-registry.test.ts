import { describe, expect, it } from "vitest";
import {
  APP_ICON_FALLBACK,
  isKnownAppIconName,
  resolveAppIconName,
} from "./app-icon-registry";

describe("app icon registry", () => {
  it("resolves app semantic icon names to lucide icons", () => {
    expect(resolveAppIconName("app:nav.contact")).toEqual({
      kind: "lucide",
      name: "messages-square",
      requested: "app:nav.contact",
    });

    expect(resolveAppIconName("app:action.submitEvaluation")).toEqual({
      kind: "lucide",
      name: "file-plus-2",
      requested: "app:action.submitEvaluation",
    });

    expect(resolveAppIconName("app:nav.agents")).toEqual({
      kind: "lucide",
      name: "bot",
      requested: "app:nav.agents",
    });

    expect(resolveAppIconName("app:nav.registerAgent")).toEqual({
      kind: "lucide",
      name: "plug-zap",
      requested: "app:nav.registerAgent",
    });

    expect(resolveAppIconName("app:action.registerAgent")).toEqual({
      kind: "lucide",
      name: "plug-zap",
      requested: "app:action.registerAgent",
    });

    expect(resolveAppIconName("app:control.language")).toEqual({
      kind: "lucide",
      name: "languages",
      requested: "app:control.language",
    });

    expect(resolveAppIconName("app:status.running")).toEqual({
      kind: "lucide",
      name: "loader-circle",
      requested: "app:status.running",
    });
  });

  it("resolves brand icon names separately from lucide icons", () => {
    expect(resolveAppIconName("brand:x")).toEqual({
      kind: "brand",
      name: "x",
      requested: "brand:x",
    });

    expect(resolveAppIconName("brand:github")).toEqual({
      kind: "brand",
      name: "github",
      requested: "brand:github",
    });
  });

  it("keeps direct lucide icon names compatible", () => {
    expect(resolveAppIconName("lucide:mail")).toEqual({
      kind: "lucide",
      name: "mail",
      requested: "lucide:mail",
    });
  });

  it("falls back to a neutral icon for unknown names", () => {
    const legacyGithubIcon = ["ri", "github-line"].join(":");

    expect(resolveAppIconName(legacyGithubIcon)).toEqual({
      kind: "lucide",
      name: APP_ICON_FALLBACK,
      requested: legacyGithubIcon,
    });
  });

  it("checks whether an icon name is registered", () => {
    const legacyXIcon = ["ri", "twitter-x-line"].join(":");

    expect(isKnownAppIconName("app:action.close")).toBe(true);
    expect(isKnownAppIconName("brand:x")).toBe(true);
    expect(isKnownAppIconName("lucide:mail")).toBe(true);
    expect(isKnownAppIconName(legacyXIcon)).toBe(false);
  });
});
