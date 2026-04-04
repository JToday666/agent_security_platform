<template>
  <div class="content submit-page layout-page-shell layout-page-shell--wide">
    <PageHeroCard
      eyebrow="智能体提交"
      title="提交智能体评测"
      description="提交页会先加载参数元数据，再按当前攻击难度刷新评测目录；草稿仅持久化非敏感字段。"
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
      <SubmitBasicInfoForm v-model="form" :field-errors="fieldErrors" />
      <SubmitParameterControls v-model="form" :meta="submitMeta" />
      <SubmitDatasetPanel
        :categories="enabledCategories"
        :selected-dataset-ids="form.selectedDatasetIds"
        :expanded-category-ids="expandedCategoryIds"
        :status="datasetCatalogStatus"
        :error-message="datasetCatalogErrorMessage"
        :sync-message="catalogSyncNotice"
        :selection-error-message="selectionErrorMessage"
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
        :error-message="submitError"
        :restore-message="restoredDraftNotice ? '已恢复上次未提交内容。' : ''"
        :sync-message="catalogSyncNotice"
        @reset="resetDraft"
      />
    </form>

    <ConfirmDialog
      v-model="confirmDialogVisible"
      :title="confirmDialogTitle"
      :message="confirmDialogMessage"
      confirm-text="确认提交"
      cancel-text="返回修改"
      :loading="submitting"
      @confirm="confirmSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import { getSubmitMeta, precheckAgent, submitAgent } from "@/api/AgentService";
import { useSubmitDatasetCatalog } from "@/composables/useSubmitDatasetCatalog";
import PageHeroCard from "@/components/common/PageHeroCard.vue";
import ConfirmDialog from "@/components/dialog/ConfirmDialog.vue";
import SubmitActionBar from "@/components/submit/SubmitActionBar.vue";
import SubmitBasicInfoForm from "@/components/submit/SubmitBasicInfoForm.vue";
import SubmitDatasetPanel from "@/components/submit/SubmitDatasetPanel.vue";
import SubmitMethodSelector from "@/components/submit/SubmitMethodSelector.vue";
import SubmitParameterControls from "@/components/submit/SubmitParameterControls.vue";
import SubmitVisibilityCard from "@/components/submit/SubmitVisibilityCard.vue";
import { RouteLocation } from "@/router/RouteNames";
import { useSubmitDraftStore } from "@/store/SubmitDraftStore";
import type {
  PendingSubmitRequest,
  SubmitAgentPayload,
  SubmitFieldErrors,
  SubmitMetaResponse,
} from "@/types/AgentTypes";
import {
  toggleCategoryDatasets as toggleCategoryDatasetsValue,
  toggleDatasetId,
} from "@/utils/common";
import {
  MAX_SUBMIT_DATASET_COUNT,
  normalizeDifficulty,
  normalizeTimeoutMinutes,
  validateSubmitPayload,
} from "@/utils/submit";

interface SubmitPayloadSnapshot {
  agentName: string;
  description: string;
  submitMethod: SubmitAgentPayload["submitMethod"];
  apiBaseUrl: string;
  dockerImageUri: string;
  parameters: SubmitAgentPayload["parameters"];
  publicToLeaderboard: boolean;
  datasetIds: string[];
}

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
  pendingRequest,
} = storeToRefs(submitDraftStore);

const submitMeta = ref<SubmitMetaResponse | null>(null);
const pageLoading = ref(true);
const pageError = ref("");
const submitting = ref(false);
const submitError = ref("");
const fieldErrors = ref<SubmitFieldErrors>({});
const datasetSelectionNotice = ref("");
const confirmDialogVisible = ref(false);
const confirmDialogTitle = ref("确认提交");
const confirmDialogMessage = ref("");
const confirmedPayload = ref<SubmitAgentPayload | null>(null);

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
const selectionErrorMessage = computed(
  () => fieldErrors.value.selectedDatasetIds || datasetSelectionNotice.value,
);

const buildRequestId = (): string => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `submit_${crypto.randomUUID()}`;
  }

  return `submit_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
};

const clearFormErrors = () => {
  submitError.value = "";
  fieldErrors.value = {};
};

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

const setSelectedDatasetIds = (value: string[]) => {
  if (!form.value) {
    return;
  }

  const uniqueIds = Array.from(new Set(value));
  const nextIds = uniqueIds.slice(0, MAX_SUBMIT_DATASET_COUNT);
  form.value.selectedDatasetIds = nextIds;

  datasetSelectionNotice.value =
    uniqueIds.length > MAX_SUBMIT_DATASET_COUNT
      ? `最多只能选择 ${MAX_SUBMIT_DATASET_COUNT} 个评测项，超出的部分已自动忽略。`
      : "";

  if (nextIds.length > 0 && fieldErrors.value.selectedDatasetIds) {
    fieldErrors.value = {
      ...fieldErrors.value,
      selectedDatasetIds: undefined,
    };
  }
};

const buildPayloadSnapshot = (): SubmitPayloadSnapshot | null => {
  if (!form.value || !submitMeta.value) {
    return null;
  }

  const datasetIds = Array.from(new Set(form.value.selectedDatasetIds)).sort();

  return {
    agentName: form.value.agentName.trim(),
    description: form.value.description.trim(),
    submitMethod: form.value.submitMethod,
    apiBaseUrl:
      form.value.submitMethod === "api" ? form.value.api.baseUrl.trim() : "",
    dockerImageUri:
      form.value.submitMethod === "docker"
        ? form.value.docker.imageUri.trim()
        : "",
    parameters: {
      difficulty: normalizeDifficulty(
        form.value.parameters.difficulty,
        submitMeta.value.difficulty,
      ),
      timeoutMinutes: normalizeTimeoutMinutes(
        form.value.parameters.timeoutMinutes,
        submitMeta.value.timeoutMinutes,
      ),
      retryEnabled: Boolean(form.value.parameters.retryEnabled),
    },
    publicToLeaderboard: Boolean(form.value.publicToLeaderboard),
    datasetIds,
  };
};

const buildPayloadDigest = (): string => {
  const snapshot = buildPayloadSnapshot();
  return snapshot ? JSON.stringify(snapshot) : "";
};

const resolvePendingRequest = (payloadDigest: string): PendingSubmitRequest => {
  if (
    pendingRequest.value &&
    pendingRequest.value.payloadDigest === payloadDigest
  ) {
    return pendingRequest.value;
  }

  const nextPendingRequest: PendingSubmitRequest = {
    requestId: buildRequestId(),
    payloadDigest,
    createdAt: new Date().toISOString(),
  };
  submitDraftStore.setPendingRequest(nextPendingRequest);
  return nextPendingRequest;
};

const buildPayload = (mode: "preview" | "submit"): SubmitAgentPayload => {
  const snapshot = buildPayloadSnapshot();
  if (!snapshot) {
    throw new Error("提交表单尚未初始化完成。");
  }

  const payloadDigest = JSON.stringify(snapshot);
  const requestId =
    mode === "submit"
      ? resolvePendingRequest(payloadDigest).requestId
      : pendingRequest.value?.payloadDigest === payloadDigest
        ? pendingRequest.value.requestId
        : "preview_request_id";

  return {
    agentName: snapshot.agentName,
    description: snapshot.description,
    submitMethod: snapshot.submitMethod,
    api:
      snapshot.submitMethod === "api"
        ? {
            baseUrl: form.value?.api.baseUrl.trim() ?? "",
            token: form.value?.api.token.trim() ?? "",
          }
        : null,
    docker:
      snapshot.submitMethod === "docker"
        ? {
            imageUri: form.value?.docker.imageUri.trim() ?? "",
            username: form.value?.docker.username.trim() ?? "",
            password: form.value?.docker.password.trim() ?? "",
          }
        : null,
    parameters: snapshot.parameters,
    publicToLeaderboard: snapshot.publicToLeaderboard,
    selectedDatasetIds: snapshot.datasetIds,
    requestId,
  };
};

const buildConfirmMessage = (warnings: string[], payload: SubmitAgentPayload): string => {
  const header = `智能体名称：${payload.agentName}\n提交方式：${payload.submitMethod.toUpperCase()}\n评测项数量：${payload.selectedDatasetIds.length}`;

  if (!warnings.length) {
    return `${header}\n\n系统已完成提交检查，确认后将正式创建评测任务。`;
  }

  return `${header}\n\n系统发现以下提示：\n- ${warnings.join("\n- ")}\n\n确认后将正式创建评测任务。`;
};

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
  clearFormErrors();
  datasetSelectionNotice.value = "";
  confirmDialogVisible.value = false;
  confirmedPayload.value = null;

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
    setSelectedDatasetIds(form.value.selectedDatasetIds);

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
  setSelectedDatasetIds(validDatasetIds.value);
};

const clearAllDatasets = () => {
  setSelectedDatasetIds([]);
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

  setSelectedDatasetIds(
    toggleCategoryDatasetsValue(
      category,
      form.value.selectedDatasetIds,
      MAX_SUBMIT_DATASET_COUNT,
    ),
  );
};

const toggleDataset = (datasetId: string) => {
  if (!form.value) {
    return;
  }

  setSelectedDatasetIds(
    toggleDatasetId(
      datasetId,
      form.value.selectedDatasetIds,
      MAX_SUBMIT_DATASET_COUNT,
    ),
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
  clearFormErrors();
  datasetSelectionNotice.value = "";
  confirmDialogVisible.value = false;
  confirmedPayload.value = null;

  if (currentDifficulty.value !== null) {
    void loadCatalogForDifficulty(currentDifficulty.value, true);
  }
};

const handleSubmit = async () => {
  if (!submitMeta.value || !form.value) {
    return;
  }

  clearFormErrors();

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
    const payload = buildPayload("submit");
    const validation = validateSubmitPayload(
      payload,
      submitMeta.value,
      validDatasetIds.value,
    );

    if (!validation.valid) {
      fieldErrors.value = validation.fieldErrors;
      submitError.value = validation.errors[0] || "提交参数校验失败。";
      return;
    }

    const precheckResult = await precheckAgent(payload);
    confirmedPayload.value = payload;
    confirmDialogTitle.value = precheckResult.warnings.length
      ? "提交前确认"
      : "确认提交";
    confirmDialogMessage.value = buildConfirmMessage(
      precheckResult.warnings,
      payload,
    );
    confirmDialogVisible.value = true;
  } catch (error) {
    submitError.value =
      error instanceof Error ? error.message : "提交失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
};

const confirmSubmit = async () => {
  if (!confirmedPayload.value) {
    return;
  }

  submitting.value = true;
  submitError.value = "";

  try {
    const submitResult = await submitAgent(confirmedPayload.value);
    confirmDialogVisible.value = false;
    submitDraftStore.clearDraftAfterSubmit();
    await router.push(RouteLocation.evaluationDetail(submitResult.evaluationId));
  } catch (error) {
    submitError.value =
      error instanceof Error ? error.message : "提交失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
};

const canSubmit = computed(() => {
  if (!form.value || !submitMeta.value || !datasetCatalogReady.value) {
    return false;
  }

  const payload = buildPayload("preview");
  return validateSubmitPayload(
    payload,
    submitMeta.value,
    validDatasetIds.value,
  ).valid;
});

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

    clearFormErrors();
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
  [form, expandedCategoryIds, pendingRequest, () => datasetCatalog.catalogVersion.value],
  ([currentForm]) => {
    if (!currentForm) {
      return;
    }

    const payloadDigest = buildPayloadDigest();
    if (
      pendingRequest.value &&
      payloadDigest &&
      pendingRequest.value.payloadDigest !== payloadDigest
    ) {
      submitDraftStore.setPendingRequest(null);
    }

    submitDraftStore.persistDraft(datasetCatalog.catalogVersion.value);
  },
  {
    deep: true,
  },
);

watch(
  () => form.value?.selectedDatasetIds,
  (value) => {
    if (!value) {
      return;
    }

    if (value.length > 0 && fieldErrors.value.selectedDatasetIds) {
      fieldErrors.value = {
        ...fieldErrors.value,
        selectedDatasetIds: undefined,
      };
    }
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
