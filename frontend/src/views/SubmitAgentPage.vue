<template>
  <div class="content submit-page layout-page-shell layout-page-shell--wide">
    <PageHeroCard
      eyebrow="智能体提交"
      title="提交智能体评测"
      description="提交页会先加载参数元数据，再按当前攻击难度刷新风险域与评测项目录；草稿仅持久化非敏感字段。"
      :chips="heroChips"
    />

    <div v-if="pageLoading" class="state-card layout-state-card ui-surface-white">
      <h2>正在初始化提交页</h2>
      <p>系统正在加载提交元数据、恢复草稿，并根据当前难度筛选评测目录。</p>
    </div>

    <div v-else-if="pageError" class="state-card layout-state-card ui-surface-white">
      <h2>页面初始化失败</h2>
      <p>{{ pageError }}</p>
      <button
        class="retry-btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient"
        type="button"
        @click="initializePage"
      >
        重新加载
      </button>
    </div>

    <form
      v-else-if="form && submitMeta"
      class="submit-form"
      @submit.prevent="handleSubmit"
    >
      <SubmitMethodSelector
        :model-value="form.submitMethod"
        :methods="submitMeta.supportedMethods"
        @update:model-value="submitDraftStore.setSubmitMethod"
      />
      <SubmitBasicInfoForm v-model="form" />
      <SubmitParameterControls v-model="form" :meta="submitMeta" />
      <SubmitDatasetPanel
        :categories="enabledCategories"
        :selected-dataset-ids="form.selectedDatasetIds"
        :expanded-category-ids="expandedCategoryIds"
        :status="datasetCatalogStatus"
        :error-message="datasetCatalogErrorMessage"
        :sync-message="catalogSyncNotice"
        @select-all="selectAllDatasets"
        @clear-all="clearAllDatasets"
        @toggle-category="toggleCategoryDatasets"
        @toggle-dataset="toggleDataset"
        @toggle-expanded="toggleExpandedCategory"
        @retry="retryDatasetCatalog"
      />
      <SubmitVisibilityCard v-model="form" />
      <SubmitActionBar
        :submitting="submitting"
        :can-submit="canSubmit"
        :warnings="precheckWarnings"
        :error-message="submitError"
        :restore-message="restoredDraftNotice ? '已恢复上次未提交内容。' : ''"
        @reset="resetDraft"
      />
    </form>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import { getSubmitMeta, precheckAgent, submitAgent } from "@/api/AgentService";
import { useSubmitDatasetCatalog } from "@/composables/useSubmitDatasetCatalog";
import PageHeroCard from "@/components/common/PageHeroCard.vue";
import SubmitActionBar from "@/components/submit/SubmitActionBar.vue";
import SubmitBasicInfoForm from "@/components/submit/SubmitBasicInfoForm.vue";
import SubmitDatasetPanel from "@/components/submit/SubmitDatasetPanel.vue";
import SubmitMethodSelector from "@/components/submit/SubmitMethodSelector.vue";
import SubmitParameterControls from "@/components/submit/SubmitParameterControls.vue";
import SubmitVisibilityCard from "@/components/submit/SubmitVisibilityCard.vue";
import { RouteLocation } from "@/router/RouteNames";
import { useSubmitDraftStore } from "@/store/SubmitDraftStore";
import type {
  SubmitAgentPayload,
  SubmitMetaResponse,
} from "@/types/AgentTypes";
import {
  toggleCategoryDatasets as toggleCategoryDatasetsValue,
  toggleDatasetId,
} from "@/utils/common";
import {
  normalizeDifficulty,
  normalizeTimeoutMinutes,
  validateSubmitPayload,
} from "@/utils/submit";

const router = useRouter();
const submitDraftStore = useSubmitDraftStore();
const datasetCatalog = useSubmitDatasetCatalog();
const datasetCatalogStatus = datasetCatalog.status;
const datasetCatalogErrorMessage = datasetCatalog.errorMessage;

const {
  form,
  expandedCategoryIds,
  restoredDraftNotice,
  catalogSyncNotice,
} = storeToRefs(submitDraftStore);

const submitMeta = ref<SubmitMetaResponse | null>(null);
const pageLoading = ref(true);
const pageError = ref("");
const submitting = ref(false);
const submitError = ref("");
const precheckWarnings = ref<string[]>([]);
const activeRequestId = ref<string | null>(null);

let catalogDebounceTimer: number | null = null;
let activeCatalogController: AbortController | null = null;
let latestCatalogRequestSeq = 0;

const enabledCategories = computed(() => datasetCatalog.enabledCategories.value);
const validDatasetIds = computed(() => datasetCatalog.datasetIds.value);
const selectedCategoryCount = computed(
  () =>
    enabledCategories.value.filter((category) =>
      category.subcategories.some((item) =>
        form.value?.selectedDatasetIds.includes(item.datasetId),
      ),
    ).length,
);
const currentDifficulty = computed(() => {
  if (!form.value || !submitMeta.value) {
    return null;
  }

  return normalizeDifficulty(
    form.value.parameters.difficulty,
    submitMeta.value.difficulty,
  );
});
const datasetCatalogReady = computed(
  () =>
    datasetCatalogStatus.value === "ready" &&
    datasetCatalog.hasResolvedCurrentDifficulty.value,
);
const heroChips = computed(() => [
  {
    label: "当前提交方式",
    value: form.value?.submitMethod === "docker" ? "Docker" : "API",
  },
  {
    label: "已选风险域",
    value: `${selectedCategoryCount.value} 个`,
  },
  {
    label: "已选评测项",
    value: `${form.value?.selectedDatasetIds.length ?? 0} 个`,
  },
]);

const canSubmit = computed(() => {
  if (!form.value || !submitMeta.value) {
    return false;
  }

  if (!datasetCatalogReady.value) {
    return false;
  }

  const payload = buildPayload("preview");
  return validateSubmitPayload(
    payload,
    submitMeta.value,
    validDatasetIds.value,
  ).valid;
});

const buildRequestId = (): string => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `submit_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
};

const buildPayload = (requestId: string): SubmitAgentPayload => ({
  agentName: form.value?.agentName?.trim() || "",
  description: form.value?.description?.trim() || "",
  submitMethod: form.value?.submitMethod || "api",
  api:
    form.value?.submitMethod === "api"
      ? {
          baseUrl: form.value.api.baseUrl.trim(),
          token: form.value.api.token.trim(),
        }
      : null,
  docker:
    form.value?.submitMethod === "docker"
      ? {
          imageUri: form.value.docker.imageUri.trim(),
          username: form.value.docker.username.trim(),
          password: form.value.docker.password.trim(),
        }
      : null,
  parameters: {
    difficulty: normalizeDifficulty(
      form.value?.parameters.difficulty ?? 0,
      submitMeta.value?.difficulty ?? {
        min: 0,
        max: 1,
        step: 0.1,
        default: 0.5,
      },
    ),
    timeoutMinutes: normalizeTimeoutMinutes(
      form.value?.parameters.timeoutMinutes ?? 15,
      submitMeta.value?.timeoutMinutes ?? {
        min: 15,
        max: 30,
        step: 1,
        default: 15,
      },
    ),
    retryEnabled: Boolean(form.value?.parameters.retryEnabled),
  },
  publicToLeaderboard: Boolean(form.value?.publicToLeaderboard),
  selectedDatasetIds: form.value?.selectedDatasetIds ?? [],
  requestId,
});

const clearScheduledCatalogRefresh = () => {
  if (catalogDebounceTimer !== null) {
    window.clearTimeout(catalogDebounceTimer);
    catalogDebounceTimer = null;
  }
};

const abortActiveCatalogRequest = () => {
  if (activeCatalogController) {
    activeCatalogController.abort();
    activeCatalogController = null;
  }
};

const isAbortLikeError = (error: unknown): boolean =>
  error instanceof DOMException
    ? error.name === "AbortError"
    : error instanceof Error
      ? error.name === "AbortError" || error.name === "CanceledError"
      : false;

const syncCatalogSelection = () => {
  if (!datasetCatalog.catalog.value) {
    return;
  }

  submitDraftStore.syncWithCatalog(
    datasetCatalog.catalog.value.categories,
    datasetCatalog.catalogVersion.value,
  );
};

const loadCatalogForDifficulty = async (
  difficulty: number,
  force = false,
) => {
  const requestSeq = ++latestCatalogRequestSeq;
  abortActiveCatalogRequest();
  const controller = new AbortController();
  activeCatalogController = controller;

  try {
    await datasetCatalog.fetchCatalog(difficulty, {
      signal: controller.signal,
      force,
    });

    if (requestSeq !== latestCatalogRequestSeq) {
      return;
    }

    syncCatalogSelection();
  } catch (error) {
    if (requestSeq !== latestCatalogRequestSeq || isAbortLikeError(error)) {
      return;
    }
  }
};

const scheduleCatalogRefresh = (difficulty: number, force = false) => {
  clearScheduledCatalogRefresh();
  catalogDebounceTimer = window.setTimeout(() => {
    void loadCatalogForDifficulty(difficulty, force);
  }, force ? 0 : 200);
};

const initializePage = async () => {
  pageLoading.value = true;
  pageError.value = "";
  submitError.value = "";
  precheckWarnings.value = [];

  try {
    const meta = await getSubmitMeta();
    submitMeta.value = meta;
    submitDraftStore.applyMeta(meta);

    if (!form.value) {
      throw new Error("提交表单初始化失败。");
    }

    form.value.parameters.difficulty = normalizeDifficulty(
      form.value.parameters.difficulty,
      meta.difficulty,
    );
    form.value.parameters.timeoutMinutes = normalizeTimeoutMinutes(
      form.value.parameters.timeoutMinutes,
      meta.timeoutMinutes,
    );

    if (currentDifficulty.value !== null) {
      await loadCatalogForDifficulty(currentDifficulty.value, true);
    }
  } catch (error) {
    pageError.value =
      error instanceof Error ? error.message : "提交页初始化失败。";
  } finally {
    pageLoading.value = false;
  }
};

const selectAllDatasets = () => {
  if (!form.value) {
    return;
  }

  form.value.selectedDatasetIds = [...validDatasetIds.value];
};

const clearAllDatasets = () => {
  if (!form.value) {
    return;
  }

  form.value.selectedDatasetIds = [];
};

const toggleCategoryDatasets = (categoryId: string) => {
  if (!form.value) {
    return;
  }

  const category = enabledCategories.value.find(
    (item) => item.categoryId === categoryId,
  );
  if (!category) {
    return;
  }

  form.value.selectedDatasetIds = toggleCategoryDatasetsValue(
    category,
    form.value.selectedDatasetIds,
  );
};

const toggleDataset = (datasetId: string) => {
  if (!form.value) {
    return;
  }

  form.value.selectedDatasetIds = toggleDatasetId(
    datasetId,
    form.value.selectedDatasetIds,
  );
};

const toggleExpandedCategory = (categoryId: string) => {
  const nextExpanded = expandedCategoryIds.value.includes(categoryId)
    ? expandedCategoryIds.value.filter((item) => item !== categoryId)
    : [...expandedCategoryIds.value, categoryId];

  submitDraftStore.setExpandedCategoryIds(nextExpanded);
};

const retryDatasetCatalog = () => {
  if (currentDifficulty.value === null) {
    return;
  }

  void loadCatalogForDifficulty(currentDifficulty.value, true);
};

const resetDraft = () => {
  if (!submitMeta.value) {
    return;
  }

  submitDraftStore.resetDraft(
    submitMeta.value,
    datasetCatalog.catalog.value?.categories ?? [],
  );
  submitError.value = "";
  precheckWarnings.value = [];
  activeRequestId.value = null;

  if (currentDifficulty.value !== null) {
    void loadCatalogForDifficulty(currentDifficulty.value, true);
  }
};

const handleSubmit = async () => {
  if (!submitMeta.value || !form.value) {
    return;
  }

  submitError.value = "";
  precheckWarnings.value = [];

  if (datasetCatalogStatus.value === "empty") {
    submitError.value = "当前难度下没有可用评测项，无法提交。";
    return;
  }

  if (!datasetCatalogReady.value) {
    submitError.value = "请等待评测目录刷新完成后再提交。";
    return;
  }

  submitting.value = true;

  try {
    const requestId = activeRequestId.value || buildRequestId();
    activeRequestId.value = requestId;

    const payload = buildPayload(requestId);
    const validation = validateSubmitPayload(
      payload,
      submitMeta.value,
      validDatasetIds.value,
    );

    if (!validation.valid) {
      submitError.value = validation.errors[0] || "提交参数校验失败。";
      return;
    }

    const precheckResult = await precheckAgent(payload);
    precheckWarnings.value = precheckResult.warnings ?? [];

    const submitResult = await submitAgent(payload);
    submitDraftStore.clearDraftAfterSubmit();
    await router.push(RouteLocation.evaluationDetail(submitResult.evaluationId));
  } catch (error) {
    submitError.value =
      error instanceof Error ? error.message : "提交失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
};

watch(
  () => form.value?.parameters.difficulty,
  (value, previousValue) => {
    if (!form.value || !submitMeta.value || typeof value !== "number") {
      return;
    }

    const normalized = normalizeDifficulty(value, submitMeta.value.difficulty);
    if (normalized !== value) {
      form.value.parameters.difficulty = normalized;
      return;
    }

    if (typeof previousValue !== "number") {
      return;
    }

    submitError.value = "";
    precheckWarnings.value = [];
    scheduleCatalogRefresh(normalized);
  },
);

watch(
  () => form.value?.parameters.timeoutMinutes,
  (value) => {
    if (!form.value || !submitMeta.value || typeof value !== "number") {
      return;
    }

    const normalized = normalizeTimeoutMinutes(
      value,
      submitMeta.value.timeoutMinutes,
    );
    if (normalized !== value) {
      form.value.parameters.timeoutMinutes = normalized;
    }
  },
);

watch(
  [form, expandedCategoryIds, () => datasetCatalog.catalogVersion.value],
  ([currentForm]) => {
    if (!currentForm) {
      return;
    }

    submitDraftStore.persistDraft(datasetCatalog.catalogVersion.value);
    activeRequestId.value = null;
  },
  {
    deep: true,
  },
);

onMounted(async () => {
  await initializePage();
});

onBeforeUnmount(() => {
  clearScheduledCatalogRefresh();
  abortActiveCatalogRequest();
});
</script>

<style scoped>
.submit-page {
  padding-bottom: 2.5rem;
}

.submit-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 980px;
  margin: 0 auto;
}
</style>
