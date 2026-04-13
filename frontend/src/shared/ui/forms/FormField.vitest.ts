import { describe, expect, it } from "vitest";
import { renderComponent } from "@/shared/test/renderComponent";
import FormField from "./FormField.vue";

describe("FormField", () => {
  it("renders select options", () => {
    const view = renderComponent(FormField, {
      props: {
        modelValue: "b",
        type: "select",
        options: [
          { label: "Option A", value: "a" },
          { label: "Option B", value: "b" },
        ],
      },
    });

    const select = view.container.querySelector(
      "select",
    ) as HTMLSelectElement | null;
    expect(select?.value).toBe("b");
    expect(view.container.querySelectorAll("option")).toHaveLength(2);
    view.unmount();
  });

  it("supports readonly, autocomplete, leading icon and help text", () => {
    const view = renderComponent(FormField, {
      props: {
        modelValue: "query",
        type: "search",
        readonly: true,
        autocomplete: "off",
        leadingIcon: "lucide:search",
        help: "Type to filter",
      },
    });

    const input = view.container.querySelector("input");
    expect(input?.getAttribute("readonly")).not.toBeNull();
    expect(input?.getAttribute("autocomplete")).toBe("off");
    expect(view.container.querySelector(".form-field__icon")).not.toBeNull();
    expect(view.container.textContent).toContain("Type to filter");
    view.unmount();
  });
});
