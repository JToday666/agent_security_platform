import { nextTick } from "vue";
import { describe, expect, it, vi } from "vitest";
import { renderComponent } from "@/shared/test/renderComponent";
import PageStateCard from "./PageStateCard.vue";

describe("PageStateCard", () => {
  it("renders loading state", () => {
    const view = renderComponent(PageStateCard, {
      props: {
        title: "Loading",
        message: "Please wait",
        loading: true,
      },
    });

    const root = view.container.firstElementChild as HTMLElement | null;
    expect(root?.classList.contains("page-state-card--loading")).toBe(true);
    expect(view.container.textContent).toContain("Loading");
    expect(view.container.textContent).toContain("Please wait");
    view.unmount();
  });

  it("emits an action event", async () => {
    const onAction = vi.fn();
    const view = renderComponent(PageStateCard, {
      props: {
        title: "Error",
        message: "Retry available",
        actionText: "Retry",
        onAction,
      },
    });

    (
      view.container.querySelector("button") as HTMLButtonElement | null
    )?.click();
    await nextTick();

    expect(onAction).toHaveBeenCalledTimes(1);
    view.unmount();
  });
});
