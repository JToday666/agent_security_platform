import { createApp, nextTick, ref } from "vue";
import { describe, expect, it } from "vitest";
import { i18n, loadLocaleMessages } from "@/app/i18n";
import type {
  SubmitFormState,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";
import SubmitParameterControls from "./SubmitParameterControls.vue";

const meta: SubmitMetaResponse = {
  supportedMethods: ["api"],
  difficulty: { min: 0.1, max: 1, step: 0.1, default: 0.5 },
  timeoutMinutes: { min: 5, max: 60, step: 5, default: 20 },
  maxSteps: { min: 1, max: 100, step: 1, default: 30 },
  leaderboardDisplayMode: {
    default: "public",
    options: ["public", "anonymous"],
  },
};

const mountControls = async () => {
  await loadLocaleMessages("zh-CN");

  const form = ref<SubmitFormState>({
    submitMethod: "api",
    agentId: "agt_demo",
    docker: {
      imageUri: "",
      command: "",
    },
    parameters: {
      difficulty: 0.5,
      timeoutMinutes: 20,
      maxSteps: 30,
    },
    leaderboardDisplayMode: "public",
    selectedAttackScenarioId: "",
    selectedEvaluationItemIds: [],
  });
  const host = document.createElement("div");
  document.body.appendChild(host);
  const app = createApp({
    components: { SubmitParameterControls },
    setup() {
      return { form, meta };
    },
    template: '<SubmitParameterControls v-model="form" :meta="meta" />',
  });
  app.use(i18n);
  app.mount(host);
  await nextTick();

  return {
    form,
    host,
    unmount: () => {
      app.unmount();
      host.remove();
    },
  };
};

const input = async (element: HTMLInputElement, value: string) => {
  element.value = value;
  element.dispatchEvent(new Event("input", { bubbles: true }));
  await nextTick();
};

const blur = async (element: HTMLInputElement) => {
  element.dispatchEvent(new FocusEvent("blur", { bubbles: true }));
  await nextTick();
};

describe("SubmitParameterControls", () => {
  it("keeps numeric draft text while editing and normalizes it on blur", async () => {
    const { form, host, unmount } = await mountControls();

    try {
      const numberInputs = host.querySelectorAll<HTMLInputElement>(
        'input[type="number"]',
      );
      const timeoutInput = numberInputs[1];
      const maxStepsInput = numberInputs[2];

      await input(timeoutInput, "");
      expect(timeoutInput.value).toBe("");
      expect(form.value.parameters.timeoutMinutes).toBe(20);

      await input(timeoutInput, "26");
      expect(timeoutInput.value).toBe("26");
      expect(form.value.parameters.timeoutMinutes).toBe(20);

      await blur(timeoutInput);
      expect(timeoutInput.value).toBe("25");
      expect(form.value.parameters.timeoutMinutes).toBe(25);

      await input(maxStepsInput, "");
      expect(maxStepsInput.value).toBe("");
      expect(form.value.parameters.maxSteps).toBe(30);

      await blur(maxStepsInput);
      expect(maxStepsInput.value).toBe("30");
      expect(form.value.parameters.maxSteps).toBe(30);
    } finally {
      unmount();
    }
  });
});
