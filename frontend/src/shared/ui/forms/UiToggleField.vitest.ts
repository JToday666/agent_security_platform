import { nextTick } from "vue";
import { describe, expect, it, vi } from "vitest";
import { renderComponent } from "@/shared/test/renderComponent";
import UiToggleField from "./UiToggleField.vue";

describe("UiToggleField", () => {
  it("reflects checked state and emits updates", async () => {
    const onUpdateModelValue = vi.fn();
    const view = renderComponent(UiToggleField, {
      props: {
        modelValue: false,
        title: "Retry",
        description: "Retry once on failure",
        "onUpdate:modelValue": onUpdateModelValue,
      },
    });

    const input = view.container.querySelector(
      'input[type="checkbox"]',
    ) as HTMLInputElement | null;
    expect(input).not.toBeNull();

    input?.click();
    await nextTick();

    expect(onUpdateModelValue).toHaveBeenCalledWith(true);
    view.unmount();
  });
});
