import { ref } from "vue";
import { defineStore } from "pinia";
import type {
  SubmitFormPersistedData,
  SubmitFormState,
  SubmitMetaResponse,
} from "@/types/AgentTypes";
import type { DatasetCategory } from "@/types/DatasetTypes";
import {
  getAllDatasetIds,
  getEnabledCategories,
  sanitizeDatasetSelection,
} from "@/utils/DatasetUtils";
import {
  clearPersistedState,
  loadPersistedState,
  savePersistedState,
} from "@/utils/StorageUtils";
import {
  normalizeDifficulty,
  normalizeTimeoutMinutes,
} from "@/utils/SubmitParameterUtils";

const STORAGE_KEY = "agent-platform:submit-page:form:v2";
const STORAGE_VERSION = 2;
const PERSIST_DELAY_MS = 400;

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
  const restoredDraftNotice = ref(false);
  const catalogSyncNotice = ref("");
  const hydrated = ref(false);
  const restoredFromPersistedDraft = ref(false);
  const persistedCatalogVersion = ref("");
  const hasSyncedCatalog = ref(false);
  const currentMeta = ref<SubmitMetaResponse | null>(null);
  const persistTimer = ref<number | null>(null);

  const clearPersistTimer = () => {
    if (persistTimer.value !== null) {
      window.clearTimeout(persistTimer.value);
      persistTimer.value = null;
    }
  };

  const applyMeta = (meta: SubmitMetaResponse) => {
    currentMeta.value = meta;
    const defaultForm = createDefaultForm(meta);

    if (!hydrated.value) {
      const persisted = loadPersistedState<SubmitFormPersistedData>(
        STORAGE_KEY,
        STORAGE_VERSION,
      );

      if (persisted) {
        form.value = applyMetaDefaults(
          {
            ...defaultForm,
            ...persisted.data,
            api: {
              ...defaultForm.api,
              ...persisted.data.api,
              token: "",
            },
            docker: {
              ...defaultForm.docker,
              ...persisted.data.docker,
              password: "",
            },
          },
          meta,
        );
        expandedCategoryIds.value = [
          ...(persisted.data.expandedCategoryIds ?? []),
        ];
        restoredDraftNotice.value = true;
        restoredFromPersistedDraft.value = true;
        persistedCatalogVersion.value = persisted.catalogVersion ?? "";
      } else {
        form.value = defaultForm;
        expandedCategoryIds.value = [];
        restoredDraftNotice.value = false;
        restoredFromPersistedDraft.value = false;
        persistedCatalogVersion.value = "";
      }

      hydrated.value = true;
      hasSyncedCatalog.value = false;
      return;
    }

    if (!form.value) {
      form.value = defaultForm;
      expandedCategoryIds.value = [];
      return;
    }

    form.value = applyMetaDefaults(form.value, meta);
  };

  const syncWithCatalog = (
    categories: DatasetCategory[],
    catalogVersion: string,
  ) => {
    if (!form.value) {
      return;
    }

    const availableDatasetIds = getAllDatasetIds(categories);
    const previousSelected = [...form.value.selectedDatasetIds];
    const previousExpanded = [...expandedCategoryIds.value];
    const availableCategoryIdSet = new Set(
      getEnabledCategories(categories).map((item) => item.categoryId),
    );

    let nextSelected = sanitizeDatasetSelection(
      categories,
      form.value.selectedDatasetIds,
      true,
    );

    if (
      !hasSyncedCatalog.value &&
      !restoredFromPersistedDraft.value &&
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

    const removedDatasets = previousSelected.length - nextSelected.length;
    const removedExpanded = previousExpanded.length - nextExpanded.length;

    if (removedDatasets > 0 || removedExpanded > 0) {
      catalogSyncNotice.value =
        persistedCatalogVersion.value &&
        persistedCatalogVersion.value !== catalogVersion
          ? "目录版本已更新，系统已保留当前仍有效的已选数据集与展开分组。"
          : "难度变化后已自动移除失效的数据集或展开分组。";
    } else {
      catalogSyncNotice.value = "";
    }

    hasSyncedCatalog.value = true;
  };

  const persistDraft = (catalogVersion: string) => {
    if (!form.value) {
      return;
    }

    clearPersistTimer();
    persistTimer.value = window.setTimeout(() => {
      if (!form.value) {
        return;
      }

      const payload: SubmitFormPersistedData = {
        submitMethod: form.value.submitMethod,
        agentName: form.value.agentName,
        description: form.value.description,
        api: {
          baseUrl: form.value.api.baseUrl,
        },
        docker: {
          imageUri: form.value.docker.imageUri,
          username: form.value.docker.username,
        },
        parameters: form.value.parameters,
        publicToLeaderboard: form.value.publicToLeaderboard,
        selectedDatasetIds: form.value.selectedDatasetIds,
        expandedCategoryIds: expandedCategoryIds.value,
      };

      savePersistedState(STORAGE_KEY, STORAGE_VERSION, payload, catalogVersion);
    }, PERSIST_DELAY_MS);
  };

  const resetDraft = (
    meta: SubmitMetaResponse,
    categories: DatasetCategory[],
  ) => {
    clearPersistTimer();
    currentMeta.value = meta;
    form.value = createDefaultForm(meta);
    form.value.selectedDatasetIds = [...getAllDatasetIds(categories)];
    expandedCategoryIds.value = [];
    restoredDraftNotice.value = false;
    restoredFromPersistedDraft.value = false;
    persistedCatalogVersion.value = "";
    catalogSyncNotice.value = "";
    hasSyncedCatalog.value = categories.length > 0;
    clearPersistedState(STORAGE_KEY);
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

  const setCatalogSyncNotice = (value: string) => {
    catalogSyncNotice.value = value;
  };

  const clearDraftAfterSubmit = () => {
    clearPersistTimer();
    clearPersistedState(STORAGE_KEY);
    restoredDraftNotice.value = false;
    restoredFromPersistedDraft.value = false;
    persistedCatalogVersion.value = "";
    catalogSyncNotice.value = "";
    hasSyncedCatalog.value = false;
    hydrated.value = false;
    form.value = null;
    expandedCategoryIds.value = [];
  };

  return {
    form,
    expandedCategoryIds,
    restoredDraftNotice,
    catalogSyncNotice,
    currentMeta,
    applyMeta,
    syncWithCatalog,
    persistDraft,
    resetDraft,
    setSubmitMethod,
    setExpandedCategoryIds,
    setCatalogSyncNotice,
    clearDraftAfterSubmit,
  };
});
