import { describe, expect, it } from "vitest";
import {
  LANGUAGE_OPTIONS,
  getLanguageOption,
  getNativeLanguageLabel,
} from "./language-switcher";

describe("language switcher options", () => {
  it("keeps supported languages in the navigation order with native labels", () => {
    expect(LANGUAGE_OPTIONS).toEqual([
      { locale: "zh-CN", nativeLabel: "汉语" },
      { locale: "en-US", nativeLabel: "English" },
      { locale: "fr-FR", nativeLabel: "Français" },
      { locale: "es-ES", nativeLabel: "Español" },
      { locale: "ja-JP", nativeLabel: "日本語" },
    ]);
  });

  it("resolves the native label for the current locale", () => {
    expect(getNativeLanguageLabel("fr-FR")).toBe("Français");
    expect(getLanguageOption("ja-JP")).toEqual({
      locale: "ja-JP",
      nativeLabel: "日本語",
    });
  });
});
