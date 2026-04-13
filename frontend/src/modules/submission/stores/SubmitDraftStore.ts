import { ref } from "vue";
import { defineStore } from "pinia";
import type {
  PendingSubmitRequest,
  SubmitFormState,
  SubmitMetaResponse,
} from "@/shared/types/AgentTypes";
import type { DatasetCategory } from "@/shared/types/DatasetTypes";
import {
  getAllDatasetIds,
  getEnabledCategories,
  sanitizeDatasetSelection,
} from "@/modules/dataset/lib";
import {
  MAX_SUBMIT_DATASET_COUNT,
  normalizeDifficulty,
  normalizeTimeoutMinutes,
} from "@/modules/submission/lib";

const createDefaultForm = (meta: SubmitMetaResponse): SubmitFormState => ({
  submitMethod: meta.supportedMethods[0] ?? "api",
  agentName: "",
  description: "",
  api: {
    baseUrl: "",
    token: "",
  },
  docker: {
    imageUri: "",
    username: "",
    password: "",
  },
  parameters: {
    difficulty: meta.difficulty.default,
    timeoutMinutes: meta.timeoutMinutes.default,
    retryEnabled: meta.retryEnabled.default,
  },
  publicToLeaderboard: meta.publicToLeaderboard.default,
  selectedDatasetIds: [],
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
    retryEnabled: Boolean(form.parameters.retryEnabled),
  },
  publicToLeaderboard: Boolean(form.publicToLeaderboard),
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

  const syncWithCatalog = (categories: DatasetCategory[]) => {
    if (!form.value) {
      return;
    }

    const availableDatasetIds = getAllDatasetIds(categories);
    const availableCategoryIdSet = new Set(
      getEnabledCategories(categories).map((item) => item.categoryId),
    );

    let nextSelected = sanitizeDatasetSelection(
      categories,
      form.value.selectedDatasetIds,
      true,
      MAX_SUBMIT_DATASET_COUNT,
    );

    if (
      !hasSyncedCatalog.value &&
      nextSelected.length === 0 &&
      availableDatasetIds.length > 0
    ) {
      nextSelected = [...availableDatasetIds];
    }

    const nextExpanded = expandedCategoryIds.value.filter((item) =>
      availableCategoryIdSet.has(item),
    );

    form.value.selectedDatasetIds = nextSelected;
    expandedCategoryIds.value = nextExpanded;

    hasSyncedCatalog.value = true;
  };

  const resetDraft = (
    meta: SubmitMetaResponse,
    categories: DatasetCategory[],
  ) => {
    form.value = createDefaultForm(meta);
    form.value.selectedDatasetIds = [
      ...getAllDatasetIds(categories, MAX_SUBMIT_DATASET_COUNT),
    ];
    expandedCategoryIds.value = [];
    pendingRequest.value = null;
    hasSyncedCatalog.value = categories.length > 0;
  };

  const setSubmitMethod = (method: "api" | "docker") => {
    if (!form.value) {
      return;
    }

    form.value.submitMethod = method;
    if (method === "api") {
      form.value.api.token = "";
    }
    if (method === "docker") {
      form.value.docker.password = "";
    }
  };

  const setExpandedCategoryIds = (value: string[]) => {
    expandedCategoryIds.value = value;
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
    setExpandedCategoryIds,
    setPendingRequest,
    clearDraftAfterSubmit,
  };
});
