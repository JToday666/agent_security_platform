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

describe("FormField", () => {
  it("keeps number edits local until blur when configured", async () => {
    const updates: string[] = [];
    const { host, unmount } = await mountFormField({
      label: "Timeout",
      modelValue: "30",
      type: "number",
      updateOnBlur: true,
      "onUpdate:modelValue": (value: string) => updates.push(value),
    });

    try {
      const input = host.querySelector<HTMLInputElement>("input");
      expect(input).toBeTruthy();

      (input as HTMLInputElement).value = "";
      input?.dispatchEvent(new Event("input", { bubbles: true }));
      await nextTick();

      expect(input?.value).toBe("");
      expect(updates).toEqual([]);

      (input as HTMLInputElement).value = "45";
      input?.dispatchEvent(new Event("input", { bubbles: true }));
      await nextTick();
      input?.dispatchEvent(new FocusEvent("blur", { bubbles: true }));
      await nextTick();

      expect(updates).toEqual(["45"]);
    } finally {
      unmount();
    }
  });

  it("resets the draft when the parent keeps the current value after blur", async () => {
    const updates: string[] = [];
    const { host, unmount } = await mountFormField({
      label: "Timeout",
      modelValue: "30",
      type: "number",
      updateOnBlur: true,
      "onUpdate:modelValue": (value: string) => updates.push(value),
    });

    try {
      const input = host.querySelector<HTMLInputElement>("input");
      expect(input).toBeTruthy();

      (input as HTMLInputElement).value = "";
      input?.dispatchEvent(new Event("input", { bubbles: true }));
      await nextTick();
      input?.dispatchEvent(new FocusEvent("blur", { bubbles: true }));
      await nextTick();
      await nextTick();

      expect(updates).toEqual([""]);
      expect(input?.value).toBe("30");
    } finally {
      unmount();
    }
  });

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
