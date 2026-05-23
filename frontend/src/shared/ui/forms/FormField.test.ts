import { createApp, nextTick } from "vue";
import { describe, expect, it } from "vitest";
import { i18n, loadLocaleMessages } from "@/app/i18n";
import FormField from "./FormField.vue";

const mountFormField = async (props: Record<string, unknown>) => {
  await loadLocaleMessages("zh-CN");

  const host = document.createElement("div");
  document.body.appendChild(host);

  const app = createApp(FormField, props);
  app.use(i18n);
  app.mount(host);
  await nextTick();

  return {
    host,
    unmount: () => {
      app.unmount();
      host.remove();
    },
  };
};

const click = async (element: Element) => {
  element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await nextTick();
};

describe("FormField select", () => {
  it("keeps the dropdown closed after selecting an option", async () => {
    const { host, unmount } = await mountFormField({
      label: "Status",
      modelValue: "all",
      type: "select",
      options: [
        { label: "All", value: "all" },
        { label: "Running", value: "running" },
      ],
      "onUpdate:modelValue": () => undefined,
    });

    try {
      const trigger = host.querySelector<HTMLButtonElement>(
        ".ui-select__trigger",
      );
      expect(trigger).toBeTruthy();

      await click(trigger as HTMLButtonElement);
      expect(trigger?.getAttribute("aria-expanded")).toBe("true");

      const options = host.querySelectorAll<HTMLElement>(".ui-select__item");
      await click(options[1]);

      expect(trigger?.getAttribute("aria-expanded")).toBe("false");
    } finally {
      unmount();
    }
  });

  it("associates select labels and errors with the trigger", async () => {
    const { host, unmount } = await mountFormField({
      id: "status-filter",
      label: "Status",
      modelValue: "all",
      type: "select",
      error: "Choose a status",
      options: [{ label: "All", value: "all" }],
      "onUpdate:modelValue": () => undefined,
    });

    try {
      const trigger = host.querySelector<HTMLButtonElement>("#status-filter");
      const label = host.querySelector(".form-field-label");
      const error = host.querySelector(".form-field-error");

      expect(trigger).toBeTruthy();
      expect(label?.id).toBeTruthy();
      expect(error?.id).toBeTruthy();
      expect(trigger?.getAttribute("aria-labelledby")).toContain(label?.id);
      expect(trigger?.getAttribute("aria-describedby")).toBe(error?.id);
      expect(trigger?.getAttribute("aria-invalid")).toBe("true");
    } finally {
      unmount();
    }
  });
});
