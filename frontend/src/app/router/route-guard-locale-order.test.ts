import type { Router } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

const SUPPORTED_LOCALE_SET = new Set([
  "zh-CN",
  "en-US",
  "fr-FR",
  "es-ES",
  "ja-JP",
]);

const normalizeLocale = (locale?: string | null) =>
  locale && SUPPORTED_LOCALE_SET.has(locale) ? locale : "zh-CN";

describe("route guard locale synchronization order", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("updates RouteLocation before activating the route locale", async () => {
    const activationObservedLocales: string[] = [];

    vi.doMock("@/app/i18n", () => ({
      DEFAULT_LOCALE: "zh-CN",
      activateLocale: vi.fn(async () => {
        const { RouteLocation } = await import("@/app/router/route-names");
        activationObservedLocales.push(RouteLocation.currentLocale);
        return "fr-FR";
      }),
      normalizeLocale,
      resolveLocalePath: vi.fn(() => ({
        locale: "fr-FR",
        path: "/fr-FR/dataset",
        redirect: false,
      })),
      resolveRuntimePreferredLocale: vi.fn(() => "zh-CN"),
    }));

    vi.doMock("@/modules/account/stores/userStore", () => ({
      useUserStore: () => ({
        initPromise: null,
        isLogin: true,
        openLoginDialog: vi.fn(),
        setPostLoginRedirect: vi.fn(),
      }),
    }));

    const { RouteLocation } = await import("@/app/router/route-names");
    const { registerRouteGuards } = await import("@/app/router/route-guards");
    let guard:
      | ((to: {
          fullPath: string;
          matched: Array<{ meta?: unknown }>;
        }) => unknown)
      | undefined;
    const router = {
      beforeEach: vi.fn((callback) => {
        guard = callback;
      }),
    };

    RouteLocation.setCurrentLocale("zh-CN");
    registerRouteGuards(router as unknown as Router);

    await guard?.({
      fullPath: "/fr-FR/dataset",
      matched: [],
    });

    expect(activationObservedLocales).toEqual(["fr-FR"]);
    expect(RouteLocation.currentLocale).toBe("fr-FR");
  });
});
