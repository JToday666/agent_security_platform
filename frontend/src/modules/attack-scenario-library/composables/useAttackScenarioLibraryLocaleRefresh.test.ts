import { nextTick, ref } from "vue";
import { describe, expect, it, vi } from "vitest";
import { useAttackScenarioLibraryLocaleRefresh } from "@/modules/attack-scenario-library/composables/useAttackScenarioLibraryLocaleRefresh";

describe("useAttackScenarioLibraryLocaleRefresh", () => {
  it("refreshes when the display locale changes", async () => {
    const locale = ref("zh-CN");
    const refresh = vi.fn();
    const stop = useAttackScenarioLibraryLocaleRefresh(locale, refresh);

    await nextTick();
    expect(refresh).not.toHaveBeenCalled();

    locale.value = "en-US";
    await nextTick();

    expect(refresh).toHaveBeenCalledTimes(1);
    stop();
  });

  it("does not refresh when aliases normalize to the same locale", async () => {
    const locale = ref("en");
    const refresh = vi.fn();
    const stop = useAttackScenarioLibraryLocaleRefresh(locale, refresh);

    locale.value = "en-US";
    await nextTick();

    expect(refresh).not.toHaveBeenCalled();
    stop();
  });
});
