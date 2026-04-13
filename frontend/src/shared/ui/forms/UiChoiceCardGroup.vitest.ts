import { nextTick } from "vue";
import { describe, expect, it, vi } from "vitest";
import { renderComponent } from "@/shared/test/renderComponent";
import UiChoiceCardGroup from "./UiChoiceCardGroup.vue";

describe("UiChoiceCardGroup", () => {
  it("renders options and marks the active item", async () => {
    const onUpdateModelValue = vi.fn();
    const view = renderComponent(UiChoiceCardGroup, {
      props: {
        modelValue: "api",
        options: [
          { value: "api", title: "API", description: "Use an HTTP endpoint" },
          { value: "docker", title: "Docker", description: "Use an image" },
        ],
        "onUpdate:modelValue": onUpdateModelValue,
      },
    });

    const items = view.container.querySelectorAll(
      ".ui-choice-card-group__item",
    );
    expect(items).toHaveLength(2);
    expect(
      items[0]?.classList.contains("ui-choice-card-group__item--active"),
    ).toBe(true);

    (
      view.container.querySelectorAll("button")[1] as
        | HTMLButtonElement
        | undefined
    )?.click();
    await nextTick();

    expect(onUpdateModelValue).toHaveBeenCalledWith("docker");
    view.unmount();
  });
});
