import { describe, expect, it } from "vitest";
import { renderComponent } from "@/shared/test/renderComponent";
import UiButton from "./UiButton.vue";

describe("UiButton", () => {
  it("renders a leading icon and loading spinner", () => {
    const view = renderComponent(UiButton, {
      props: {
        leadingIcon: "lucide:plus",
        loading: true,
      },
      slots: {
        default: () => "Save",
      },
    });

    const root = view.container.firstElementChild as HTMLElement | null;
    expect(view.container.querySelector(".ui-button__icon")).not.toBeNull();
    expect(view.container.querySelector(".ui-button__spinner")).not.toBeNull();
    expect(root?.getAttribute("aria-busy")).toBe("true");
    view.unmount();
  });

  it("renders with a custom tag", () => {
    const view = renderComponent(UiButton, {
      props: {
        as: "label",
      },
      slots: {
        default: () => "Upload",
      },
    });

    expect(view.container.firstElementChild?.tagName).toBe("LABEL");
    view.unmount();
  });
});
