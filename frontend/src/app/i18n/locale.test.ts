import { describe, expect, it } from "vitest";
import {
  DEFAULT_LOCALE,
  normalizeLocale,
  resolvePreferredLocale,
  resolveLocalePath,
} from "@/app/i18n";

describe("locale utilities", () => {
  it("normalizes supported language tags and aliases", () => {
    expect(normalizeLocale("zh")).toBe("zh-CN");
    expect(normalizeLocale("zh-hans")).toBe("zh-CN");
    expect(normalizeLocale("en-us")).toBe("en-US");
    expect(normalizeLocale("en-GB")).toBe("en-US");
    expect(normalizeLocale("fr")).toBe("fr-FR");
    expect(normalizeLocale("es-mx")).toBe("es-ES");
    expect(normalizeLocale("ja")).toBe("ja-JP");
  });

  it("falls back to zh-CN for unsupported locale tags", () => {
    expect(normalizeLocale("de-DE")).toBe(DEFAULT_LOCALE);
    expect(normalizeLocale("")).toBe(DEFAULT_LOCALE);
  });

  it("resolves the preferred locale from explicit, stored, browser, then default", () => {
    expect(
      resolvePreferredLocale({
        explicitLocale: "fr",
        storedLocale: "ja-JP",
        browserLocales: ["en-US"],
      }),
    ).toBe("fr-FR");

    expect(
      resolvePreferredLocale({
        storedLocale: "ja-JP",
        browserLocales: ["en-US"],
      }),
    ).toBe("ja-JP");

    expect(resolvePreferredLocale({ browserLocales: ["es-MX"] })).toBe(
      "es-ES",
    );

    expect(resolvePreferredLocale({ browserLocales: ["de-DE"] })).toBe(
      DEFAULT_LOCALE,
    );
  });

  it("keeps canonical locale paths unchanged", () => {
    expect(resolveLocalePath("/en-US/dataset/A1", "zh-CN")).toEqual({
      locale: "en-US",
      path: "/en-US/dataset/A1",
      redirect: false,
    });
  });

  it("canonicalizes locale casing in paths", () => {
    expect(resolveLocalePath("/en-us/dataset", "zh-CN")).toEqual({
      locale: "en-US",
      path: "/en-US/dataset",
      redirect: true,
    });
  });

  it("adds preferred locale to paths without a locale segment", () => {
    expect(resolveLocalePath("/dataset/A1?tab=meta#top", "ja-JP")).toEqual({
      locale: "ja-JP",
      path: "/ja-JP/dataset/A1?tab=meta#top",
      redirect: true,
    });

    expect(resolveLocalePath("/", "fr-FR")).toEqual({
      locale: "fr-FR",
      path: "/fr-FR/",
      redirect: true,
    });
  });

  it("falls back unsupported locale-looking paths to the default locale", () => {
    expect(resolveLocalePath("/de-DE/dataset", "en-US")).toEqual({
      locale: DEFAULT_LOCALE,
      path: "/zh-CN/dataset",
      redirect: true,
    });
  });
});
