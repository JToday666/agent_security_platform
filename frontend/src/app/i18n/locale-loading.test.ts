import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { STORAGE_KEYS } from "@/shared/constants/storage-keys";

const importFreshI18n = async () => {
  vi.resetModules();
  setActivePinia(createPinia());
  return import("@/app/i18n");
};

describe("locale message loading", () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
  });

  it("loads the default fallback locale before activating a non-default locale", async () => {
    const { activateLocale, i18n } = await importFreshI18n();

    await activateLocale("en-US");

    expect(i18n.global.locale.value).toBe("en-US");
    expect(i18n.global.getLocaleMessage("en-US")).toHaveProperty("common");
    expect(i18n.global.getLocaleMessage("zh-CN")).toHaveProperty("common");
  });

  it("deduplicates concurrent loads for the same locale", async () => {
    const { i18n, loadLocaleMessages } = await importFreshI18n();
    const setLocaleMessage = vi.spyOn(i18n.global, "setLocaleMessage");

    await Promise.all([
      loadLocaleMessages("zh-CN"),
      loadLocaleMessages("zh-CN"),
    ]);

    expect(setLocaleMessage).toHaveBeenCalledTimes(1);
    expect(setLocaleMessage).toHaveBeenCalledWith(
      "zh-CN",
      expect.objectContaining({
        common: expect.any(Object),
      }),
    );
  });

  it("keeps only the latest activation side effects when locale switches race", async () => {
    const { activateLocale, i18n } = await importFreshI18n();

    await Promise.all([activateLocale("en-US"), activateLocale("ja-JP")]);

    expect(i18n.global.locale.value).toBe("ja-JP");
    expect(document.documentElement.lang).toBe("ja-JP");
    expect(localStorage.getItem(STORAGE_KEYS.i18n.displayLocale)).toBe(
      "ja-JP",
    );
  });
});
