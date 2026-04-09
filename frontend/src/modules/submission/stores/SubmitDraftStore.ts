import { ref } from "vue";
import { defineStore } from "pinia";
import type {
  PendingSubmitRequest,
  SubmitFormPersistedData,
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
  clearPersistedState,
  loadPersistedState,
  savePersistedState,
} from "@/shared/lib/StorageUtils";
import {
  MAX_SUBMIT_DATASET_COUNT,
  normalizeDifficulty,
  normalizeTimeoutMinutes,
} from "@/modules/submission/lib";
import { STORAGE_KEYS } from "@/shared/constants/StorageKeys";

const STORAGE_VERSION = 3;
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
  const pendingRequest = ref<PendingSubmitRequest | null>(null);
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
        STORAGE_KEYS.draft.submit,
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
        pendingRequest.value = persisted.data.pendingRequest ?? null;
        restoredDraftNotice.value = true;
        restoredFromPersistedDraft.value = true;
        persistedCatalogVersion.value = persisted.catalogVersion ?? "";
      } else {
        form.value = defaultForm;
        expandedCategoryIds.value = [];
        pendingRequest.value = null;
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
      pendingRequest.value = null;
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
      MAX_SUBMIT_DATASET_COUNT,
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
      const catalogWasUpdated =
        Boolean(persistedCatalogVersion.value) &&
        persistedCatalogVersion.value !== catalogVersion;

      catalogSyncNotice.value = catalogWasUpdated
        ? "目录版本已更新，系统已保留当前仍有效的已选评测项与展开分组。"
        : "目录更新后已自动移除失效的评测项或无效展开分组。";
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
        pendingRequest: pendingRequest.value,
      };

      savePersistedState(
        STORAGE_KEYS.draft.submit,
        STORAGE_VERSION,
        payload,
        catalogVersion,
      );
    }, PERSIST_DELAY_MS);
  };

  const resetDraft = (
    meta: SubmitMetaResponse,
    categories: DatasetCategory[],
  ) => {
    clearPersistTimer();
    currentMeta.value = meta;
    form.value = createDefaultForm(meta);
    form.value.selectedDatasetIds = [
      ...getAllDatasetIds(categories, MAX_SUBMIT_DATASET_COUNT),
    ];
    expandedCategoryIds.value = [];
    pendingRequest.value = null;
    restoredDraftNotice.value = false;
    restoredFromPersistedDraft.value = false;
    persistedCatalogVersion.value = "";
    catalogSyncNotice.value = "";
    hasSyncedCatalog.value = categories.length > 0;
    clearPersistedState(STORAGE_KEYS.draft.submit);
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

  const setCatalogSyncNotice = (value: string) => {
    catalogSyncNotice.value = value;
  };

  const clearDraftAfterSubmit = () => {
    clearPersistTimer();
    clearPersistedState(STORAGE_KEYS.draft.submit);
    restoredDraftNotice.value = false;
    restoredFromPersistedDraft.value = false;
    persistedCatalogVersion.value = "";
    catalogSyncNotice.value = "";
    hasSyncedCatalog.value = false;
    hydrated.value = false;
    form.value = null;
    expandedCategoryIds.value = [];
    pendingRequest.value = null;
  };

  return {
    form,
    expandedCategoryIds,
    restoredDraftNotice,
    catalogSyncNotice,
    currentMeta,
    pendingRequest,
    applyMeta,
    syncWithCatalog,
    persistDraft,
    resetDraft,
    setSubmitMethod,
    setExpandedCategoryIds,
    setPendingRequest,
    setCatalogSyncNotice,
    clearDraftAfterSubmit,
  };
});
