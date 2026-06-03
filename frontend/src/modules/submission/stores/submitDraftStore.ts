import { ref } from "vue";
import { defineStore } from "pinia";
import type {
  PendingSubmitRequest,
  SubmitFormState,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";
import type { AttackScenarioCatalogResponse } from "@/shared/types/attack-scenario-library-types";
import {
  MAX_SUBMIT_EVALUATION_ITEM_COUNT,
  normalizeDifficulty,
  normalizeMaxSteps,
  normalizeTimeoutMinutes,
} from "@/modules/submission/model/parameter-validator";

const createDefaultForm = (meta: SubmitMetaResponse): SubmitFormState => ({
  submitMethod: meta.supportedMethods[0] ?? "api",
  agentId: "",
  docker: {
    imageUri: "",
    command: "",
  },
  parameters: {
    difficulty: meta.difficulty.default,
    timeoutMinutes: meta.timeoutMinutes.default,
    maxSteps: meta.maxSteps.default,
  },
  leaderboardDisplayMode: meta.leaderboardDisplayMode.default,
  selectedAttackScenarioId: "",
  selectedEvaluationItemIds: [],
});

const applyMetaDefaults = (
  form: SubmitFormState,
  meta: SubmitMetaResponse,
): SubmitFormState => ({
  ...form,
  submitMethod: meta.supportedMethods.includes(form.submitMethod)
    ? form.submitMethod
    : (meta.supportedMethods[0] ?? "api"),
  parameters: {
    difficulty: normalizeDifficulty(
      form.parameters.difficulty,
      meta.difficulty,
    ),
    timeoutMinutes: normalizeTimeoutMinutes(
      form.parameters.timeoutMinutes,
      meta.timeoutMinutes,
    ),
    maxSteps: normalizeMaxSteps(form.parameters.maxSteps, meta.maxSteps),
  },
  leaderboardDisplayMode: meta.leaderboardDisplayMode.options.includes(
    form.leaderboardDisplayMode,
  )
    ? form.leaderboardDisplayMode
    : meta.leaderboardDisplayMode.default,
});

export const useSubmitDraftStore = defineStore("submitDraft", () => {
  const form = ref<SubmitFormState | null>(null);
  const expandedCategoryIds = ref<string[]>([]);
  const hasSyncedCatalog = ref(false);
  const pendingRequest = ref<PendingSubmitRequest | null>(null);

  const applyMeta = (meta: SubmitMetaResponse) => {
    if (!form.value) {
      form.value = createDefaultForm(meta);
      expandedCategoryIds.value = [];
      pendingRequest.value = null;
      hasSyncedCatalog.value = false;
      return;
    }

    form.value = applyMetaDefaults(form.value, meta);
  };

  const syncWithCatalog = (catalog: AttackScenarioCatalogResponse) => {
    if (!form.value) {
      return;
    }

    const scenario = catalog.attackScenarios.find(
      (item) => item.attackScenarioId === form.value?.selectedAttackScenarioId,
    );
    const availableItemIds = new Set(
      scenario?.riskDomains.flatMap((riskDomain) =>
        riskDomain.evaluationItems.map((item) => item.evaluationItemId),
      ) ?? [],
    );

    const nextExpanded = expandedCategoryIds.value.filter((item) =>
      Boolean(
        scenario?.riskDomains.some(
          (riskDomain) => riskDomain.riskDomainId === item,
        ),
      ),
    );

    form.value.selectedEvaluationItemIds = form.value.selectedEvaluationItemIds
      .filter((item) => availableItemIds.has(item))
      .slice(0, MAX_SUBMIT_EVALUATION_ITEM_COUNT);
    expandedCategoryIds.value = nextExpanded;
    hasSyncedCatalog.value = true;
  };

  const resetDraft = (
    meta: SubmitMetaResponse,
    _catalog: AttackScenarioCatalogResponse | null,
  ) => {
    form.value = createDefaultForm(meta);
    expandedCategoryIds.value = [];
    pendingRequest.value = null;
    hasSyncedCatalog.value = false;
  };

  const setSubmitMethod = (method: "api" | "docker") => {
    if (!form.value) {
      return;
    }

    form.value.submitMethod = method;
  };

  const setAgentId = (agentId: string) => {
    if (!form.value) {
      return;
    }

    form.value.agentId = agentId;
  };

  const setExpandedCategoryIds = (value: string[]) => {
    expandedCategoryIds.value = value;
  };

  const setAttackScenarioId = (attackScenarioId: string) => {
    if (!form.value || form.value.selectedAttackScenarioId === attackScenarioId) {
      return;
    }

    form.value.selectedAttackScenarioId = attackScenarioId;
    form.value.selectedEvaluationItemIds = [];
    expandedCategoryIds.value = [];
    pendingRequest.value = null;
  };

  const setPendingRequest = (value: PendingSubmitRequest | null) => {
    pendingRequest.value = value;
  };

  const clearDraftAfterSubmit = () => {
    form.value = null;
    expandedCategoryIds.value = [];
    pendingRequest.value = null;
    hasSyncedCatalog.value = false;
  };

  return {
    form,
    expandedCategoryIds,
    pendingRequest,
    applyMeta,
    syncWithCatalog,
    resetDraft,
    setSubmitMethod,
    setAgentId,
    setAttackScenarioId,
    setExpandedCategoryIds,
    setPendingRequest,
    clearDraftAfterSubmit,
  };
});
